"""DuckDB analytical queries and Parquet snapshot export."""

import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import duckdb

_ALLOWED_TYPES = frozenset({"VARCHAR", "DOUBLE"})

_PREMISES_COLUMNS: tuple[tuple[str, str], ...] = (
    ("entity_id", "VARCHAR"),
    ("legal_name", "VARCHAR"),
    ("jurisdiction_iso", "VARCHAR"),
    ("premises_type", "VARCHAR"),
    ("address", "VARCHAR"),
    ("postal_code", "VARCHAR"),
    ("city", "VARCHAR"),
    ("state", "VARCHAR"),
    ("lat", "DOUBLE"),
    ("lon", "DOUBLE"),
    ("fssai_id", "VARCHAR"),
)

_LISTING_COLUMNS: tuple[tuple[str, str], ...] = (
    ("listing_id", "VARCHAR"),
    ("display_name", "VARCHAR"),
    ("platform", "VARCHAR"),
    ("premises_entity_id", "VARCHAR"),
    ("postal_code", "VARCHAR"),
    ("first_seen_at", "VARCHAR"),
    ("last_seen_at", "VARCHAR"),
)

_EVENT_COLUMNS: tuple[tuple[str, str], ...] = (
    ("event_id", "VARCHAR"),
    ("event_type", "VARCHAR"),
    ("target_entity_id", "VARCHAR"),
    ("jurisdiction_iso", "VARCHAR"),
    ("event_date", "VARCHAR"),
    ("status", "VARCHAR"),
    ("batch_or_lot_no", "VARCHAR"),
    ("verbatim_summary", "VARCHAR"),
)


def _validate_columns(columns: Sequence[tuple[str, str]]) -> None:
    for col_name, col_type in columns:
        if not col_name.isidentifier() or col_type not in _ALLOWED_TYPES:
            raise ValueError(f"Invalid column definition: {(col_name, col_type)!r}")


def write_parquet_table(
    rows: Sequence[Sequence[object]],
    columns: Sequence[tuple[str, str]],
    output_path: Path,
) -> Path:
    """Write rows with an explicit schema to a Parquet file via DuckDB."""
    _validate_columns(columns)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    col_defs = ", ".join(f"{name} {dtype}" for name, dtype in columns)
    placeholders = ", ".join("?" for _ in columns)
    con = duckdb.connect(":memory:")
    try:
        con.execute(f"CREATE TABLE export_tbl ({col_defs})")
        if rows:
            con.executemany(
                f"INSERT INTO export_tbl VALUES ({placeholders})",  # noqa: S608
                rows,
            )
        con.table("export_tbl").write_parquet(str(output_path))
    finally:
        con.close()
    return output_path


def export_parquet_snapshots(
    sqlite_db_path: Path,
    snapshot_dir: Path,
) -> dict[str, Path]:
    """Export food_premises, brand_listings, and authoritative_events to Parquet."""
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    table_specs: list[tuple[str, tuple[tuple[str, str], ...]]] = [
        ("food_premises", _PREMISES_COLUMNS),
        ("brand_listings", _LISTING_COLUMNS),
        ("authoritative_events", _EVENT_COLUMNS),
    ]
    outputs: dict[str, Path] = {}
    sqlite_conn = sqlite3.connect(str(sqlite_db_path))
    try:
        for table_name, columns in table_specs:
            col_names = ", ".join(name for name, _ in columns)
            rows = sqlite_conn.execute(
                f"SELECT {col_names} FROM {table_name}"  # noqa: S608
            ).fetchall()
            outputs[table_name] = write_parquet_table(
                rows=rows,
                columns=columns,
                output_path=snapshot_dir / f"{table_name}.parquet",
            )
    finally:
        sqlite_conn.close()
    return outputs


def query_ghost_brand_clusters_by_postal_code(
    snapshot_dir: Path,
) -> list[dict[str, Any]]:
    """Aggregate premises_count and brand_listing_count grouped by postal_code."""
    parquet_path = str(snapshot_dir / "brand_listings.parquet")
    con = duckdb.connect(":memory:")
    try:
        rows = con.execute(
            "SELECT postal_code, "
            "COUNT(DISTINCT premises_entity_id) AS premises_count, "
            "COUNT(*) AS brand_listing_count "
            "FROM read_parquet(?) "
            "GROUP BY postal_code "
            "ORDER BY postal_code",
            [parquet_path],
        ).fetchall()
    finally:
        con.close()
    return [
        {
            "postal_code": row[0],
            "premises_count": row[1],
            "brand_listing_count": row[2],
        }
        for row in rows
    ]


def query_enforcement_summary(snapshot_dir: Path) -> list[dict[str, Any]]:
    """Aggregate authoritative event counts by event_type and status."""
    parquet_path = str(snapshot_dir / "authoritative_events.parquet")
    con = duckdb.connect(":memory:")
    try:
        rows = con.execute(
            "SELECT event_type, status, COUNT(*) AS count "
            "FROM read_parquet(?) "
            "GROUP BY event_type, status "
            "ORDER BY event_type, status",
            [parquet_path],
        ).fetchall()
    finally:
        con.close()
    return [{"event_type": row[0], "status": row[1], "count": row[2]} for row in rows]
