"""Unit tests for AuthoritativeEvent model."""

from datetime import date

import pytest
from pydantic import ValidationError

from india_ate.models.base import EvidenceProvenance
from india_ate.models.events import AuthoritativeEvent, EventType


@pytest.mark.parametrize(
    ("event_id", "event_type", "status"),
    [
        ("evt:lic:001", "license_status_snapshot", "Active"),
        ("evt:audit:001", "hygiene_audit", "Active"),
        ("evt:recall:001", "food_recall", "Initiated"),
        ("evt:raid:001", "enforcement_raid_or_suspension", "Suspended"),
        ("evt:lab:001", "lab_test_result", "Active"),
        ("evt:griev:001", "grievance_ticket", "Escalated_15d"),
    ],
)
def test_authoritative_event_types(
    event_id: str,
    event_type: EventType,
    status: str,
    official_provenance: EvidenceProvenance,
) -> None:
    evt = AuthoritativeEvent(
        event_id=event_id,
        event_type=event_type,
        target_entity_id="actor:in:fssai:10013022000417",
        jurisdiction_iso="IN",
        event_date=date(2026, 4, 1),
        status=status,
        verbatim_summary="Verbatim authoritative summary.",
        provenance=official_provenance,
    )
    assert evt.event_type == event_type
    assert evt.batch_or_lot_no is None


def test_authoritative_event_validation_and_immutability(
    sample_event: AuthoritativeEvent,
    official_provenance: EvidenceProvenance,
) -> None:
    assert sample_event.batch_or_lot_no == "LOT-MH-2026-09"
    with pytest.raises(ValidationError):
        AuthoritativeEvent(
            event_id="evt:bad",
            event_type="unverified_rumor",  # type: ignore[arg-type]
            target_entity_id="actor:in:fssai:10013022000417",
            jurisdiction_iso="IN",
            event_date=date(2026, 4, 1),
            status="Active",
            verbatim_summary="Bad",
            provenance=official_provenance,
        )
    with pytest.raises(ValidationError):
        sample_event.status = "Cleared"  # type: ignore[misc]
