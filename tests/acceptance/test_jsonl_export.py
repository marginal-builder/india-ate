"""Acceptance tests for jsonl_export.feature."""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from pytest_bdd import given, scenarios, then, when

from india_ate.models import (
    AuthoritativeEvent,
    BrandListing,
    FoodItem,
    FoodPremises,
    ScientificStandard,
    Substance,
)
from india_ate.store import export_jsonl, import_jsonl

FEATURE_PATH = (
    Path(__file__).resolve().parents[2] / "features" / "store" / "jsonl_export.feature"
)
scenarios(str(FEATURE_PATH))


@pytest.fixture
def ctx(tmp_path: Path) -> dict[str, Any]:
    return {"tmp_path": tmp_path, "dataset": [], "reconstructed": [], "error": None}


@given(
    "a dataset containing FoodPremises, BrandListing, FoodItem, Substance, "
    "ScientificStandard, and AuthoritativeEvent records"
)
def given_full_dataset(
    ctx: dict[str, Any],
    sample_premises: FoodPremises,
    sample_brand_listing: BrandListing,
    sample_food_item: FoodItem,
    sample_substance: Substance,
    sample_standard: ScientificStandard,
    sample_event: AuthoritativeEvent,
) -> None:
    ctx["dataset"] = [
        sample_premises,
        sample_brand_listing,
        sample_food_item,
        sample_substance,
        sample_standard,
        sample_event,
    ]


@given("an empty dataset with 0 records")
def given_empty_dataset(ctx: dict[str, Any]) -> None:
    ctx["dataset"] = []


@given('a ".jsonl" file containing a truncated or invalid JSON line')
def given_malformed_jsonl(ctx: dict[str, Any]) -> None:
    bad_path = ctx["tmp_path"] / "malformed.jsonl"
    bad_path.write_text('{"entity_type": "FoodItem", "payload": ', encoding="utf-8")
    ctx["jsonl_path"] = bad_path


@when('I export the dataset to a ".jsonl" file')
def export_dataset(ctx: dict[str, Any]) -> None:
    out_path = ctx["tmp_path"] / "export.jsonl"
    export_jsonl(ctx["dataset"], out_path)
    ctx["jsonl_path"] = out_path


@when('I import the ".jsonl" file back into Pydantic entity models')
def import_dataset(ctx: dict[str, Any]) -> None:
    ctx["reconstructed"] = import_jsonl(ctx["jsonl_path"])


@when('I import the empty ".jsonl" file')
def import_empty_dataset(ctx: dict[str, Any]) -> None:
    ctx["reconstructed"] = import_jsonl(ctx["jsonl_path"])


@when('I attempt to import the ".jsonl" file')
def attempt_import_malformed(ctx: dict[str, Any]) -> None:
    try:
        import_jsonl(ctx["jsonl_path"])
    except (ValueError, ValidationError) as exc:
        ctx["error"] = exc


@then('every line in the ".jsonl" file is valid UTF-8 JSON')
def check_valid_utf8_json(ctx: dict[str, Any]) -> None:
    lines = ctx["jsonl_path"].read_text(encoding="utf-8").splitlines()
    for line in lines:
        json.loads(line)
    ctx["lines"] = lines


@then("the line count equals the total number of exported records")
def check_line_count(ctx: dict[str, Any]) -> None:
    assert len(ctx["lines"]) == len(ctx["dataset"])


@then(
    "every reconstructed entity equals the original entity including nested "
    "EvidenceProvenance and RegulatoryIdentifier"
)
def check_roundtrip_equals(ctx: dict[str, Any]) -> None:
    assert ctx["reconstructed"] == ctx["dataset"]


@then('the ".jsonl" file contains 0 lines')
def check_zero_lines(ctx: dict[str, Any]) -> None:
    assert ctx["jsonl_path"].read_text(encoding="utf-8").splitlines() == []


@then("0 records are returned")
def check_zero_records(ctx: dict[str, Any]) -> None:
    assert ctx["reconstructed"] == []


@then("a ValueError or ValidationError is raised")
def check_error_raised(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["error"], (ValueError, ValidationError))
