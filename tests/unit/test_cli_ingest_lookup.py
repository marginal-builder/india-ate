"""Unit tests for india-ate CLI ingest hygiene and lookup commands."""

import json
from datetime import UTC, datetime
from pathlib import Path

from click.testing import CliRunner
from pydantic import HttpUrl

from india_ate.adapters.hygiene_rating import HygieneRatingAdapter
from india_ate.cli import app
from india_ate.models import BrandListing, EvidenceProvenance
from india_ate.store import SQLiteStore

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
    assert '\n  "premises_ingested": 1,' in ingest_res.output
    summary = json.loads(ingest_res.output)
    assert summary["premises_ingested"] == 1
    assert summary["events_ingested"] == 1
    assert summary["quarantined"] == 1
    assert any(p.name == "hygiene_entities.jsonl" for p in jsonl_dir.iterdir())

    # Add a BrandListing to verify lookup includes serialized brand_listings
    with SQLiteStore(db_path) as store:
        store.save_brand_listing(
            BrandListing(
                listing_id="lst:swiggy:1",
                display_name="Acme Ghost Kitchen",
                platform="swiggy",
                premises_entity_id="actor:in:fssai:10013022000417",
                postal_code="400001",
                first_seen_at=datetime(2026, 2, 14, tzinfo=UTC),
                last_seen_at=datetime(2026, 2, 14, tzinfo=UTC),
                provenance=EvidenceProvenance(
                    source_name="Swiggy",
                    source_url=HttpUrl("https://swiggy.com"),
                    retrieved_at=datetime(2026, 2, 14, tzinfo=UTC),
                    content_sha256="a" * 64,
                    verification_tier="user_verified_snapshot",
                ),
            )
        )

    lookup_res = runner.invoke(app, ["lookup", "10013022000417", "--db", str(db_path)])
    assert lookup_res.exit_code == 0, lookup_res.output
    receipt = json.loads(lookup_res.output)
    assert receipt["decoded"]["state_name"] == "Central"
    assert receipt["premises"]["entity_id"] == "actor:in:fssai:10013022000417"
    assert len(receipt["brand_listings"]) == 1
    assert receipt["brand_listings"][0]["display_name"] == "Acme Ghost Kitchen"
    assert len(receipt["events"]) == 1
    assert receipt["events"][0]["event_type"] == "hygiene_audit"


def test_cli_lookup_missing_premises_and_invalid_fssai(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "empty.db"
    not_found = runner.invoke(app, ["lookup", "10013022000417", "--db", str(db_path)])
    assert not_found.exit_code == 0, not_found.output
    receipt = json.loads(not_found.output)
    assert receipt["decoded"]["state_name"] == "Central"
    assert receipt["premises"] is None
    assert receipt["brand_listings"] == []
    assert receipt["events"] == []

    res = runner.invoke(app, ["lookup", "bad-id", "--db", str(tmp_path / "missing.db")])
    assert res.exit_code != 0


def test_cli_ingest_hygiene_live_fetch_and_no_jsonl(
    tmp_path: Path, monkeypatch: object
) -> None:
    runner = CliRunner()
    db_path = tmp_path / "live.db"
    raw = (FIXTURES_DIR / "hygiene_sample.json").read_bytes()
    monkeypatch.setattr(HygieneRatingAdapter, "fetch", lambda self: raw)  # type: ignore[attr-defined]

    res = runner.invoke(
        app, ["ingest", "hygiene", "--state", "27", "--db", str(db_path)]
    )
    assert res.exit_code == 0, res.output
    summary = json.loads(res.output)
    assert summary["premises_ingested"] == 1
    assert summary["events_ingested"] == 1
    assert summary["quarantined"] == 0
