"""Acceptance tests for scientific_standard.feature."""

from datetime import date
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from pytest_bdd import given, parsers, scenarios, then, when

from india_ate.models import EvidenceProvenance, ScientificStandard

FEATURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "features"
    / "entity_graph"
    / "scientific_standard.feature"
)
scenarios(str(FEATURE_PATH))


@pytest.fixture
def ctx(
    official_provenance: EvidenceProvenance,
    science_provenance: EvidenceProvenance,
) -> dict[str, Any]:
    return {
        "official_provenance": official_provenance,
        "science_provenance": science_provenance,
        "error": None,
    }


@given(
    parsers.parse(
        'a ScientificStandard with standard_id "{standard_id}", standard_type '
        '"{standard_type}", jurisdiction_iso "{jurisdiction_iso}", substance_id '
        '"{substance_id}", food_item_id "{food_item_id}", value {value:f}, '
        'unit "{unit}", effective_date "{effective_date}", and valid '
        "official_registry provenance"
    )
)
def given_mrl_standard(
    ctx: dict[str, Any],
    standard_id: str,
    standard_type: str,
    jurisdiction_iso: str,
    substance_id: str,
    food_item_id: str,
    value: float,
    unit: str,
    effective_date: str,
) -> None:
    ctx["standard"] = ScientificStandard(
        standard_id=standard_id,
        standard_type=standard_type,  # type: ignore[arg-type]
        jurisdiction_iso=jurisdiction_iso,
        substance_id=substance_id,
        food_item_id=food_item_id,
        value=value,
        unit=unit,
        effective_date=date.fromisoformat(effective_date),
        provenance=ctx["official_provenance"],
    )


@given(
    parsers.parse(
        'a ScientificStandard with standard_id "{standard_id}", standard_type '
        '"{standard_type}", jurisdiction_iso "{jurisdiction_iso}", substance_id '
        '"{substance_id}", value {value:f}, unit "{unit}", and valid '
        "peer_reviewed_science provenance"
    )
)
def given_science_standard(
    ctx: dict[str, Any],
    standard_id: str,
    standard_type: str,
    jurisdiction_iso: str,
    substance_id: str,
    value: float,
    unit: str,
) -> None:
    ctx["standard"] = ScientificStandard(
        standard_id=standard_id,
        standard_type=standard_type,  # type: ignore[arg-type]
        jurisdiction_iso=jurisdiction_iso,
        substance_id=substance_id,
        value=value,
        unit=unit,
        provenance=ctx["science_provenance"],
    )


@given(
    parsers.parse(
        'a ScientificStandard with standard_id "{standard_id}", standard_type '
        '"{standard_type}", jurisdiction_iso "{jurisdiction_iso}", substance_id '
        '"{substance_id}", value {value:f}, unit "{unit}", and valid provenance'
    )
)
def given_outline_standard(
    ctx: dict[str, Any],
    standard_id: str,
    standard_type: str,
    jurisdiction_iso: str,
    substance_id: str,
    value: float,
    unit: str,
) -> None:
    ctx["standard"] = ScientificStandard(
        standard_id=standard_id,
        standard_type=standard_type,  # type: ignore[arg-type]
        jurisdiction_iso=jurisdiction_iso,
        substance_id=substance_id,
        value=value,
        unit=unit,
        provenance=ctx["official_provenance"],
    )


@given(
    parsers.parse('a valid ScientificStandard with value {value:f} and unit "{unit}"')
)
def given_valid_standard(ctx: dict[str, Any], value: float, unit: str) -> None:
    ctx["standard"] = ScientificStandard(
        standard_id="std:test",
        standard_type="statutory_mrl",
        jurisdiction_iso="IN",
        substance_id="substance:cas:2921-88-2",
        value=value,
        unit=unit,
        provenance=ctx["official_provenance"],
    )


@when(
    parsers.parse(
        'I attempt to create a ScientificStandard with standard_type "{stype}"'
    )
)
def attempt_invalid_stype(ctx: dict[str, Any], stype: str) -> None:
    try:
        ScientificStandard(
            standard_id="std:bad",
            standard_type=stype,  # type: ignore[arg-type]
            jurisdiction_iso="IN",
            substance_id="substance:cas:2921-88-2",
            value=0.05,
            unit="mg/kg",
            provenance=ctx["official_provenance"],
        )
    except ValidationError as exc:
        ctx["error"] = exc


@when("I attempt to mutate its value")
def mutate_value(ctx: dict[str, Any]) -> None:
    try:
        ctx["standard"].value = 99.9
    except ValidationError as exc:
        ctx["error"] = exc


@when(
    parsers.parse(
        'I attempt to create a ScientificStandard with string "{val}" as value'
    )
)
def attempt_str_value(ctx: dict[str, Any], val: str) -> None:
    try:
        ScientificStandard(
            standard_id="std:bad:2",
            standard_type="statutory_mrl",
            jurisdiction_iso="IN",
            substance_id="substance:cas:2921-88-2",
            value=val,  # type: ignore[arg-type]
            unit="mg/kg",
            provenance=ctx["official_provenance"],
        )
    except ValidationError as exc:
        ctx["error"] = exc


@when("I attempt to create a ScientificStandard without provenance")
def attempt_missing_provenance(ctx: dict[str, Any]) -> None:
    try:
        ScientificStandard(  # type: ignore[call-arg]
            standard_id="std:bad:3",
            standard_type="statutory_mrl",
            jurisdiction_iso="IN",
            substance_id="substance:cas:2921-88-2",
            value=0.05,
            unit="mg/kg",
        )
    except ValidationError as exc:
        ctx["error"] = exc


@then("the ScientificStandard is valid")
def check_std_valid(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["standard"], ScientificStandard)


@then(parsers.parse('its standard_type is "{stype}"'))
def check_stype(ctx: dict[str, Any], stype: str) -> None:
    assert ctx["standard"].standard_type == stype


@then(parsers.parse('its jurisdiction_iso is "{iso}"'))
def check_iso(ctx: dict[str, Any], iso: str) -> None:
    assert ctx["standard"].jurisdiction_iso == iso


@then(parsers.parse("its value is {val:f}"))
def check_val(ctx: dict[str, Any], val: float) -> None:
    assert ctx["standard"].value == val


@then(parsers.parse('its unit is "{unit}"'))
def check_unit(ctx: dict[str, Any], unit: str) -> None:
    assert ctx["standard"].unit == unit


@then(parsers.parse('its food_item_id is "{item_id}"'))
def check_food_item_id(ctx: dict[str, Any], item_id: str) -> None:
    assert ctx["standard"].food_item_id == item_id


@then("its food_item_id is null")
def check_food_item_id_null(ctx: dict[str, Any]) -> None:
    assert ctx["standard"].food_item_id is None


@then("its effective_date is null")
def check_effective_date_null(ctx: dict[str, Any]) -> None:
    assert ctx["standard"].effective_date is None


@then(parsers.parse('its provenance verification_tier is "{tier}"'))
def check_prov_tier(ctx: dict[str, Any], tier: str) -> None:
    assert ctx["standard"].provenance.verification_tier == tier


@then("a ValidationError is raised")
def check_validation_error(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["error"], ValidationError)
