"""Food Safety Connect grievance packet generator (15-day escalation)."""

import hashlib
from datetime import UTC, date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl

from india_ate.models import AuthoritativeEvent, EvidenceProvenance, IndiaFSSAI14
from india_ate.store import SQLiteStore

FOOD_SAFETY_CONNECT_URL = "https://foscos.fssai.gov.in/consumergrievance/"
ESCALATION_WINDOW_DAYS = 15

GrievanceCategory = Literal[
    "spoiled_food",
    "misbranded",
    "shelf_life_30pct_violation",
    "unlicensed_or_suspended",
    "foreign_matter",
    "other",
]


class GrievancePacket(BaseModel):
    """Structured Food Safety Connect grievance packet."""

    model_config = ConfigDict(strict=True, frozen=True)

    packet_id: str
    portal_url: str
    fssai_id: str
    decoded_jurisdiction: dict[str, object]
    premises_legal_name: str | None
    premises_address: str | None
    issue_category: GrievanceCategory
    order_reference: str | None
    incident_date: date
    escalation_deadline: date
    description: str
    known_events_count: int
    ticket_event: AuthoritativeEvent | None = None


def _ticket_provenance(
    packet_id: str, fssai_id: str, description: str
) -> EvidenceProvenance:
    digest = hashlib.sha256(
        f"{packet_id}:{fssai_id}:{description}".encode()
    ).hexdigest()
    return EvidenceProvenance(
        source_name="Food Safety Connect Grievance Packet",
        source_url=HttpUrl(FOOD_SAFETY_CONNECT_URL),
        retrieved_at=datetime.now(UTC),
        content_sha256=digest,
        verification_tier="user_verified_snapshot",
    )


def _build_ticket_event(
    packet_id: str,
    fssai_id: str,
    issue_category: GrievanceCategory,
    incident_date: date,
    description: str,
) -> AuthoritativeEvent:
    prov = _ticket_provenance(packet_id, fssai_id, description)
    return AuthoritativeEvent(
        event_id=f"evt:grievance:{packet_id}",
        event_type="grievance_ticket",
        target_entity_id=f"actor:in:fssai:{fssai_id}",
        jurisdiction_iso="IN",
        event_date=incident_date,
        status="Escalated_15d",
        verbatim_summary=f"[{issue_category}] {description}",
        provenance=prov,
    )


def _maybe_persist_ticket(
    store: SQLiteStore,
    persist: bool,
    packet_id: str,
    clean_id: str,
    issue_category: GrievanceCategory,
    incident_date: date,
    clean_desc: str,
) -> AuthoritativeEvent | None:
    if not persist:
        return None
    ticket = _build_ticket_event(
        packet_id, clean_id, issue_category, incident_date, clean_desc
    )
    store.save_event(ticket)
    return ticket


def generate_grievance_packet(
    store: SQLiteStore,
    fssai_id: str,
    issue_category: GrievanceCategory,
    order_reference: str | None,
    description: str,
    incident_date: date,
    persist: bool = False,
) -> GrievancePacket:
    """Build a Food Safety Connect grievance packet with 15-day escalation."""
    clean_id = fssai_id.strip()
    decoded = IndiaFSSAI14(raw_value=clean_id).decode_offline()
    clean_desc = description.strip()
    if not clean_desc:
        raise ValueError("Grievance description must be non-empty")
    premises = store.get_premises_by_fssai_id(clean_id)
    events = store.get_events_for_target(premises.entity_id) if premises else []
    seed = f"{clean_id}:{issue_category}:{incident_date.isoformat()}:{clean_desc}"
    packet_id = hashlib.sha256(seed.encode()).hexdigest()[:16]
    ticket = _maybe_persist_ticket(
        store, persist, packet_id, clean_id, issue_category, incident_date, clean_desc
    )
    return GrievancePacket(
        packet_id=packet_id,
        portal_url=FOOD_SAFETY_CONNECT_URL,
        fssai_id=clean_id,
        decoded_jurisdiction=decoded,
        premises_legal_name=premises.legal_name if premises else None,
        premises_address=premises.address if premises else None,
        issue_category=issue_category,
        order_reference=order_reference.strip() if order_reference else None,
        incident_date=incident_date,
        escalation_deadline=incident_date + timedelta(days=ESCALATION_WINDOW_DAYS),
        description=clean_desc,
        known_events_count=len(events),
        ticket_event=ticket,
    )
