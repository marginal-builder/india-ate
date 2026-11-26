"""Pure objective Fact Receipt assembly service."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from india_ate.models import (
    AuthoritativeEvent,
    BrandListing,
    FoodPremises,
    IndiaFSSAI14,
)
from india_ate.store import SQLiteStore


class FactReceipt(BaseModel):
    """Strictly objective, source-verified Fact Receipt for a 14-digit FSSAI ID."""

    model_config = ConfigDict(strict=True, frozen=True)

    fssai_id: str
    decoded: dict[str, object]
    premises: FoodPremises | None
    ghost_brand_count: int
    brand_listings: list[BrandListing]
    events: list[AuthoritativeEvent]
    last_verified_at: datetime | None


def _compute_last_verified_at(
    premises: FoodPremises, events: list[AuthoritativeEvent]
) -> datetime | None:
    timestamps = [p.retrieved_at for p in premises.provenance]
    timestamps.extend(event.provenance.retrieved_at for event in events)
    return max(timestamps) if timestamps else None


def _empty_receipt(clean_id: str, decoded: dict[str, object]) -> FactReceipt:
    return FactReceipt(
        fssai_id=clean_id,
        decoded=decoded,
        premises=None,
        ghost_brand_count=0,
        brand_listings=[],
        events=[],
        last_verified_at=None,
    )


def build_fact_receipt(store: SQLiteStore, fssai_id: str) -> FactReceipt:
    """Assemble an objective Fact Receipt for a 14-digit FSSAI ID."""
    clean_id = fssai_id.strip()
    decoded = IndiaFSSAI14(raw_value=clean_id).decode_offline()
    premises = store.get_premises_by_fssai_id(clean_id)
    if premises is None:
        return _empty_receipt(clean_id, decoded)
    listings = store.get_brand_listings_for_premises(premises.entity_id)
    events = sorted(
        store.get_events_for_target(premises.entity_id),
        key=lambda ev: ev.event_date,
        reverse=True,
    )
    return FactReceipt(
        fssai_id=clean_id,
        decoded=decoded,
        premises=premises,
        ghost_brand_count=len(listings),
        brand_listings=listings,
        events=events,
        last_verified_at=_compute_last_verified_at(premises, events),
    )
