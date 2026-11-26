"""Acceptance tests for food_item.feature."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from pytest_bdd import given, parsers, scenarios, then, when

from india_ate.models import FoodItem

FEATURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "features"
    / "entity_graph"
    / "food_item.feature"
)
scenarios(str(FEATURE_PATH))


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {"items": [], "error": None}


@given(
    parsers.parse(
        'a FoodItem with item_id "{item_id}", canonical_name "{canonical_name}", '
        'item_kind "{item_kind}", foodon_uri "{foodon_uri}", and ifct_code '
        '"{ifct_code}"'
    )
)
def given_raw_staple(
    ctx: dict[str, Any],
    item_id: str,
    canonical_name: str,
    item_kind: str,
    foodon_uri: str,
    ifct_code: str,
) -> None:
    ctx["item"] = FoodItem(
        item_id=item_id,
        canonical_name=canonical_name,
        item_kind=item_kind,  # type: ignore[arg-type]
        foodon_uri=foodon_uri,
        ifct_code=ifct_code,
    )


@given(
    parsers.parse(
        'a FoodItem with item_id "{item_id}", canonical_name "{canonical_name}", '
        'item_kind "{item_kind}", gtin_barcode "{gtin_barcode}", '
        'manufacturer_premises_ids containing "{mfg_id}", and '
        'marketer_actor_ids containing "{mkt_id}"'
    )
)
def given_packaged_product(
    ctx: dict[str, Any],
    item_id: str,
    canonical_name: str,
    item_kind: str,
    gtin_barcode: str,
    mfg_id: str,
    mkt_id: str,
) -> None:
    ctx["item"] = FoodItem(
        item_id=item_id,
        canonical_name=canonical_name,
        item_kind=item_kind,  # type: ignore[arg-type]
        gtin_barcode=gtin_barcode,
        manufacturer_premises_ids=[mfg_id],
        marketer_actor_ids=[mkt_id],
    )


@given(
    parsers.parse(
        'a FoodItem with item_id "{item_id}", canonical_name "{canonical_name}", '
        'and item_kind "{item_kind}"'
    )
)
def given_other_food_item(
    ctx: dict[str, Any], item_id: str, canonical_name: str, item_kind: str
) -> None:
    ctx["items"].append(
        FoodItem(
            item_id=item_id,
            canonical_name=canonical_name,
            item_kind=item_kind,  # type: ignore[arg-type]
        )
    )


@given(
    parsers.parse(
        'a valid FoodItem with item_id "{item_id}" and canonical_name "{name}"'
    )
)
def given_valid_food_item(ctx: dict[str, Any], item_id: str, name: str) -> None:
    ctx["item"] = FoodItem(
        item_id=item_id,
        canonical_name=name,
        item_kind="raw_staple",
    )


@when(parsers.parse('I attempt to create a FoodItem with item_kind "{item_kind}"'))
def attempt_invalid_item_kind(ctx: dict[str, Any], item_kind: str) -> None:
    try:
        FoodItem(
            item_id="item:bad",
            canonical_name="Bad",
            item_kind=item_kind,  # type: ignore[arg-type]
        )
    except ValidationError as exc:
        ctx["error"] = exc


@when("I attempt to mutate its canonical_name")
def mutate_canonical_name(ctx: dict[str, Any]) -> None:
    try:
        ctx["item"].canonical_name = "Mutated"
    except ValidationError as exc:
        ctx["error"] = exc


@when(
    parsers.parse(
        "I attempt to create a FoodItem with integer {num:d} as canonical_name"
    )
)
def attempt_int_canonical_name(ctx: dict[str, Any], num: int) -> None:
    try:
        FoodItem(
            item_id="item:bad:2",
            canonical_name=num,  # type: ignore[arg-type]
            item_kind="raw_staple",
        )
    except ValidationError as exc:
        ctx["error"] = exc


@then("the FoodItem is valid")
def check_food_item_valid(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["item"], FoodItem)


@then("both FoodItems are valid")
def check_both_valid(ctx: dict[str, Any]) -> None:
    assert len(ctx["items"]) == 2
    assert all(isinstance(item, FoodItem) for item in ctx["items"])


@then(parsers.parse('its item_kind is "{item_kind}"'))
def check_item_kind(ctx: dict[str, Any], item_kind: str) -> None:
    assert ctx["item"].item_kind == item_kind


@then(parsers.parse('its foodon_uri is "{foodon_uri}"'))
def check_foodon_uri(ctx: dict[str, Any], foodon_uri: str) -> None:
    assert ctx["item"].foodon_uri == foodon_uri


@then(parsers.parse('its ifct_code is "{ifct_code}"'))
def check_ifct_code(ctx: dict[str, Any], ifct_code: str) -> None:
    assert ctx["item"].ifct_code == ifct_code


@then("its gtin_barcode is null")
def check_gtin_null(ctx: dict[str, Any]) -> None:
    assert ctx["item"].gtin_barcode is None


@then(parsers.parse('its gtin_barcode is "{gtin_barcode}"'))
def check_gtin_value(ctx: dict[str, Any], gtin_barcode: str) -> None:
    assert ctx["item"].gtin_barcode == gtin_barcode


@then("its manufacturer_premises_ids is empty")
def check_mfg_empty(ctx: dict[str, Any]) -> None:
    assert ctx["item"].manufacturer_premises_ids == []


@then("its marketer_actor_ids is empty")
def check_mkt_empty(ctx: dict[str, Any]) -> None:
    assert ctx["item"].marketer_actor_ids == []


@then(parsers.parse('manufacturer_premises_ids contains "{entity_id}"'))
def check_mfg_contains(ctx: dict[str, Any], entity_id: str) -> None:
    assert entity_id in ctx["item"].manufacturer_premises_ids


@then(parsers.parse('marketer_actor_ids contains "{entity_id}"'))
def check_mkt_contains(ctx: dict[str, Any], entity_id: str) -> None:
    assert entity_id in ctx["item"].marketer_actor_ids


@then("a ValidationError is raised")
def check_validation_error(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["error"], ValidationError)
