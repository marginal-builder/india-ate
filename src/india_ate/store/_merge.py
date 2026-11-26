"""Merge helpers for idempotent premises upserts."""

from india_ate.models import FoodPremises, RegulatoryIdentifier

_OPTIONAL_PREMISES_FIELDS = (
    "address",
    "postal_code",
    "city",
    "state",
    "lat",
    "lon",
)


def _dedup_merge[T](existing: list[T], incoming: list[T]) -> list[T]:
    merged = list(existing)
    for item in incoming:
        if item not in merged:
            merged.append(item)
    return merged


def _dedup_regulatory_ids(
    existing: list[RegulatoryIdentifier], incoming: list[RegulatoryIdentifier]
) -> list[RegulatoryIdentifier]:
    merged: list[RegulatoryIdentifier] = []
    seen: set[tuple[str, str, str]] = set()
    for reg in (*existing, *incoming):
        key = (reg.jurisdiction_iso, reg.scheme, reg.raw_value.strip())
        if key not in seen:
            seen.add(key)
            merged.append(reg)
    return merged


def merge_premises(existing: FoodPremises, incoming: FoodPremises) -> FoodPremises:
    """Merge provenance and regulatory IDs without dropping known optional fields."""
    updates: dict[str, object] = {
        "provenance": _dedup_merge(existing.provenance, incoming.provenance),
        "regulatory_ids": _dedup_regulatory_ids(
            existing.regulatory_ids, incoming.regulatory_ids
        ),
    }
    for field in _OPTIONAL_PREMISES_FIELDS:
        if getattr(incoming, field) is None:
            existing_val = getattr(existing, field)
            if existing_val is not None:
                updates[field] = existing_val
    return incoming.model_copy(update=updates)
