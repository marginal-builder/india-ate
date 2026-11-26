"""Ghost-Brand Cluster & Verified Nearby Switch discovery services."""

from pydantic import BaseModel, ConfigDict

from india_ate.models import AuthoritativeEvent, FoodPremises
from india_ate.services._provenance import is_official_event
from india_ate.store import GhostBrandCluster, SQLiteStore

_NEGATIVE_EVENT_TYPES: frozenset[str] = frozenset(
    {"food_recall", "enforcement_raid_or_suspension"}
)


class VerifiedSwitchOption(BaseModel):
    """Factual nearby premises option with completed audits or Tier-1 license."""

    model_config = ConfigDict(strict=True, frozen=True)

    premises: FoodPremises
    verification_reasons: list[str]
    hygiene_events: list[AuthoritativeEvent]


def get_ghost_brand_cluster(
    store: SQLiteStore, fssai_id: str
) -> GhostBrandCluster | None:
    """Return physical premises and all BrandListings sharing its FSSAI ID."""
    return store.query_ghost_brand_cluster(fssai_id.strip())


def _has_tier1_license(premises: FoodPremises) -> bool:
    return any(
        reg.scheme == "IN_FSSAI_14" and reg.raw_value.strip().startswith("1")
        for reg in premises.regulatory_ids
    )


def _evaluate_premises(
    store: SQLiteStore, premises: FoodPremises
) -> VerifiedSwitchOption | None:
    events = [
        event
        for event in store.get_events_for_target(premises.entity_id)
        if is_official_event(event)
    ]
    if any(ev.event_type in _NEGATIVE_EVENT_TYPES for ev in events):
        return None
    hygiene_events = [ev for ev in events if ev.event_type == "hygiene_audit"]
    reasons = [f"Completed FSSAI Hygiene Audit ({ev.status})" for ev in hygiene_events]
    if _has_tier1_license(premises):
        reasons.append("State/Central Tier-1 License")
    if not reasons:
        return None
    return VerifiedSwitchOption(
        premises=premises,
        verification_reasons=reasons,
        hygiene_events=hygiene_events,
    )


def find_verified_nearby_switches(
    store: SQLiteStore, postal_code: str
) -> list[VerifiedSwitchOption]:
    """Find premises in postal_code with hygiene audits or Tier-1 licenses."""
    candidates = store.query_nearby_premises(postal_code.strip())
    options = [_evaluate_premises(store, premises) for premises in candidates]
    return [opt for opt in options if opt is not None]
