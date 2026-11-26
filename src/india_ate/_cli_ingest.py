"""Click CLI ingestion subcommands for india-ate."""

import json
from pathlib import Path
from typing import Protocol, cast

import click

from india_ate.adapters.foscos_recall import FoSCoSRecallAdapter
from india_ate.adapters.hygiene_rating import HygieneRatingAdapter
from india_ate.adapters.ifct_nutrition import IFCTNutritionAdapter
from india_ate.adapters.ondc_catalog import ONDCCatalogAdapter
from india_ate.adapters.state_enforcement import StateEnforcementAdapter
from india_ate.models import AuthoritativeEvent, FoodPremises, IngestionBatch
from india_ate.store import SQLiteStore
from india_ate.store.jsonl import EntityModel, export_jsonl


class _BatchAdapter(Protocol):
    def fetch(self) -> bytes: ...
    def parse(self, raw: bytes) -> list[dict[str, object]]: ...
    def validate_and_emit_batch(
        self, records: list[dict[str, object]]
    ) -> IngestionBatch: ...


def persist_batch(
    batch: IngestionBatch, db_path: str, jsonl_dir: Path | None, filename: str
) -> None:
    """Persist an IngestionBatch to SQLite and optionally export JSONL."""
    with SQLiteStore(db_path) as store:
        store.initialize()
        store.save_ingestion_batch(batch)
    if jsonl_dir is not None:
        export_entities = cast(list[EntityModel], batch.entities)
        export_jsonl(export_entities, jsonl_dir / filename)


def format_ingest_summary(batch: IngestionBatch) -> str:
    """Format a deterministic JSON ingestion summary."""
    summary = {
        "premises_ingested": sum(
            1 for e in batch.entities if isinstance(e, FoodPremises)
        ),
        "events_ingested": sum(
            1 for e in batch.entities if isinstance(e, AuthoritativeEvent)
        ),
        "entities_ingested": len(batch.entities),
        "quarantined": len(batch.quarantined),
    }
    return json.dumps(summary, indent=2)


def run_adapter_ingest(
    adapter: _BatchAdapter,
    from_file: Path | None,
    db_path: str,
    jsonl_dir: Path | None,
    jsonl_name: str,
) -> None:
    """Execute fetch/parse/validate_and_emit_batch/persist for any batch adapter."""
    raw = from_file.read_bytes() if from_file is not None else adapter.fetch()
    batch = adapter.validate_and_emit_batch(adapter.parse(raw))
    persist_batch(batch, db_path, jsonl_dir, jsonl_name)
    click.echo(format_ingest_summary(batch))


def _file_opt() -> click.Path:
    return click.Path(exists=True, dir_okay=False, path_type=Path)


def _jsonl_opt() -> click.Path:
    return click.Path(file_okay=False, path_type=Path)


def _reg_hygiene(ingest_group: click.Group, default_db: str) -> None:
    @ingest_group.command("hygiene")
    @click.option("--from-file", "from_file", type=_file_opt(), default=None)
    @click.option("--state", "state_code", type=str, default=None)
    @click.option("--db", "db_path", type=str, default=default_db, show_default=True)
    @click.option("--jsonl-dir", "jsonl_dir", type=_jsonl_opt(), default=None)
    def ingest_hygiene_command(
        from_file: Path | None,
        state_code: str | None,
        db_path: str,
        jsonl_dir: Path | None,
    ) -> None:
        """Ingest FSSAI Hygiene Rating records."""
        adapter = HygieneRatingAdapter(state_code=state_code)
        run_adapter_ingest(
            cast(_BatchAdapter, adapter),
            from_file,
            db_path,
            jsonl_dir,
            "hygiene_entities.jsonl",
        )


def _reg_recall(ingest_group: click.Group, default_db: str) -> None:
    @ingest_group.command("recall")
    @click.option("--from-file", "from_file", type=_file_opt(), default=None)
    @click.option("--db", "db_path", type=str, default=default_db, show_default=True)
    @click.option("--jsonl-dir", "jsonl_dir", type=_jsonl_opt(), default=None)
    def ingest_recall_command(
        from_file: Path | None, db_path: str, jsonl_dir: Path | None
    ) -> None:
        """Ingest FoSCoS Food Recall Portal records."""
        run_adapter_ingest(
            cast(_BatchAdapter, FoSCoSRecallAdapter()),
            from_file,
            db_path,
            jsonl_dir,
            "recall_entities.jsonl",
        )


def _reg_enforcement(ingest_group: click.Group, default_db: str) -> None:
    @ingest_group.command("enforcement")
    @click.option("--source-name", type=str, default="Telangana TG SAFE")
    @click.option("--from-file", "from_file", type=_file_opt(), default=None)
    @click.option("--db", "db_path", type=str, default=default_db, show_default=True)
    @click.option("--jsonl-dir", "jsonl_dir", type=_jsonl_opt(), default=None)
    def ingest_enforcement_command(
        source_name: str,
        from_file: Path | None,
        db_path: str,
        jsonl_dir: Path | None,
    ) -> None:
        """Ingest state enforcement raid & suspension feeds."""
        adapter = StateEnforcementAdapter(source_name=source_name)
        run_adapter_ingest(
            cast(_BatchAdapter, adapter),
            from_file,
            db_path,
            jsonl_dir,
            "enforcement_entities.jsonl",
        )


def _reg_ondc(ingest_group: click.Group, default_db: str) -> None:
    @ingest_group.command("ondc")
    @click.option("--from-file", "from_file", type=_file_opt(), default=None)
    @click.option("--db", "db_path", type=str, default=default_db, show_default=True)
    @click.option("--jsonl-dir", "jsonl_dir", type=_jsonl_opt(), default=None)
    def ingest_ondc_command(
        from_file: Path | None, db_path: str, jsonl_dir: Path | None
    ) -> None:
        """Ingest ONDC Open F&B Catalog BrandListing -> FoodPremises mappings."""
        run_adapter_ingest(
            cast(_BatchAdapter, ONDCCatalogAdapter()),
            from_file,
            db_path,
            jsonl_dir,
            "ondc_entities.jsonl",
        )


def _reg_ifct(ingest_group: click.Group, default_db: str) -> None:
    @ingest_group.command("ifct")
    @click.option("--from-file", "from_file", type=_file_opt(), required=True)
    @click.option("--db", "db_path", type=str, default=default_db, show_default=True)
    @click.option("--jsonl-dir", "jsonl_dir", type=_jsonl_opt(), default=None)
    def ingest_ifct_command(
        from_file: Path, db_path: str, jsonl_dir: Path | None
    ) -> None:
        """Ingest ICMR-NIN IFCT 2017 CSV nutrition compositions."""
        adapter = IFCTNutritionAdapter(csv_path=from_file)
        run_adapter_ingest(
            cast(_BatchAdapter, adapter),
            from_file,
            db_path,
            jsonl_dir,
            "ifct_entities.jsonl",
        )


def register_ingest_commands(ingest_group: click.Group, default_db: str) -> None:
    """Attach all ingestion subcommands to the Click ingest group."""
    _reg_hygiene(ingest_group, default_db)
    _reg_recall(ingest_group, default_db)
    _reg_enforcement(ingest_group, default_db)
    _reg_ondc(ingest_group, default_db)
    _reg_ifct(ingest_group, default_db)
