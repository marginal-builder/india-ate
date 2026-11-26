"""Unit tests for SQLiteStore quarantine and atomic batch persistence."""

from datetime import UTC, date, datetime

from pydantic import HttpUrl

from india_ate.models import (
    AuthoritativeEvent,
    EvidenceProvenance,
    FoodPremises,
    IndiaFSSAI14,
    IngestionBatch,
    QuarantinedRecord,
)
from india_ate.store import SQLiteStore


def _make_provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        source_name="FSSAI Hygiene Rating Portal",
        source_url=HttpUrl("https://hygiene.fssai.gov.in/snapshot"),
        retrieved_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
        content_sha256="deadbeef",
        verification_tier="official_registry",
    )


def test_sqlite_store_save_ingestion_batch_and_list_quarantined() -> None:
    prov = _make_provenance()
    premises = FoodPremises(
        entity_id="actor:in:fssai:10011034002374",
        legal_name="Eastern Foods",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value="10011034002374")],
        provenance=[prov],
        premises_type="restaurant",
    )
    event = AuthoritativeEvent(
        event_id="evt:hygiene:10011034002374:2026-03-01",
        event_type="hygiene_audit",
        target_entity_id=premises.entity_id,
        jurisdiction_iso="IN",
        event_date=date(2026, 3, 1),
        status="5/5",
        verbatim_summary="FSSAI Hygiene Rating 5/5 audited on 2026-03-01",
        provenance=prov,
    )
    quarantined = QuarantinedRecord(
        source_name="FSSAI Hygiene Rating Portal",
        raw_record={"fssai_id": "bad-id"},
        reason="FSSAI ID must be a 14-digit numeric string",
        quarantined_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
    )
    batch = IngestionBatch(entities=[premises, event], quarantined=[quarantined])

    with SQLiteStore(":memory:") as store:
        store.initialize()
        store.save_ingestion_batch(batch)

        loaded_premises = store.get_premises_by_fssai_id("10011034002374")
        assert loaded_premises is not None
        assert loaded_premises.entity_id == "actor:in:fssai:10011034002374"

        loaded_events = store.get_events_for_target(premises.entity_id)
        assert len(loaded_events) == 1
        assert loaded_events[0].event_type == "hygiene_audit"

        all_quarantined = store.list_quarantined()
        assert len(all_quarantined) == 1
        assert all_quarantined[0].reason == quarantined.reason
        assert (
            len(store.list_quarantined(source_name="FSSAI Hygiene Rating Portal")) == 1
        )
        assert store.list_quarantined(source_name="Other Source") == []
