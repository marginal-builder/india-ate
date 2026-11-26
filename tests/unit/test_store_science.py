"""Unit tests for FoodItem, Substance, and ScientificStandard SQLite persistence."""

from datetime import UTC, date, datetime

from pydantic import HttpUrl

from india_ate.models import (
    BrandListing,
    EvidenceProvenance,
    FoodItem,
    IngestionBatch,
    ScientificStandard,
    Substance,
)
from india_ate.store import SQLiteStore


def _sci_provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        source_name="ICMR-NIN IFCT 2017",
        source_url=HttpUrl("https://github.com/ifct2017/ifct2017"),
        retrieved_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
        content_sha256="abcdef1234",
        verification_tier="peer_reviewed_science",
    )


def test_sqlite_store_food_item_substance_and_standards() -> None:
    prov = _sci_provenance()
    item = FoodItem(
        item_id="item:in:ifct:A001",
        canonical_name="Amaranth seed, black",
        item_kind="raw_staple",
        ifct_code="A001",
    )
    substance = Substance(
        substance_id="sub:ifct:protcnt",
        canonical_name="Protein",
        substance_class="nutrient",
    )
    standard = ScientificStandard(
        standard_id="std:in:ifct:A001:protcnt",
        standard_type="nutrient_composition",
        jurisdiction_iso="IN",
        substance_id=substance.substance_id,
        food_item_id=item.item_id,
        value=14.59,
        unit="g/100g",
        effective_date=date(2017, 1, 1),
        provenance=prov,
    )
    listing = BrandListing(
        listing_id="listing:ondc:1",
        display_name="Amaranth Kitchen",
        platform="ondc",
        premises_entity_id="actor:in:fssai:10011034002374",
        postal_code="500081",
        first_seen_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
        last_seen_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
        provenance=prov,
    )
    batch = IngestionBatch(entities=[item, substance, standard, listing])

    with SQLiteStore(":memory:") as store:
        store.initialize()
        store.save_ingestion_batch(batch)

        loaded_item = store.get_food_item("item:in:ifct:A001")
        assert loaded_item is not None
        assert loaded_item.ifct_code == "A001"
        assert len(store.search_food_items("Amaranth")) == 1
        assert store.search_food_items("NonExistent") == []

        loaded_sub = store.get_substance("sub:ifct:protcnt")
        assert loaded_sub is not None
        assert loaded_sub.canonical_name == "Protein"

        stds_by_food = store.get_standards_for_food_item("item:in:ifct:A001")
        assert len(stds_by_food) == 1
        assert stds_by_food[0].value == 14.59

        stds_by_sub = store.get_standards_for_substance("sub:ifct:protcnt")
        assert len(stds_by_sub) == 1
        assert stds_by_sub[0].standard_id == "std:in:ifct:A001:protcnt"

        listings = store.get_brand_listings_for_premises(
            "actor:in:fssai:10011034002374"
        )
        assert len(listings) == 1

        item2 = FoodItem(
            item_id="item:in:ifct:A002",
            canonical_name="Bajra",
            item_kind="raw_staple",
            ifct_code="A002",
        )
        sub2 = Substance(
            substance_id="sub:ifct:fe",
            canonical_name="Iron",
            substance_class="nutrient",
        )
        std2 = ScientificStandard(
            standard_id="std:in:ifct:A002:fe",
            standard_type="nutrient_composition",
            jurisdiction_iso="IN",
            substance_id=sub2.substance_id,
            food_item_id=item2.item_id,
            value=6.42,
            unit="mg/100g",
            provenance=prov,
        )
        store.save_food_item(item2)
        store.save_substance(sub2)
        store.save_scientific_standard(std2)
        assert store.get_food_item("item:in:ifct:A002") == item2
        assert store.get_substance("sub:ifct:fe") == sub2
        assert store.get_standards_for_food_item("item:in:ifct:A002") == [std2]
