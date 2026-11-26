"""Click CLI entry point for india-ate."""

import json
from datetime import date
from typing import cast

import click

from india_ate._cli_ingest import register_ingest_commands
from india_ate.api.server import create_http_server
from india_ate.mcp.server import serve_mcp_stdio
from india_ate.models.identifiers import IndiaFSSAI14
from india_ate.services import (
    GrievanceCategory,
    build_fact_receipt,
    find_verified_nearby_switches,
    generate_grievance_packet,
)
from india_ate.store import SQLiteStore

DEFAULT_DB_PATH = "data/india_ate.db"


def _decode_or_raise(fssai_number: str) -> dict[str, object]:
    try:
        return IndiaFSSAI14(raw_value=fssai_number).decode_offline()
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@click.group()
def app() -> None:
    """India's canonical Food & Nutrition Premises Entity Graph CLI."""


@app.command("decode")
@click.argument("fssai_number")
def decode_command(fssai_number: str) -> None:
    """Decode a 14-digit FSSAI license or registration number offline."""
    click.echo(json.dumps(_decode_or_raise(fssai_number), indent=2))


@app.group("ingest")
def ingest_group() -> None:
    """Ingest authoritative public food safety datasets."""


register_ingest_commands(ingest_group, DEFAULT_DB_PATH)


@app.command("lookup")
@click.argument("fssai_id")
@click.option("--db", "db_path", type=str, default=DEFAULT_DB_PATH, show_default=True)
def lookup_command(fssai_id: str, db_path: str) -> None:
    """Print an objective Fact Receipt JSON for a 14-digit FSSAI ID."""
    _decode_or_raise(fssai_id)
    with SQLiteStore(db_path) as store:
        store.initialize()
        receipt = build_fact_receipt(store, fssai_id)
    click.echo(json.dumps(receipt.model_dump(mode="json"), indent=2))


@app.command("nearby")
@click.argument("postal_code")
@click.option("--db", "db_path", type=str, default=DEFAULT_DB_PATH, show_default=True)
def nearby_command(postal_code: str, db_path: str) -> None:
    """List verified nearby switch options in a postal code."""
    with SQLiteStore(db_path) as store:
        store.initialize()
        options = [
            opt.model_dump(mode="json")
            for opt in find_verified_nearby_switches(store, postal_code)
        ]
    click.echo(json.dumps({"postal_code": postal_code, "options": options}, indent=2))


def _run_grievance(
    fssai_id: str,
    issue_category: str,
    description: str,
    incident_date: str,
    order_ref: str | None,
    persist: bool,
    db_path: str,
) -> dict[str, object]:
    _decode_or_raise(fssai_id)
    try:
        parsed_date = date.fromisoformat(incident_date)
        with SQLiteStore(db_path) as store:
            store.initialize()
            packet = generate_grievance_packet(
                store=store,
                fssai_id=fssai_id,
                issue_category=cast(GrievanceCategory, issue_category),
                order_reference=order_ref,
                description=description,
                incident_date=parsed_date,
                persist=persist,
            )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    return packet.model_dump(mode="json")


@app.command("grievance")
@click.argument("fssai_id")
@click.option("--category", "issue_category", type=str, required=True)
@click.option("--description", type=str, required=True)
@click.option("--incident-date", type=str, required=True)
@click.option("--order-ref", type=str, default=None)
@click.option("--persist/--no-persist", default=False)
@click.option("--db", "db_path", type=str, default=DEFAULT_DB_PATH, show_default=True)
def grievance_command(
    fssai_id: str,
    issue_category: str,
    description: str,
    incident_date: str,
    order_ref: str | None,
    persist: bool,
    db_path: str,
) -> None:
    """Generate a Food Safety Connect grievance packet."""
    payload = _run_grievance(
        fssai_id,
        issue_category,
        description,
        incident_date,
        order_ref,
        persist,
        db_path,
    )
    click.echo(json.dumps(payload, indent=2))


@app.command("serve")
@click.option("--host", type=str, default="127.0.0.1", show_default=True)
@click.option("--port", type=int, default=8000, show_default=True)
@click.option("--db", "db_path", type=str, default=DEFAULT_DB_PATH, show_default=True)
@click.option(
    "--allow-grievance-persist/--no-allow-grievance-persist",
    default=False,
    show_default=True,
    help="Allow unauthenticated HTTP grievance writes (local demos only).",
)
def serve_command(
    host: str, port: int, db_path: str, allow_grievance_persist: bool
) -> None:
    """Start the public REST API HTTP server."""
    server = create_http_server(
        db_path,
        host=host,
        port=port,
        allow_grievance_persist=allow_grievance_persist,
    )
    click.echo(f"Serving india-ate API on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


@app.command("mcp")
@click.option("--db", "db_path", type=str, default=DEFAULT_DB_PATH, show_default=True)
def mcp_command(db_path: str) -> None:
    """Run the JSON-RPC 2.0 MCP server over stdio."""
    serve_mcp_stdio(db_path)
