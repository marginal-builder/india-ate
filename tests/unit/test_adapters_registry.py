"""Unit tests for FoSCoSRecall, StateEnforcement, and ONDCCatalog adapters."""

import json
from datetime import date

from india_ate.adapters.foscos_recall import FoSCoSRecallAdapter
from india_ate.adapters.ondc_catalog import ONDCCatalogAdapter
from india_ate.adapters.state_enforcement import StateEnforcementAdapter
from india_ate.models import AuthoritativeEvent, BrandListing, FoodPremises


class _StubFetcher:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def get(self, url: str, params: dict[str, str] | None = None) -> bytes:
        return self._payload


def test_foscos_recall_adapter_valid_and_quarantine() -> None:
    payload = json.dumps(
        [
            {
                "fssai_id": "10013022000417",
                "legal_name": "Acme Dairy Pvt Ltd",
                "recall_date": "2026-04-01",
                "status": "Initiated",
                "batch_or_lot_no": "LOT-2026-09",
                "verbatim_summary": "Recall initiated for elevated aflatoxin M1.",
                "city": "Mumbai",
                "state": "Maharashtra",
            },
            {
                "fssai_id": "invalid-id",
                "legal_name": "Bad Dairy",
                "recall_date": "2026-04-01",
                "status": "Initiated",
                "verbatim_summary": "Bad ID should quarantine.",
            },
            {
                "fssai_id": "10013022000417",
                "legal_name": "Acme Dairy Pvt Ltd",
                "recall_date": "bad-date",
                "status": "Initiated",
                "verbatim_summary": "Bad date should quarantine.",
            },
        ]
    ).encode("utf-8")

    adapter = FoSCoSRecallAdapter(fetcher=_StubFetcher(payload))
    raw = adapter.fetch()
    rows = adapter.parse(raw)
    batch = adapter.validate_and_emit_batch(rows)

    assert len(batch.quarantined) == 2
    premises = [e for e in batch.entities if isinstance(e, FoodPremises)]
    events = [e for e in batch.entities if isinstance(e, AuthoritativeEvent)]
    assert len(premises) == 1
    assert len(events) == 1
    assert events[0].event_type == "food_recall"
    assert events[0].batch_or_lot_no == "LOT-2026-09"
    assert events[0].event_date == date(2026, 4, 1)
    assert len(adapter.validate_and_emit(rows)) == 2


def test_state_enforcement_adapter_tg_safe_and_maharashtra_fda() -> None:
    payload = json.dumps(
        {
            "records": [
                {
                    "fssai_id": "23624001000123",
                    "legal_name": "Deccan Cloud Kitchens",
                    "premises_type": "cloud_kitchen",
                    "event_date": "2026-04-05",
                    "status": "Suspended",
                    "verbatim_summary": "License suspended during TG SAFE inspection.",
                    "postal_code": "500081",
                    "city": "Hyderabad",
                    "state": "Telangana",
                },
                {
                    "fssai_id": "23624001000123",
                    "legal_name": "",
                    "event_date": "2026-04-05",
                    "status": "Suspended",
                    "verbatim_summary": "Missing legal name should quarantine.",
                },
            ]
        }
    ).encode("utf-8")

    adapter = StateEnforcementAdapter(
        source_name="Telangana TG SAFE",
        portal_url="https://tgsafe.telangana.gov.in/enforcement",
        fetcher=_StubFetcher(payload),
    )
    rows = adapter.parse(adapter.fetch())
    batch = adapter.validate_and_emit_batch(rows)

    assert len(batch.quarantined) == 1
    events = [e for e in batch.entities if isinstance(e, AuthoritativeEvent)]
    assert len(events) == 1
    assert events[0].event_type == "enforcement_raid_or_suspension"
    assert events[0].status == "Suspended"
    assert events[0].provenance.source_name == "Telangana TG SAFE"
    assert len(adapter.validate_and_emit(rows)) == 2


def test_ondc_catalog_adapter_emits_premises_and_brand_listing() -> None:
    payload = json.dumps(
        [
            {
                "fssai_id": "13624001000999",
                "legal_name": "Spice Route Hospitality LLP",
                "display_name": "Midnight Biryani Express",
                "premises_type": "cloud_kitchen",
                "postal_code": "500081",
                "city": "Hyderabad",
                "state": "Telangana",
                "seen_at": "2026-04-10T12:00:00Z",
            },
            {
                "fssai_id": "13624001000999",
                "legal_name": "Spice Route Hospitality LLP",
                "display_name": "",
            },
        ]
    ).encode("utf-8")

    adapter = ONDCCatalogAdapter(fetcher=_StubFetcher(payload))
    rows = adapter.parse(adapter.fetch())
    batch = adapter.validate_and_emit_batch(rows)

    assert len(batch.quarantined) == 1
    premises = [e for e in batch.entities if isinstance(e, FoodPremises)]
    listings = [e for e in batch.entities if isinstance(e, BrandListing)]
    assert len(premises) == 1
    assert len(listings) == 1
    assert listings[0].platform == "ondc"
    assert listings[0].display_name == "Midnight Biryani Express"
    assert listings[0].premises_entity_id == premises[0].entity_id
    assert len(adapter.validate_and_emit(rows)) == 2
