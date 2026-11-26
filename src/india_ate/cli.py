"""Click CLI entry point for india-ate."""

import json
from pathlib import Path
from typing import cast

import click

from india_ate.adapters.hygiene_rating import HygieneRatingAdapter
from india_ate.models import AuthoritativeEvent, FoodPremises, IngestionBatch
from india_ate.models.identifiers import IndiaFSSAI14
from india_ate.store import SQLiteStore
from india_ate.store.jsonl import EntityModel, export_jsonl

DEFAULT_DB_PATH = "data/india_ate.db"


def _decode_or_raise(fssai_number: str) -> dict[str, object]:
    try:
        return IndiaFSSAI14(raw_value=fssai_number).decode_offline()
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


def _persist_hygiene_batch(
    batch: IngestionBatch, db_path: str, jsonl_dir: Path | None
) -> None:
    with SQLiteStore(db_path) as store:
        store.initialize()
        store.save_ingestion_batch(batch)
    if jsonl_dir is not None:
        export_entities = cast(list[EntityModel], batch.entities)
        export_jsonl(export_entities, jsonl_dir / "hygiene_entities.jsonl")


def _format_ingest_summary(batch: IngestionBatch) -> str:
    summary = {
        "premises_ingested": sum(
            1 for entity in batch.entities if isinstance(entity, FoodPremises)
        ),
        "events_ingested": sum(
            1 for entity in batch.entities if isinstance(entity, AuthoritativeEvent)
        ),
        "quarantined": len(batch.quarantined),
    }
    return json.dumps(summary, indent=2)


def _fetch_fact_receipt(
    fssai_id: str, db_path: str, decoded: dict[str, object]
) -> dict[str, object]:
    with SQLiteStore(db_path) as store:
        store.initialize()
        premises = store.get_premises_by_fssai_id(fssai_id.strip())
        if premises is None:
            return {
                "decoded": decoded,
                "premises": None,
                "brand_listings": [],
                "events": [],
            }
        listings = store.get_brand_listings_for_premises(premises.entity_id)
        events = store.get_events_for_target(premises.entity_id)
    return {
        "decoded": decoded,
        "premises": premises.model_dump(mode="json"),
        "brand_listings": [item.model_dump(mode="json") for item in listings],
        "events": [item.model_dump(mode="json") for item in events],
    }


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
    _persist_hygiene_batch(batch, db_path, jsonl_dir)
    click.echo(_format_ingest_summary(batch))


@app.command("lookup")
@click.argument("fssai_id")
@click.option("--db", "db_path", type=str, default=DEFAULT_DB_PATH, show_default=True)
def lookup_command(fssai_id: str, db_path: str) -> None:
    """Print a Fact Receipt JSON for a 14-digit FSSAI ID."""
    decoded = _decode_or_raise(fssai_id)
    receipt = _fetch_fact_receipt(fssai_id, db_path, decoded)
    click.echo(json.dumps(receipt, indent=2))
