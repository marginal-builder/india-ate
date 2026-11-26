"""Click CLI entry point for india-ate."""

import json

import click

from india_ate.models.identifiers import IndiaFSSAI14


@click.group()
def app() -> None:
    """India's canonical Food & Nutrition Premises Entity Graph CLI."""


@app.command("decode")
@click.argument("fssai_number")
def decode_command(fssai_number: str) -> None:
    """Decode a 14-digit FSSAI license or registration number offline."""
    try:
        decoded = IndiaFSSAI14(raw_value=fssai_number).decode_offline()
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(decoded, indent=2))
