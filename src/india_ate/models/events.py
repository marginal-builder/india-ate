"""Authoritative enforcement, recall, hygiene audit, and grievance events."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

from india_ate.models.base import EvidenceProvenance

EventType = Literal[
    "license_status_snapshot",
    "hygiene_audit",
    "food_recall",
    "enforcement_raid_or_suspension",
    "lab_test_result",
    "grievance_ticket",
]


class AuthoritativeEvent(BaseModel):
    """Strictly factual enforcement, recall, audit, lab, or grievance event."""

    model_config = ConfigDict(strict=True, frozen=True)

    event_id: str
    event_type: EventType
    target_entity_id: str
    jurisdiction_iso: str
    event_date: date
    status: str
    batch_or_lot_no: str | None = None
    verbatim_summary: str
    provenance: EvidenceProvenance
