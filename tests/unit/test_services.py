"""Unit tests for FactReceipt, Discovery (Nearby Switch), and Grievance services."""

from datetime import UTC, date, datetime

import pytest
from pydantic import HttpUrl

from india_ate.models import (
    AuthoritativeEvent,
    BrandListing,
    EvidenceProvenance,
    FoodPremises,
    IndiaFSSAI14,
)
from india_ate.services import (
    build_fact_receipt,
    find_verified_nearby_switches,
    generate_grievance_packet,
    get_ghost_brand_cluster,
)
from india_ate.store import SQLiteStore


def _prov(ts: datetime) -> EvidenceProvenance:
    return EvidenceProvenance(
        source_name="Official Registry",
        source_url=HttpUrl("https://hygiene.fssai.gov.in/snapshot"),
        retrieved_at=ts,
        content_sha256="abc123",
        verification_tier="official_registry",
    )


def _seed_store(store: SQLiteStore) -> None:
    ts = datetime(2026, 4, 1, 10, 0, tzinfo=UTC)
    prov = _prov(ts)
    p_basic = FoodPremises(
        entity_id="actor:in:fssai:23624001000123",
        legal_name="Cloud Kitchen Basic",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value="23624001000123")],
        provenance=[prov],
        premises_type="cloud_kitchen",
        postal_code="500081",
    )
    p_verified = FoodPremises(
        entity_id="actor:in:fssai:13624001000999",
        legal_name="Verified Kitchen Ltd",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value="13624001000999")],
        provenance=[prov],
        premises_type="restaurant",
        postal_code="500081",
    )
    p_suspended = FoodPremises(
        entity_id="actor:in:fssai:13624001000888",
        legal_name="Suspended Kitchen Ltd",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value="13624001000888")],
        provenance=[prov],
        premises_type="cloud_kitchen",
        postal_code="500081",
    )
    for p in (p_basic, p_verified, p_suspended):
        store.save_premises(p)

    for idx, name in enumerate(["Ghost Brand A", "Ghost Brand B"], start=1):
        store.save_brand_listing(
            BrandListing(
                listing_id=f"listing:ondc:{idx}",
                display_name=name,
                platform="ondc",
                premises_entity_id=p_basic.entity_id,
                postal_code="500081",
                first_seen_at=ts,
                last_seen_at=ts,
                provenance=prov,
            )
        )

    store.save_event(
        AuthoritativeEvent(
            event_id="evt:hygiene:13624001000999:2026-03-01",
            event_type="hygiene_audit",
            target_entity_id=p_verified.entity_id,
            jurisdiction_iso="IN",
            event_date=date(2026, 3, 1),
            status="5/5",
            verbatim_summary="FSSAI Hygiene Rating 5/5 audited on 2026-03-01",
            provenance=prov,
        )
    )
    store.save_event(
        AuthoritativeEvent(
            event_id="evt:license:13624001000999:2026-04-01",
            event_type="license_status_snapshot",
            target_entity_id=p_verified.entity_id,
            jurisdiction_iso="IN",
            event_date=date(2026, 4, 1),
            status="Active",
            verbatim_summary="Official license status snapshot.",
            provenance=prov,
        )
    )
    store.save_event(
        AuthoritativeEvent(
            event_id="evt:enf:tg_safe:13624001000888:2026-03-10",
            event_type="enforcement_raid_or_suspension",
            target_entity_id=p_suspended.entity_id,
            jurisdiction_iso="IN",
            event_date=date(2026, 3, 10),
            status="Suspended",
            verbatim_summary="License suspended by TG SAFE.",
            provenance=prov,
        )
    )


def test_fact_receipt_and_ghost_cluster() -> None:
    with SQLiteStore(":memory:") as store:
        store.initialize()
        _seed_store(store)

        receipt = build_fact_receipt(store, "23624001000123")
        assert receipt.premises is not None
        assert receipt.ghost_brand_count == 2
        assert len(receipt.brand_listings) == 2
        assert receipt.decoded["pre_inspection_exempt_post_apr2026"] is True
        assert receipt.last_verified_at is not None

        uncached = build_fact_receipt(store, "10013022000417")
        assert uncached.premises is None
        assert uncached.ghost_brand_count == 0
        assert uncached.last_verified_at is None

        cluster = get_ghost_brand_cluster(store, "23624001000123")
        assert cluster is not None
        assert len(cluster.listings) == 2

        verified_receipt = build_fact_receipt(store, "13624001000999")
        assert [event.event_type for event in verified_receipt.events] == [
            "license_status_snapshot",
            "hygiene_audit",
        ]


def test_verified_nearby_switches_excludes_suspended_and_basic() -> None:
    with SQLiteStore(":memory:") as store:
        store.initialize()
        _seed_store(store)

        switches = find_verified_nearby_switches(store, "500081")
        assert len(switches) == 1
        assert switches[0].premises.entity_id == "actor:in:fssai:13624001000999"
        assert len(switches[0].hygiene_events) == 1
        assert len(switches[0].verification_reasons) == 2


def test_generate_grievance_packet_15_day_escalation_and_validation() -> None:
    with SQLiteStore(":memory:") as store:
        store.initialize()
        _seed_store(store)

        packet = generate_grievance_packet(
            store=store,
            fssai_id="13624001000888",
            issue_category="shelf_life_30pct_violation",
            order_reference="ORD-9911",
            description="Delivered with 10% remaining shelf life.",
            incident_date=date(2026, 4, 1),
            persist=True,
        )
        assert packet.escalation_deadline == date(2026, 4, 16)
        assert packet.premises_legal_name == "Suspended Kitchen Ltd"
        assert packet.known_events_count == 1
        assert packet.ticket_event is not None
        assert packet.ticket_event.event_type == "grievance_ticket"
        events = store.get_events_for_target("actor:in:fssai:13624001000888")
        assert len(events) == 2

        with pytest.raises(ValueError, match="description"):
            generate_grievance_packet(
                store=store,
                fssai_id="13624001000888",
                issue_category="other",
                order_reference=None,
                description="   ",
                incident_date=date(2026, 4, 1),
            )


def test_user_submitted_grievance_does_not_enter_official_receipt() -> None:
    with SQLiteStore(":memory:") as store:
        store.initialize()
        _seed_store(store)

        first = generate_grievance_packet(
            store=store,
            fssai_id="13624001000888",
            issue_category="spoiled_food",
            order_reference=None,
            description="First user submission.",
            incident_date=date(2026, 4, 2),
            persist=True,
        )
        assert first.ticket_event is not None

        second = generate_grievance_packet(
            store=store,
            fssai_id="13624001000888",
            issue_category="misbranded",
            order_reference=None,
            description="Second user submission.",
            incident_date=date(2026, 4, 3),
        )
        assert second.known_events_count == 1

        receipt = build_fact_receipt(store, "13624001000888")
        assert [event.event_type for event in receipt.events] == [
            "enforcement_raid_or_suspension"
        ]
        assert receipt.last_verified_at == datetime(2026, 4, 1, 10, 0, tzinfo=UTC)
        assert len(store.get_events_for_target("actor:in:fssai:13624001000888")) == 2
