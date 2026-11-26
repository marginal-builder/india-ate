"""Unit tests for india-ate CLI ingest hygiene and lookup commands."""

import json
from pathlib import Path

from click.testing import CliRunner

from india_ate.cli import app

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_cli_ingest_hygiene_from_file_and_lookup(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "india_ate.db"
    jsonl_dir = tmp_path / "jsonl"
    snapshot = FIXTURES_DIR / "hygiene_sample.html"

    ingest_res = runner.invoke(
        app,
        [
            "ingest",
            "hygiene",
            "--from-file",
            str(snapshot),
            "--db",
            str(db_path),
            "--jsonl-dir",
            str(jsonl_dir),
        ],
    )
    assert ingest_res.exit_code == 0, ingest_res.output
    summary = json.loads(ingest_res.output)
    assert summary["premises_ingested"] == 1
    assert summary["events_ingested"] == 1
    assert summary["quarantined"] == 1
    assert (jsonl_dir / "hygiene_entities.jsonl").exists()

    lookup_res = runner.invoke(app, ["lookup", "10013022000417", "--db", str(db_path)])
    assert lookup_res.exit_code == 0, lookup_res.output
    receipt = json.loads(lookup_res.output)
    assert receipt["decoded"]["state_name"] == "Central"
    assert receipt["premises"]["entity_id"] == "actor:in:fssai:10013022000417"
    assert len(receipt["events"]) == 1
    assert receipt["events"][0]["event_type"] == "hygiene_audit"


def test_cli_lookup_invalid_fssai_fails(tmp_path: Path) -> None:
    runner = CliRunner()
    res = runner.invoke(app, ["lookup", "bad-id", "--db", str(tmp_path / "missing.db")])
    assert res.exit_code != 0
