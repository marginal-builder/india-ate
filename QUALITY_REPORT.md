# india-ate Phase 2 Quality Report
Generated: 2026-11-26T08:56:10.670430+00:00

## Acceptance Test Results

Command: `.venv/bin/pytest tests/acceptance/ -v --tb=long --no-cov`

```text
85 passed, 3 warnings in 0.73s
```

All 85 BDD scenarios across all 10 acceptance test modules (`features/entity_graph/`, `features/fssai_decoder/`, `features/ingestion/`, `features/store/`) passed:

- `tests/acceptance/test_authoritative_event.py`: 13 passed
- `tests/acceptance/test_decode_offline.py`: 14 passed
- `tests/acceptance/test_duckdb_analytics.py`: 3 passed
- `tests/acceptance/test_food_actors.py`: 10 passed
- `tests/acceptance/test_food_item.py`: 5 passed
- `tests/acceptance/test_hygiene_rating.py`: 13 passed
- `tests/acceptance/test_jsonl_export.py`: 3 passed
- `tests/acceptance/test_scientific_standard.py`: 8 passed
- `tests/acceptance/test_sqlite_store.py`: 5 passed
- `tests/acceptance/test_substance.py`: 11 passed

## Full Test Suite & Coverage Report

Command: `.venv/bin/pytest -v --cov=india_ate --cov-fail-under=95 --cov-report=term-missing`

```text
================================ tests coverage ================================
_______________ coverage: platform darwin, python 3.15.2-final-0 _______________

Name                                        Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------
src/india_ate/__init__.py                       1      0   100%
src/india_ate/adapters/__init__.py             10      0   100%
src/india_ate/adapters/_hygiene_parser.py      72      1    99%   37
src/india_ate/adapters/http.py                 25      0   100%
src/india_ate/adapters/hygiene_rating.py       53      0   100%
src/india_ate/cli.py                           60      0   100%
src/india_ate/config.py                         7      0   100%
src/india_ate/models/__init__.py                9      0   100%
src/india_ate/models/actors.py                 24      0   100%
src/india_ate/models/base.py                   21      0   100%
src/india_ate/models/events.py                  8      0   100%
src/india_ate/models/food_item.py              10      0   100%
src/india_ate/models/identifiers.py            42      0   100%
src/india_ate/models/ingestion.py               8      0   100%
src/india_ate/models/standards.py               9      0   100%
src/india_ate/models/substance.py               8      0   100%
src/india_ate/store/__init__.py                 4      0   100%
src/india_ate/store/_params.py                 15      0   100%
src/india_ate/store/_schema.py                  5      0   100%
src/india_ate/store/duckdb.py                  55      0   100%
src/india_ate/store/jsonl.py                   28      0   100%
src/india_ate/store/sqlite.py                  75      0   100%
-------------------------------------------------------------------------
TOTAL                                         549      1    99%
Required test coverage of 95% reached. Total coverage: 99.82%
======================= 168 passed, 4 warnings in 0.93s ========================
```

- Total tests: **168 passed** (85 acceptance + 83 unit)
- Coverage: **99.82%** (548/549 statements, threshold ≥ 95%)

## Static Analysis, Formatting & Duplication

- **Ruff lint**: `.venv/bin/ruff check src/ tests/` → `All checks passed!`
- **Ruff format**: `.venv/bin/ruff format --check src/ tests/` → `51 files already formatted`
- **Mypy strict**: `.venv/bin/mypy src/` → `Success: no issues found in 22 source files`
- **Pylint duplicate-code**: `.venv/bin/pylint src/ --disable=all --enable=duplicate-code` → `Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)`

## Mutation Score

Command: `.venv/bin/mutmut results --all true`

- Total mutants: **769**
- Killed: **728**
- Survived: **37**
- Suspicious: **4**
- Mutation score: **94.67%** (728 / 769, threshold ≥ 80%)

## Complexity Report

Commands:
- `.venv/bin/radon cc src/ -a -nb`
- `.venv/bin/radon cc src/ --total-average -s`

```text
src/india_ate/models/identifiers.py
    F 95:0 _normalize_and_validate - B (6)

99 blocks (classes, functions, methods) analyzed.
Average complexity: A (1.9090909090909092)
```

- All 99 analyzed blocks are grade **A** (CC 1–5) except `_normalize_and_validate` at grade **B** (CC = 6 ≤ 10 threshold).
- CRAP max: `cc^2 * (1 - cov)^3 + cc` = `6^2 * (1 - 1.0)^3 + 6` = **6.0** (threshold ≤ 30).

## Security Verification

Commands:
- `grep -rnE "execute\([^)]*(f['\"]|\.format\(|%s|% )" src/india_ate/store/`
- `grep -rn "\.execute(" src/india_ate/store/`
- `grep -rnE "(API_KEY|SECRET_KEY|PASSWORD|TOKEN)\s*=" src/`

Results:
- Parameterized SQL execution in `src/india_ate/store/sqlite.py` (`self._conn.execute(sql, params)` / `(param,)`, including `INSERT_PREMISES_SQL`, `INSERT_EVENT_SQL`, `INSERT_QUARANTINED_SQL`) and `src/india_ate/store/duckdb.py` (`con.execute(sql, [str(parquet_path)])`).
- The single DDL call `con.execute(f"CREATE TABLE export_tbl ({col_defs})")` in `src/india_ate/store/duckdb.py:100` builds `col_defs` exclusively from internal `_TABLE_SPECS` tuples validated by `_validate_columns` (`col_name.isidentifier()` and `col_type in _ALLOWED_TYPES`), and `_export_one_table` at line 115 uses the same internal `_TABLE_SPECS` identifiers. Zero user-controlled SQL interpolation paths exist.
- Hardcoded secrets check: `0 secret patterns`.

## Architecture Compliance

Commands:
- `grep -rn "from india_ate.store" src/india_ate/models/` → `0 violations`
- `grep -rnE "from india_ate\.(store|adapters|cli|config)|import india_ate\.(store|adapters|cli|config)|import sqlite3|import duckdb|import click|import logfire|import httpx|import bs4|from sqlite3|from duckdb|from click|from logfire|from httpx|from bs4" src/india_ate/models/` → `0 outer-layer violations`

`models/` has zero imports from outer layers (`store/`, `adapters/`, `cli.py`, `config.py`) or infrastructure frameworks (`sqlite3`, `duckdb`, `click`, `logfire`, `httpx`, `bs4`).

## CLI Smoke Test

Command 1: `.venv/bin/india-ate decode 10013022000417`

```json
{
  "tier": "license",
  "pre_inspection_exempt_post_apr2026": false,
  "authority_scope": "central",
  "state_code": "00",
  "state_name": "Central",
  "registration_year": 2013,
  "officer_code": "022",
  "central_regional_office": "RO Mumbai",
  "officer_jurisdiction_state": "Maharashtra",
  "serial": "000417"
}
```

Command 2: `.venv/bin/india-ate ingest hygiene --from-file tests/fixtures/hygiene_sample.html --db /tmp/india_ate_qa.db`

```json
{
  "premises_ingested": 1,
  "events_ingested": 1,
  "quarantined": 1
}
```

Command 3: `.venv/bin/india-ate lookup 10013022000417 --db /tmp/india_ate_qa.db`

```json
{
  "decoded": {
    "tier": "license",
    "pre_inspection_exempt_post_apr2026": false,
    "authority_scope": "central",
    "state_code": "00",
    "state_name": "Central",
    "registration_year": 2013,
    "officer_code": "022",
    "central_regional_office": "RO Mumbai",
    "officer_jurisdiction_state": "Maharashtra",
    "serial": "000417"
  },
  "premises": {
    "entity_id": "actor:in:fssai:10013022000417",
    "legal_name": "Acme Foods Pvt Ltd",
    "jurisdiction_iso": "IN",
    "regulatory_ids": [
      {
        "jurisdiction_iso": "IN",
        "scheme": "IN_FSSAI_14",
        "raw_value": "10013022000417"
      }
    ],
    "provenance": [
      {
        "source_name": "FSSAI Hygiene Rating Portal",
        "source_url": "https://hygiene.fssai.gov.in/snapshot",
        "retrieved_at": "2026-11-26T08:56:05.362847Z",
        "content_sha256": "ae86b19fe58f50d5991b13d57d3180f975ef23365fea3c5ded21d257836527c1",
        "verification_tier": "official_registry"
      }
    ],
    "premises_type": "restaurant",
    "address": "12 MG Road",
    "postal_code": "400001",
    "city": "Mumbai",
    "state": "Maharashtra",
    "lat": null,
    "lon": null
  },
  "brand_listings": [],
  "events": [
    {
      "event_id": "evt:hygiene:10013022000417:2026-02-14",
      "event_type": "hygiene_audit",
      "target_entity_id": "actor:in:fssai:10013022000417",
      "jurisdiction_iso": "IN",
      "event_date": "2026-02-14",
      "status": "5/5",
      "batch_or_lot_no": null,
      "verbatim_summary": "FSSAI Hygiene Rating 5/5 audited on 2026-02-14",
      "provenance": {
        "source_name": "FSSAI Hygiene Rating Portal",
        "source_url": "https://hygiene.fssai.gov.in/snapshot",
        "retrieved_at": "2026-11-26T08:56:05.362847Z",
        "content_sha256": "ae86b19fe58f50d5991b13d57d3180f975ef23365fea3c5ded21d257836527c1",
        "verification_tier": "official_registry"
      }
    }
  ]
}
```

## Sign-off

Phase 2 is COMPLETE. All quality gates passed.
