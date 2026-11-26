"""Acceptance tests for decode_offline.feature."""

import json
import shlex
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from pytest_bdd import given, parsers, scenarios, then, when

from india_ate.cli import app
from india_ate.models import IndiaFSSAI14, RegulatoryIdentifier

FEATURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "features"
    / "fssai_decoder"
    / "decode_offline.feature"
)
scenarios(str(FEATURE_PATH))


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {"error": None, "decoded": {}}


@given(parsers.parse('the FSSAI number "{raw}"'))
def given_fssai_number(ctx: dict[str, Any], raw: str) -> None:
    ctx["ident"] = IndiaFSSAI14(raw_value=raw)


@given(parsers.parse('an IndiaFSSAI14 identifier with raw_value "{raw}"'))
def given_india_fssai14(ctx: dict[str, Any], raw: str) -> None:
    ctx["ident"] = IndiaFSSAI14(raw_value=raw)


@when("I call decode_offline()")
def call_decode_offline(ctx: dict[str, Any]) -> None:
    try:
        ctx["decoded"] = ctx["ident"].decode_offline()
    except ValueError as exc:
        ctx["error"] = exc


@when(parsers.parse('I run the CLI command "{cmd}"'))
def run_cli_command(ctx: dict[str, Any], cmd: str) -> None:
    tokens = shlex.split(cmd)
    args = tokens[1:] if tokens and tokens[0] == "india-ate" else tokens
    runner = CliRunner()
    ctx["cli_result"] = runner.invoke(app, args)


@then(parsers.parse('the tier is "{tier}"'))
def check_tier(ctx: dict[str, Any], tier: str) -> None:
    assert ctx["decoded"]["tier"] == tier


@then("pre_inspection_exempt_post_apr2026 is false")
def check_exempt_false(ctx: dict[str, Any]) -> None:
    assert ctx["decoded"]["pre_inspection_exempt_post_apr2026"] is False


@then("pre_inspection_exempt_post_apr2026 is true")
def check_exempt_true(ctx: dict[str, Any]) -> None:
    assert ctx["decoded"]["pre_inspection_exempt_post_apr2026"] is True


@then(parsers.parse('the authority_scope is "{scope}"'))
def check_authority_scope(ctx: dict[str, Any], scope: str) -> None:
    assert ctx["decoded"]["authority_scope"] == scope


@then(parsers.parse('the state_code is "{code}"'))
def check_state_code(ctx: dict[str, Any], code: str) -> None:
    assert ctx["decoded"]["state_code"] == code


@then(parsers.parse('the state_name is "{name}"'))
def check_state_name(ctx: dict[str, Any], name: str) -> None:
    assert ctx["decoded"]["state_name"] == name


@then(parsers.parse("the registration_year is {year:d}"))
def check_registration_year(ctx: dict[str, Any], year: int) -> None:
    assert ctx["decoded"]["registration_year"] == year


@then(parsers.parse('the officer_code is "{code}"'))
def check_officer_code(ctx: dict[str, Any], code: str) -> None:
    assert ctx["decoded"]["officer_code"] == code


@then("the central_regional_office is null")
def check_ro_null(ctx: dict[str, Any]) -> None:
    assert ctx["decoded"]["central_regional_office"] is None


@then(parsers.parse('the central_regional_office is "{ro}"'))
def check_ro_value(ctx: dict[str, Any], ro: str) -> None:
    assert ctx["decoded"]["central_regional_office"] == ro


@then(parsers.parse('the officer_jurisdiction_state is "{state}"'))
def check_officer_state(ctx: dict[str, Any], state: str) -> None:
    assert ctx["decoded"]["officer_jurisdiction_state"] == state


@then(parsers.parse('the serial is "{serial}"'))
def check_serial(ctx: dict[str, Any], serial: str) -> None:
    assert ctx["decoded"]["serial"] == serial


@then(parsers.parse('its jurisdiction_iso is "{iso}"'))
def check_jurisdiction_iso(ctx: dict[str, Any], iso: str) -> None:
    assert ctx["ident"].jurisdiction_iso == iso


@then(parsers.parse('its scheme is "{scheme}"'))
def check_scheme(ctx: dict[str, Any], scheme: str) -> None:
    assert ctx["ident"].scheme == scheme


@then(
    "calling decode_offline() on the base RegulatoryIdentifier raises "
    "NotImplementedError"
)
def check_base_not_implemented() -> None:
    base = RegulatoryIdentifier(
        jurisdiction_iso="US", scheme="US_FDA_FEI", raw_value="3001234567"
    )
    with pytest.raises(NotImplementedError):
        base.decode_offline()


@then("a ValueError is raised")
def check_value_error(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["error"], ValueError)


@then(parsers.parse('the error message contains "{substr}"'))
def check_error_contains(ctx: dict[str, Any], substr: str) -> None:
    assert substr in str(ctx["error"])


@then(parsers.parse("the CLI exit code is {code:d}"))
def check_cli_exit_zero(ctx: dict[str, Any], code: int) -> None:
    assert ctx["cli_result"].exit_code == code


@then("the CLI exit code is non-zero")
def check_cli_exit_nonzero(ctx: dict[str, Any]) -> None:
    assert ctx["cli_result"].exit_code != 0


@then("the CLI stdout is valid JSON")
def check_cli_json(ctx: dict[str, Any]) -> None:
    ctx["cli_json"] = json.loads(ctx["cli_result"].stdout)


@then(parsers.parse('the JSON field "{field}" equals "{value}"'))
def check_json_str_field(ctx: dict[str, Any], field: str, value: str) -> None:
    assert ctx["cli_json"][field] == value


@then(parsers.parse('the JSON field "{field}" equals {value:d}'))
def check_json_int_field(ctx: dict[str, Any], field: str, value: int) -> None:
    assert ctx["cli_json"][field] == value


@then(parsers.parse('the JSON field "{field}" equals false'))
def check_json_false_field(ctx: dict[str, Any], field: str) -> None:
    assert ctx["cli_json"][field] is False


@then(parsers.parse('the CLI output contains "{substr}"'))
def check_cli_output_contains(ctx: dict[str, Any], substr: str) -> None:
    assert substr in ctx["cli_result"].output
