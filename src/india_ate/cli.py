"""Click CLI entry point for india-ate."""

import json
from pathlib import Path
from typing import cast

import click

from india_ate.adapters.hygiene_rating import HygieneRatingAdapter
from india_ate.models import AuthoritativeEvent, FoodPremises
from india_ate.models.identifiers import IndiaFSSAI14
from india_ate.store import SQLiteStore
from india_ate.store.jsonl import EntityModel, export_jsonl

DEFAULT_DB_PATH = "data/india_ate.db"


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


@app.group("ingest")
def ingest_group() -> None:
    """Ingest authoritative public food safety datasets."""


@ingest_group.command("hygiene")
@click.option(
    "--from-file",
    "from_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Local HTML or JSON snapshot file to ingest offline.",
)
@click.option("--state", "state_code", type=str, default=None, help="FSSAI state code.")
@click.option("--db", "db_path", type=str, default=DEFAULT_DB_PATH, show_default=True)
@click.option(
    "--jsonl-dir",
    "jsonl_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
)
def ingest_hygiene_command(
    from_file: Path | None,
    state_code: str | None,
    db_path: str,
    jsonl_dir: Path | None,
) -> None:
    """Ingest FSSAI Hygiene Rating records from a local snapshot or live portal."""
    adapter = HygieneRatingAdapter(state_code=state_code)
    raw = from_file.read_bytes() if from_file is not None else adapter.fetch()
    batch = adapter.validate_and_emit_batch(adapter.parse(raw))
    with SQLiteStore(db_path) as store:
        store.initialize()
        store.save_ingestion_batch(batch)
    if jsonl_dir is not None:
        export_entities = cast(list[EntityModel], batch.entities)
        export_jsonl(export_entities, jsonl_dir / "hygiene_entities.jsonl")
    summary = {
        "premises_ingested": sum(
            1 for entity in batch.entities if isinstance(entity, FoodPremises)
        ),
        "events_ingested": sum(
            1 for entity in batch.entities if isinstance(entity, AuthoritativeEvent)
        ),
        "quarantined": len(batch.quarantined),
    }
    click.echo(json.dumps(summary, indent=2))


@app.command("lookup")
@click.argument("fssai_id")
@click.option("--db", "db_path", type=str, default=DEFAULT_DB_PATH, show_default=True)
def lookup_command(fssai_id: str, db_path: str) -> None:
    """Print a Fact Receipt JSON for a 14-digit FSSAI ID."""
    try:
        decoded = IndiaFSSAI14(raw_value=fssai_id).decode_offline()
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    with SQLiteStore(db_path) as store:
        store.initialize()
        premises = store.get_premises_by_fssai_id(fssai_id.strip())
        listings = (
            store.get_brand_listings_for_premises(premises.entity_id)
            if premises is not None
            else []
        )
        events = (
            store.get_events_for_target(premises.entity_id)
            if premises is not None
            else []
        )
    receipt = {
        "decoded": decoded,
        "premises": premises.model_dump(mode="json") if premises is not None else None,
        "brand_listings": [item.model_dump(mode="json") for item in listings],
        "events": [item.model_dump(mode="json") for item in events],
    }
    click.echo(json.dumps(receipt, indent=2))
