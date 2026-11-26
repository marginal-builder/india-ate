"""Unit tests for Click CLI."""

import json

from click.testing import CliRunner

from india_ate.cli import app


def test_cli_decode_valid_fssai() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["decode", "10013022000417"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["tier"] == "license"
    assert data["authority_scope"] == "central"
    assert data["state_code"] == "00"
    assert data["state_name"] == "Central"
    assert data["registration_year"] == 2013
    assert data["officer_code"] == "022"
    assert data["serial"] == "000417"
    assert data["pre_inspection_exempt_post_apr2026"] is False


def test_cli_decode_invalid_fssai() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["decode", "12345"])
    assert result.exit_code != 0
    assert "14-digit" in result.output
