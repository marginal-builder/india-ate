"""Acceptance tests for substance.feature."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from pytest_bdd import given, parsers, scenarios, then, when

from india_ate.models import Substance

FEATURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "features"
    / "entity_graph"
    / "substance.feature"
)
scenarios(str(FEATURE_PATH))


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {"error": None}


@given(
    parsers.parse(
        'a Substance with substance_id "{substance_id}", canonical_name '
        '"{canonical_name}", substance_class "{substance_class}", cas_number '
        '"{cas_number}", pubchem_cid "{pubchem_cid}", and ins_e_number '
        '"{ins_e_number}"'
    )
)
def given_full_substance(
    ctx: dict[str, Any],
    substance_id: str,
    canonical_name: str,
    substance_class: str,
    cas_number: str,
    pubchem_cid: str,
    ins_e_number: str,
) -> None:
    ctx["substance"] = Substance(
        substance_id=substance_id,
        canonical_name=canonical_name,
        substance_class=substance_class,  # type: ignore[arg-type]
        cas_number=cas_number,
        pubchem_cid=pubchem_cid,
        ins_e_number=ins_e_number,
    )


@given(
    parsers.parse(
        'a Substance with substance_id "{substance_id}", canonical_name '
        '"{canonical_name}", substance_class "{substance_class}", and '
        "cas_number {cas_raw}"
    )
)
def given_outline_substance(
    ctx: dict[str, Any],
    substance_id: str,
    canonical_name: str,
    substance_class: str,
    cas_raw: str,
) -> None:
    cas = None if cas_raw == "null" else cas_raw.strip('"')
    ctx["substance"] = Substance(
        substance_id=substance_id,
        canonical_name=canonical_name,
        substance_class=substance_class,  # type: ignore[arg-type]
        cas_number=cas,
    )


@given(
    parsers.parse(
        'a Substance with substance_id "{substance_id}", canonical_name '
        '"{canonical_name}", and substance_class "{substance_class}"'
    )
)
def given_minimal_substance(
    ctx: dict[str, Any],
    substance_id: str,
    canonical_name: str,
    substance_class: str,
) -> None:
    ctx["substance"] = Substance(
        substance_id=substance_id,
        canonical_name=canonical_name,
        substance_class=substance_class,  # type: ignore[arg-type]
    )


@given(
    parsers.parse(
        'a valid Substance with substance_id "{substance_id}" and '
        'canonical_name "{canonical_name}"'
    )
)
def given_valid_substance(
    ctx: dict[str, Any], substance_id: str, canonical_name: str
) -> None:
    ctx["substance"] = Substance(
        substance_id=substance_id,
        canonical_name=canonical_name,
        substance_class="additive",
    )


@when(parsers.parse('I attempt to create a Substance with substance_class "{sclass}"'))
def attempt_invalid_sclass(ctx: dict[str, Any], sclass: str) -> None:
    try:
        Substance(
            substance_id="substance:bad",
            canonical_name="Bad",
            substance_class=sclass,  # type: ignore[arg-type]
        )
    except ValidationError as exc:
        ctx["error"] = exc


@when("I attempt to mutate its cas_number")
def mutate_cas(ctx: dict[str, Any]) -> None:
    try:
        ctx["substance"].cas_number = "000-00-0"
    except ValidationError as exc:
        ctx["error"] = exc


@when(
    parsers.parse("I attempt to create a Substance with integer {num:d} as cas_number")
)
def attempt_int_cas(ctx: dict[str, Any], num: int) -> None:
    try:
        Substance(
            substance_id="substance:bad:2",
            canonical_name="Bad",
            substance_class="additive",
            cas_number=num,  # type: ignore[arg-type]
        )
    except ValidationError as exc:
        ctx["error"] = exc


@then("the Substance is valid")
def check_substance_valid(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["substance"], Substance)


@then(parsers.parse('its substance_class is "{sclass}"'))
def check_sclass(ctx: dict[str, Any], sclass: str) -> None:
    assert ctx["substance"].substance_class == sclass


@then(parsers.parse('its cas_number is "{cas}"'))
def check_cas(ctx: dict[str, Any], cas: str) -> None:
    assert ctx["substance"].cas_number == cas


@then(parsers.parse('its pubchem_cid is "{cid}"'))
def check_cid(ctx: dict[str, Any], cid: str) -> None:
    assert ctx["substance"].pubchem_cid == cid


@then(parsers.parse('its ins_e_number is "{ins}"'))
def check_ins(ctx: dict[str, Any], ins: str) -> None:
    assert ctx["substance"].ins_e_number == ins


@then("cas_number is null")
def check_cas_null(ctx: dict[str, Any]) -> None:
    assert ctx["substance"].cas_number is None


@then("pubchem_cid is null")
def check_cid_null(ctx: dict[str, Any]) -> None:
    assert ctx["substance"].pubchem_cid is None


@then("ins_e_number is null")
def check_ins_null(ctx: dict[str, Any]) -> None:
    assert ctx["substance"].ins_e_number is None


@then("a ValidationError is raised")
def check_validation_error(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["error"], ValidationError)
