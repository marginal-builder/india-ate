"""Unit tests for FoodItem model."""

import pytest
from pydantic import ValidationError

from india_ate.models.food_item import FoodItem


def test_raw_staple_defaults(sample_food_item: FoodItem) -> None:
    assert sample_food_item.item_kind == "raw_staple"
    assert sample_food_item.gtin_barcode is None
    assert sample_food_item.manufacturer_premises_ids == []
    assert sample_food_item.marketer_actor_ids == []


def test_packaged_product_and_other_kinds() -> None:
    packaged = FoodItem(
        item_id="item:gtin:8901234567890",
        canonical_name="Masala Oats 500g",
        item_kind="packaged_product",
        gtin_barcode="8901234567890",
        manufacturer_premises_ids=["actor:in:fssai:10013022000417"],
        marketer_actor_ids=["actor:in:fssai:10411012000075"],
    )
    assert packaged.gtin_barcode == "8901234567890"
    dish = FoodItem(
        item_id="item:dish:paneer_tikka",
        canonical_name="Paneer Tikka",
        item_kind="menu_dish",
    )
    supp = FoodItem(
        item_id="item:supp:whey_01",
        canonical_name="Whey Protein Isolate",
        item_kind="supplement",
    )
    assert dish.item_kind == "menu_dish"
    assert supp.item_kind == "supplement"


def test_food_item_rejects_invalid_kind_and_is_frozen_strict(
    sample_food_item: FoodItem,
) -> None:
    with pytest.raises(ValidationError):
        FoodItem(
            item_id="item:bad:1",
            canonical_name="Snack",
            item_kind="unclassified_snack",  # type: ignore[arg-type]
        )
    with pytest.raises(ValidationError):
        sample_food_item.canonical_name = "Other"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        FoodItem(
            item_id="item:bad:2",
            canonical_name=42,  # type: ignore[arg-type]
            item_kind="raw_staple",
        )
