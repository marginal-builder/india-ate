# india-ate

[![CI](https://github.com/marginal-builder/india-ate/actions/workflows/ci.yml/badge.svg)](https://github.com/marginal-builder/india-ate/actions/workflows/ci.yml)
[![Deploy](https://github.com/marginal-builder/india-ate/actions/workflows/pages.yml/badge.svg)](https://github.com/marginal-builder/india-ate/actions/workflows/pages.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**An open-source Food & Nutrition Premises Entity Graph for India.** Decode
14-digit FSSAI identifiers deterministically, ingest authoritative public
records, resolve ghost-brand clusters, and generate source-backed Fact
Receipts.

**Live demo:** <https://marginal-builder.github.io/india-ate/>

> **Demo data notice**
> The static web demo in `web/` is built from **synthetic fixtures**. Its
> premises, names, events, and placeholder hashes are illustrative only, are
> not FSSAI/FoSCoS records, and must not be used for regulatory, purchasing, or
> legal decisions. The backend never mixes demo fixtures into its official
> Fact Receipts. See [docs/DATA_POLICY.md](docs/DATA_POLICY.md).

## What it does

- **Deterministic FSSAI decoding** — license/registration tier, state/UT,
  issue year, registering officer, and serial number, fully offline.
- **Entity graph** — `FoodPremises`, `BrandListing`, `FoodItem`, `Substance`,
  `ScientificStandard`, and `AuthoritativeEvent` models.
- **Source-backed ingestion** — adapters for FSSAI hygiene ratings, FoSCoS
  recalls, state enforcement feeds, ONDC catalogs, and ICMR-NIN IFCT nutrition
  data, with quarantine-on-doubt validation.
- **Three stores** — SQLite for runtime, JSONL for git-versioned exports, and
  DuckDB/Parquet for analytics.
- **Four interfaces** — Click CLI, REST API, MCP stdio server, and a static
  Astro demo UI.
- **Contract-tested API** — a checked-in Postman v3 collection exercises every
  endpoint in CI.

## Quickstart

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), and Node 20+ for
the web demo.

```bash
git clone https://github.com/marginal-builder/india-ate.git
cd india-ate
uv sync --extra dev
uv run india-ate decode 10013022000417
```

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

### Run the REST API

```bash
uv run india-ate serve --db data/india_ate.db
```

The server binds to `127.0.0.1:8000` by default. It is read-only except for
grievance-packet generation; HTTP persistence is **disabled by default**. For a
local demo that persists grievance tickets, opt in explicitly:

```bash
uv run india-ate serve --db data/india_ate.db --allow-grievance-persist
```

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/v1/decode/10013022000417
curl http://127.0.0.1:8000/v1/receipt/10013022000417
```

See [docs/API.md](docs/API.md) for every endpoint and request shape.

### Run the web demo

```bash
cd web
npm ci
npm run dev
```

Open `http://localhost:4321`. The UI uses the local API when it is reachable and
falls back to the clearly labelled synthetic fixtures otherwise. Build the
static site with:

```bash
npm run build
```

### Run the MCP server

```bash
uv run india-ate mcp --db data/india_ate.db
```

Example MCP client configuration:

```json
{
  "mcpServers": {
    "india-ate": {
      "command": "uv",
      "args": ["run", "india-ate", "mcp", "--db", "data/india_ate.db"],
      "cwd": "/absolute/path/to/india-ate"
    }
  }
}
```

The MCP tools are `decode_fssai`, `get_fact_receipt`, `get_ghost_brand_cluster`,
`find_verified_nearby_switches`, `lookup_food_nutrition`, and
`generate_grievance_packet`.

## Ingest data

```bash
uv run india-ate ingest hygiene --from-file tests/fixtures/hygiene_sample.html --db data/india_ate.db
uv run india-ate ingest recall --from-file recall.json --db data/india_ate.db
uv run india-ate ingest enforcement --from-file enforcement.json --db data/india_ate.db
uv run india-ate ingest ondc --from-file ondc.json --db data/india_ate.db
uv run india-ate ingest ifct --from-file ifct.csv --db data/india_ate.db
```

Every ingested entity carries `EvidenceProvenance` with a source URL, retrieval
timestamp, and content hash. Ambiguous records are quarantined instead of being
guessed. Run `uv run india-ate lookup <fssai-id> --db data/india_ate.db` to see
a Fact Receipt.

## Data integrity rules

1. Official Fact Receipts include only `official_registry` and
   `peer_reviewed_science` events.
2. User-submitted grievance snapshots are tagged `user_verified_snapshot` and
   are never presented as official records or used for "last verified"
   timestamps.
3. The web demo's `synthetic_demo` tier is visually distinct and excluded from
   the backend.
4. No secrets, fabricated legal names, or inferred regulatory statuses belong in
   production data. See [docs/DATA_POLICY.md](docs/DATA_POLICY.md).

## Quality gates

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
uv run pytest --cov=india_ate --cov-fail-under=95
uv run radon cc src/ -a -nb
uv run mutmut run && uv run mutmut results   # before a release/handoff
```

Frontend gates:

```bash
cd web
npm ci
npm test
npm run check
npm run build
```

Current verified state on this checkout:

| Gate | Result |
| --- | --- |
| Backend tests | 187 passed |
| Coverage | 98.3% (threshold 95%) |
| Ruff check/format | clean |
| Mypy strict | clean |
| Radon | max grade B, average A |
| Mutation score | 80.65% (threshold 80%) |
| Frontend tests | 22 passed |
| Astro check/build | 0 errors, 15 pages |
| Postman contract | 9 requests, 19 assertions, 0 failures |

## Project layout

```text
src/india_ate/
  models/       domain entities and value objects (no framework imports)
  adapters/     source fetchers, parsers, and validators
  store/        SQLite, JSONL, and DuckDB persistence
  services/     Fact Receipt, discovery, and grievance use cases
  api/          stdlib REST router and HTTP server
  mcp/          JSON-RPC 2.0 MCP tools and stdio transport
  cli.py        Click entry point
web/            Astro static demo (synthetic fixtures)
postman/        API contract suite
features/       BDD feature files
tests/          unit and acceptance tests
docs/           API, data policy, deployment, and publishing notes
```

Architecture and dependency rules: [ARCHITECTURE.md](ARCHITECTURE.md).

## Deploy the demo

The repository includes a GitHub Pages workflow. After pushing to GitHub:

1. Open **Settings → Pages** and set **Source** to **GitHub Actions** (the
   workflow can also enable it on first run).
2. Push to `main`. The site is built with the repository subpath and deployed at
   `https://<owner>.github.io/<repo>/`.
3. For a custom domain, set repository variables `SITE_URL` and `BASE_PATH`
   (for example `https://india-ate.org` and `/`), then add the domain in Pages.

The API is not hosted by the Pages workflow. If you deploy the API elsewhere,
set `PUBLIC_API_BASE` at web build time. See
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for details and
[docs/PUBLISHING.md](docs/PUBLISHING.md) for the one-time GitHub setup.

## Limitations

- The demo dataset is synthetic; it is not a live FSSAI/FoSCoS mirror.
- Ingestion adapters target public sources whose markup and availability can
  change; adapters validate and quarantine rather than guess.
- Grievance packets are structured templates to help a user file a complaint.
  They are not legal advice and do not file anything automatically.
- The REST server is intentionally small and stdlib-based. Put it behind a
  reverse proxy with rate limiting before exposing it publicly.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The repository follows the SwarmForge
engineering constitution in `.swarmforge/`: failing test first, strict typing,
Clean Architecture boundaries, and all quality gates green before handoff.
Security reports: [SECURITY.md](SECURITY.md).

## License

MIT — see [LICENSE](LICENSE).
