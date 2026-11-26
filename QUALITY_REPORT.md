# india-ate Quality Report

Snapshot: **2026-11-27**
Scope: backend, REST/MCP interfaces, API contract suite, and static web demo.

This is a current quality snapshot, not a historical phase sign-off. Re-run the
commands below before a release.

## Summary

| Gate | Result | Status |
| --- | --- | --- |
| Backend tests | 187 passed | Pass |
| Coverage | 98.28% (1335 statements, 23 missed) | Pass (≥95%) |
| Ruff check | All checks passed | Pass |
| Ruff format | 78 files already formatted | Pass |
| Mypy strict | Success, 42 source files | Pass |
| Radon complexity | 220 blocks, average A (2.0), max B | Pass (≤B / CC 10) |
| Mutation score | 80.65% (2134/2646 killed) | Pass (≥80%) |
| Postman contract | 9 requests, 19 assertions, 0 failed | Pass |
| Frontend tests | 22 passed (7 files) | Pass |
| Astro check | 0 errors, 0 warnings, 0 hints | Pass |
| Astro build | 15 pages | Pass |
| npm audit (prod) | 0 vulnerabilities | Pass |
| Package build | wheel + sdist; `py.typed` and `LICENSE` included | Pass |

## Backend

```text
$ uv run pytest -q
187 passed, 4 warnings in 2.12s
Required test coverage of 95% reached. Total coverage: 98.28%

$ uv run ruff check src/ tests/
All checks passed!

$ uv run ruff format --check src/ tests/
78 files already formatted

$ uv run mypy src/
Success: no issues found in 42 source files

$ uv run radon cc src/ -a -nb
220 blocks (classes, functions, methods) analyzed.
Average complexity: A (2.0)
```

The highest-complexity functions are grade B and remain at or below the CC 10
threshold:

- `models/identifiers.py::_normalize_and_validate` — B
- `api/router.py::_dispatch_get` — B
- `services/discovery.py::_evaluate_premises` — B
- `services/grievance.py::generate_grievance_packet` — B

## Mutation testing

Fresh run with `.mutmut-cache` removed:

```text
$ uv run mutmut run
$ uv run mutmut results --all true
total     2646
killed    2134
survived   511
suspicious   0
```

**Mutation score: 80.65% (2134/2646).** Survivors are concentrated in
pre-existing adapter and MCP error branches; the release gate is met.

## API contract

```text
$ postman collection lint postman/collections/india-ate-api --fail-severity warning
No issues found. Scanned: 9 | Errors: 0 | Warnings: 0

$ postman environment lint postman/environments/local.environment.yaml --fail-severity warning
No issues found. Scanned: 1 | Errors: 0 | Warnings: 0

$ postman collection run postman/collections/india-ate-api \
    -e postman/environments/local.environment.yaml
9 requests, 19 assertions, 0 failed
```

The contract covers health/CORS, decoding, Fact Receipt, ghost-brand cluster,
nearby options, food search/detail, non-persisted grievance generation, and the
403 rejection of unauthenticated persistence.

## Data-integrity verification

- `build_fact_receipt()` includes only `official_registry` and
  `peer_reviewed_science` events.
- User-submitted grievance tickets (`user_verified_snapshot`) are excluded from
  official receipts and from `last_verified_at`.
- `find_verified_nearby_switches()` ignores user-submitted events.
- HTTP grievance persistence is disabled by default and requires
  `--allow-grievance-persist`; the API returns 403 otherwise.
- The web demo fixtures use `synthetic_demo` provenance, `example.com` source
  URLs, explicit `(Synthetic)` names, and an all-zero placeholder hash.
- Every web page renders a synthetic-demo banner and tier labels.
- Generated demo record pages are `noindex`; the sitemap lists only the landing
  page while the dataset is synthetic.

## Security checks

- No hard-coded secrets or token assignments in `src/`, `web/src/`, or
  `.github/`.
- SQL uses parameterized statements in `store/sqlite.py` and `store/duckdb.py`.
- Request bodies are capped at 1 MB (`MAX_REQUEST_BODY_BYTES`).
- API responses set `Cache-Control: no-store` and
  `X-Content-Type-Options: nosniff`.
- CORS is intentionally permissive for the public read surface; write
  persistence is opt-in and local-only.
- `npm audit --omit=dev --audit-level=high`: 0 vulnerabilities.

## Architecture checks

```text
$ grep -rn "from india_ate.store" src/india_ate/models/
$ grep -rnE "import (sqlite3|duckdb|click|httpx|bs4|logfire)|from (sqlite3|duckdb|click|httpx|bs4|logfire)" src/india_ate/models/
```

Both return no matches. `models/` remains free of outer-layer and framework
imports.

## Packaging

```text
$ uv build
Successfully built dist/india_ate-0.1.0.tar.gz
Successfully built dist/india_ate-0.1.0-py3-none-any.whl
```

The wheel includes `india_ate/py.typed` and
`india_ate-0.1.0.dist-info/licenses/LICENSE`.

## Web

```text
$ cd web && npm ci && npm test && npm run check && npm run build
Test Files  7 passed (7)
Tests       22 passed (22)
Result: 0 errors, 0 warnings, 0 hints
15 page(s) built
```

A second build with `BASE_PATH=/india-ate/` verifies GitHub Pages project-path
linking and asset resolution.

## Sign-off

The release gates in `.swarmforge/articles/engineering.prompt` pass. The demo
dataset is synthetic and clearly labelled; production data must be ingested from
source-backed records under [docs/DATA_POLICY.md](docs/DATA_POLICY.md).
