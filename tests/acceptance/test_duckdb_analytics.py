"""Acceptance tests for duckdb_analytics.feature."""

from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from india_ate.models import (
    AuthoritativeEvent,
    BrandListing,
    EvidenceProvenance,
    FoodPremises,
)
from india_ate.store import (
    SQLiteStore,
    export_parquet_snapshots,
    query_enforcement_summary,
    query_ghost_brand_clusters_by_postal_code,
    write_parquet_table,
)

FEATURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "features"
    / "store"
    / "duckdb_analytics.feature"
)
scenarios(str(FEATURE_PATH))


@pytest.fixture
def ctx(tmp_path: Path, official_provenance: EvidenceProvenance) -> dict[str, Any]:
    return {
        "tmp_path": tmp_path,
        "db_path": tmp_path / "analytics.db",
        "snapshot_dir": tmp_path / "snapshots",
        "provenance": official_provenance,
    }


@given(
    "an initialized SQLite store populated with FoodPremises, BrandListing, "
    "and AuthoritativeEvent records"
)
def given_populated_sqlite(
    ctx: dict[str, Any],
    sample_premises: FoodPremises,
    sample_brand_listing: BrandListing,
    sample_event: AuthoritativeEvent,
) -> None:
    with SQLiteStore(ctx["db_path"]) as store:
        store.initialize()
        store.save_premises(sample_premises)
        store.save_brand_listing(sample_brand_listing)
        store.save_event(sample_event)


@given("Parquet snapshots containing:")
def given_parquet_from_table(ctx: dict[str, Any], datatable: list[list[str]]) -> None:
    rows = [
        (listing_id, display_name, "swiggy", premises_id, postal_code)
        for premises_id, postal_code, listing_id, display_name in datatable[1:]
    ]
    snap_dir: Path = ctx["snapshot_dir"]
    snap_dir.mkdir(parents=True, exist_ok=True)
    write_parquet_table(
        rows=rows,
        columns=[
            ("listing_id", "VARCHAR"),
            ("display_name", "VARCHAR"),
            ("platform", "VARCHAR"),
            ("premises_entity_id", "VARCHAR"),
            ("postal_code", "VARCHAR"),
        ],
        output_path=snap_dir / "brand_listings.parquet",
    )


@given(
    parsers.parse(
        'Parquet snapshots containing {raid_count:d} "{raid_type}" events with '
        'status "{raid_status}" and {audit_count:d} "{audit_type}" event with '
        'status "{audit_status}"'
    )
)
def given_event_parquet_snapshots(
    ctx: dict[str, Any],
    raid_count: int,
    raid_type: str,
    raid_status: str,
    audit_count: int,
    audit_type: str,
    audit_status: str,
) -> None:
    rows: list[tuple[str, str, str, str, str, str, str | None, str]] = []
    for idx in range(raid_count):
        rows.append(
            (
                f"evt:raid:{idx}",
                raid_type,
                "actor:in:fssai:23624001000123",
                "IN",
                "2026-04-01",
                raid_status,
                None,
                "Suspended",
            )
        )
    for idx in range(audit_count):
        rows.append(
            (
                f"evt:audit:{idx}",
                audit_type,
                "actor:in:fssai:10013022000417",
                "IN",
                "2026-04-01",
                audit_status,
                None,
                "Hygiene audit",
            )
        )
    snap_dir: Path = ctx["snapshot_dir"]
    snap_dir.mkdir(parents=True, exist_ok=True)
    write_parquet_table(
        rows=rows,
        columns=[
            ("event_id", "VARCHAR"),
            ("event_type", "VARCHAR"),
            ("target_entity_id", "VARCHAR"),
            ("jurisdiction_iso", "VARCHAR"),
            ("event_date", "VARCHAR"),
            ("status", "VARCHAR"),
            ("batch_or_lot_no", "VARCHAR"),
            ("verbatim_summary", "VARCHAR"),
        ],
        output_path=snap_dir / "authoritative_events.parquet",
    )


@when("I export Parquet snapshots to a snapshot directory using DuckDB")
def export_snapshots(ctx: dict[str, Any]) -> None:
    ctx["exported"] = export_parquet_snapshots(ctx["db_path"], ctx["snapshot_dir"])


@when("I run the DuckDB ghost-brand cluster analytics query grouped by postal_code")
def run_cluster_query(ctx: dict[str, Any]) -> None:
    rows = query_ghost_brand_clusters_by_postal_code(ctx["snapshot_dir"])
    ctx["clusters"] = {row["postal_code"]: row for row in rows}


@when(
    "I run the DuckDB enforcement summary query over the authoritative_events "
    "Parquet snapshot"
)
def run_enforcement_query(ctx: dict[str, Any]) -> None:
    rows = query_enforcement_summary(ctx["snapshot_dir"])
    ctx["enforcement_summary"] = {
        (row["event_type"], row["status"]): row["count"] for row in rows
    }


@then(
    "non-empty Parquet files are created for food_premises, brand_listings, and "
    "authoritative_events"
)
def check_parquet_files(ctx: dict[str, Any]) -> None:
    for key in ("food_premises", "brand_listings", "authoritative_events"):
        path: Path = ctx["exported"][key]
        assert path.exists()
        assert path.stat().st_size > 0


@then(
    parsers.parse(
        'postal_code "{postal_code}" reports {premises_cnt:d} premises_count '
        "and {listing_cnt:d} brand_listing_count"
    )
)
def check_postal_cluster_counts(
    ctx: dict[str, Any],
    postal_code: str,
    premises_cnt: int,
    listing_cnt: int,
) -> None:
    row = ctx["clusters"][postal_code]
    assert row["premises_count"] == premises_cnt
    assert row["brand_listing_count"] == listing_cnt


@then(parsers.parse('"{event_type}" with status "{status}" has count {count:d}'))
def check_enforcement_count(
    ctx: dict[str, Any], event_type: str, status: str, count: int
) -> None:
    assert ctx["enforcement_summary"][(event_type, status)] == count
