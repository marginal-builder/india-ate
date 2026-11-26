"""Parameterized SQLite tuple builders for india-ate store."""

from india_ate.models import (
    AuthoritativeEvent,
    BrandListing,
    FoodItem,
    FoodPremises,
    QuarantinedRecord,
    ScientificStandard,
    Substance,
)

FSSAI_SCHEME = "IN_FSSAI_14"


def extract_fssai_id(premises: FoodPremises) -> str | None:
    """Return the first 14-digit FSSAI ID on a FoodPremises, if present."""
    for reg in premises.regulatory_ids:
        if reg.scheme == FSSAI_SCHEME:
            return reg.raw_value.strip()
    return None


def premises_params(premises: FoodPremises) -> tuple[object, ...]:
    """Build parameterized SQL tuple for a FoodPremises row."""
    return (
        premises.entity_id,
        premises.legal_name,
        premises.jurisdiction_iso,
        premises.premises_type,
        premises.address,
        premises.postal_code,
        premises.city,
        premises.state,
        premises.lat,
        premises.lon,
        extract_fssai_id(premises),
        premises.model_dump_json(),
    )


def brand_listing_params(listing: BrandListing) -> tuple[object, ...]:
    """Build parameterized SQL tuple for a BrandListing row."""
    return (
        listing.listing_id,
        listing.display_name,
        listing.platform,
        listing.premises_entity_id,
        listing.postal_code,
        listing.first_seen_at.isoformat(),
        listing.last_seen_at.isoformat(),
        listing.model_dump_json(),
    )


def event_params(event: AuthoritativeEvent) -> tuple[object, ...]:
    """Build parameterized SQL tuple for an AuthoritativeEvent row."""
    return (
        event.event_id,
        event.event_type,
        event.target_entity_id,
        event.jurisdiction_iso,
        event.event_date.isoformat(),
        event.status,
        event.batch_or_lot_no,
        event.verbatim_summary,
        event.model_dump_json(),
    )


def quarantined_params(record: QuarantinedRecord) -> tuple[object, ...]:
    """Build parameterized SQL tuple for a QuarantinedRecord row."""
    return (
        record.source_name,
        record.reason,
        record.quarantined_at.isoformat(),
        record.model_dump_json(),
    )


def food_item_params(item: FoodItem) -> tuple[object, ...]:
    """Build parameterized SQL tuple for a FoodItem row."""
    return (
        item.item_id,
        item.canonical_name,
        item.item_kind,
        item.ifct_code,
        item.foodon_uri,
        item.gtin_barcode,
        item.model_dump_json(),
    )


def substance_params(substance: Substance) -> tuple[object, ...]:
    """Build parameterized SQL tuple for a Substance row."""
    return (
        substance.substance_id,
        substance.canonical_name,
        substance.substance_class,
        substance.cas_number,
        substance.ins_e_number,
        substance.model_dump_json(),
    )


def scientific_standard_params(standard: ScientificStandard) -> tuple[object, ...]:
    """Build parameterized SQL tuple for a ScientificStandard row."""
    return (
        standard.standard_id,
        standard.standard_type,
        standard.jurisdiction_iso,
        standard.substance_id,
        standard.food_item_id,
        standard.value,
        standard.unit,
        standard.model_dump_json(),
    )
