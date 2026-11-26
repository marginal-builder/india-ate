# india-ate Phase 1 Quality Report
Generated: 2026-11-26T08:25:28Z

## Acceptance Test Results

Command: `.venv/bin/pytest tests/acceptance/ -v --tb=long --no-cov`

```text
72 passed, 3 warnings in 0.50s
```

All 72 BDD scenarios across all 9 acceptance test modules (`features/entity_graph/`, `features/fssai_decoder/`, `features/store/`) passed:

- `tests/acceptance/test_authoritative_event.py`: 13 passed
- `tests/acceptance/test_decode_offline.py`: 14 passed
- `tests/acceptance/test_duckdb_analytics.py`: 3 passed
- `tests/acceptance/test_food_actors.py`: 10 passed
- `tests/acceptance/test_food_item.py`: 5 passed
- `tests/acceptance/test_jsonl_export.py`: 3 passed
- `tests/acceptance/test_scientific_standard.py`: 8 passed
- `tests/acceptance/test_sqlite_store.py`: 5 passed
- `tests/acceptance/test_substance.py`: 11 passed

## Full Test Suite & Coverage Report

Command: `.venv/bin/pytest -v --cov=india_ate --cov-fail-under=95 --cov-report=term-missing`

```text
================================ tests coverage ================================
_______________ coverage: platform darwin, python 3.15.2-final-0 _______________

Name                                  Stmts   Miss  Cover   Missing
-------------------------------------------------------------------
src/india_ate/__init__.py                 1      0   100%
src/india_ate/adapters/__init__.py       10      0   100%
src/india_ate/cli.py                     13      0   100%
src/india_ate/config.py                   7      0   100%
src/india_ate/models/__init__.py          8      0   100%
src/india_ate/models/actors.py           24      0   100%
src/india_ate/models/base.py             21      0   100%
src/india_ate/models/events.py            8      0   100%
src/india_ate/models/food_item.py        10      0   100%
src/india_ate/models/identifiers.py      42      0   100%
src/india_ate/models/standards.py         9      0   100%
src/india_ate/models/substance.py         8      0   100%
src/india_ate/store/__init__.py           4      0   100%
src/india_ate/store/_schema.py            4      0   100%
src/india_ate/store/duckdb.py            55      0   100%
src/india_ate/store/jsonl.py             28      0   100%
src/india_ate/store/sqlite.py            68      0   100%
-------------------------------------------------------------------
TOTAL                                   320      0   100%
Required test coverage of 95% reached. Total coverage: 100.00%
======================= 140 passed, 3 warnings in 0.61s ========================
```

- Total tests: **140 passed** (72 acceptance + 68 unit)
- Coverage: **100.00%** (320/320 statements, threshold ≥ 95%)

## Static Analysis, Formatting & Duplication

- **Ruff lint**: `.venv/bin/ruff check src/ tests/` → `All checks passed!`
- **Ruff format**: `.venv/bin/ruff format --check src/ tests/` → `40 files already formatted`
- **Mypy strict**: `.venv/bin/mypy src/` → `Success: no issues found in 17 source files`
- **Pylint duplicate-code**: `.venv/bin/pylint src/ --disable=all --enable=duplicate-code` → `Your code has been rated at 10.00/10` (0 duplicate-code findings)

## Mutation Score

Command: `.venv/bin/mutmut results --all true`

- Total mutants: **369**
- Killed: **346**
- Survived: **23**
- Mutation score: **93.77%** (346 / 369, threshold ≥ 80%)

All 23 surviving mutants are non-functional/equivalent variants in `store/` (`sqlite.py`, `jsonl.py`, `duckdb.py`).

## Complexity Report

Commands:
- `.venv/bin/radon cc src/ -a -nb`
- `.venv/bin/radon cc src/ --total-average -s`

```text
src/india_ate/models/identifiers.py
    F 95:0 _normalize_and_validate - B (6)

56 blocks (classes, functions, methods) analyzed.
Average complexity: A (1.8214285714285714)
```

- All 56 analyzed blocks are grade **A** (CC 1–5) except `_normalize_and_validate` at grade **B** (CC = 6 ≤ 10 threshold).
- CRAP max: `cc^2 * (1 - cov)^3 + cc` = `6^2 * (1 - 1.0)^3 + 6` = **6.0** (threshold ≤ 30).

## Security Verification

Commands:
- `grep -rnE "execute\([^)]*(f['\"]|\.format\(|%s|% )" src/india_ate/store/`
- `grep -rn "\.execute(" src/india_ate/store/`
- `grep -rnE "(API_KEY|SECRET_KEY|PASSWORD|TOKEN)\s*=" src/`

Results:
- Parameterized SQL execution in `src/india_ate/store/sqlite.py` (`self._conn.execute(sql, params)` / `(param,)`) and `src/india_ate/store/duckdb.py` (`con.execute(sql, [str(parquet_path)])`).
- The single DDL call `con.execute(f"CREATE TABLE export_tbl ({col_defs})")` in `src/india_ate/store/duckdb.py:100` builds `col_defs` exclusively from internal `_TABLE_SPECS` tuples validated by `_validate_columns` (`col_name.isidentifier()` and `col_type in _ALLOWED_TYPES`), and `_export_one_table` at line 115 uses the same internal `_TABLE_SPECS` identifiers. Zero user-controlled SQL interpolation paths exist.
- Hardcoded secrets check: `0 secret patterns found`.

## Architecture Compliance

Commands:
- `grep -rn "from india_ate.store" src/india_ate/models/` → empty (0 violations)
- `grep -rnE "from india_ate\.(store|adapters|cli|config)|import india_ate\.(store|adapters|cli|config)|import sqlite3|import duckdb|import click|import logfire|from sqlite3|from duckdb|from click|from logfire" src/india_ate/models/` → `0 violations found`

`models/` has zero imports from outer layers (`store/`, `adapters/`, `cli.py`, `config.py`) or infrastructure frameworks (`sqlite3`, `duckdb`, `click`, `logfire`).

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

Command 2: `.venv/bin/india-ate decode 11524033000123`

```json
{
  "tier": "license",
  "pre_inspection_exempt_post_apr2026": false,
  "authority_scope": "state_or_ut",
  "state_code": "15",
  "state_name": "Maharashtra",
  "registration_year": 2024,
  "officer_code": "033",
  "central_regional_office": null,
  "officer_jurisdiction_state": null,
  "serial": "000123"
}
```

Command 3: `.venv/bin/india-ate decode 22711126011608`

```json
{
  "tier": "basic_registration",
  "pre_inspection_exempt_post_apr2026": true,
  "authority_scope": "state_or_ut",
  "state_code": "27",
  "state_name": "Uttar Pradesh",
  "registration_year": 2011,
  "officer_code": "126",
  "central_regional_office": null,
  "officer_jurisdiction_state": null,
  "serial": "011608"
}
```

Command 4: `.venv/bin/india-ate decode 20007015000001`

```json
{
  "tier": "basic_registration",
  "pre_inspection_exempt_post_apr2026": true,
  "authority_scope": "central",
  "state_code": "00",
  "state_name": "Central",
  "registration_year": 2007,
  "officer_code": "015",
  "central_regional_office": null,
  "officer_jurisdiction_state": null,
  "serial": "000001"
}
```

## Sign-off

Phase 1 is COMPLETE. All quality gates passed.
