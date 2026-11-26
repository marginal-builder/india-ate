# india-ate HTTP API

Run the server:

```bash
uv run india-ate serve --db data/india_ate.db
```

Default bind: `127.0.0.1:8000`. The API is a small stdlib JSON service; put it
behind a reverse proxy with TLS and rate limiting before exposing it publicly.

All responses are JSON except `OPTIONS` (204, no body) and errors share the
shape `{"error": "message"}`. Every response includes permissive CORS headers
for the public read API, `Cache-Control: no-store`, and
`X-Content-Type-Options: nosniff`. Request bodies are capped at 1 MB.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness probe: `{"status":"ok"}` |
| `GET` | `/v1/decode/{fssai_id}` | Deterministic offline ID decode |
| `GET` | `/v1/receipt/{fssai_id}` | Source-backed Fact Receipt |
| `GET` | `/v1/cluster/{fssai_id}` | Premises + ghost-brand listings |
| `GET` | `/v1/nearby/{postal_code}` | Nearby premises with official audits or Tier-1 licenses |
| `GET` | `/v1/foods?q={query}` | Search IFCT food items |
| `GET` | `/v1/food/{item_id}` | Food item plus linked scientific standards |
| `POST` | `/v1/grievance` | Build a Food Safety Connect grievance packet |
| `OPTIONS` | any | CORS preflight |

### `GET /v1/decode/{fssai_id}`

```bash
curl http://127.0.0.1:8000/v1/decode/10013022000417
```

Returns the decoded tier, authority scope, state/UT, issue year, officer code,
central regional office (when applicable), and serial. Invalid IDs return 400.

### `GET /v1/receipt/{fssai_id}`

```bash
curl http://127.0.0.1:8000/v1/receipt/10013022000417
```

Returns `fssai_id`, `decoded`, `premises`, `ghost_brand_count`,
`brand_listings`, `events`, and `last_verified_at`. Only events whose
provenance tier is `official_registry` or `peer_reviewed_science` are included.
`last_verified_at` is computed from official provenance only.

A format-valid ID that has no ingested premises returns a decoded receipt with
empty records, not a 404.

### `GET /v1/cluster/{fssai_id}`

Returns `{"premises": ..., "listings": [...]}` for a cached premises, or 404 if
no premises is cached.

### `GET /v1/nearby/{postal_code}`

Returns `{"postal_code": "...", "options": [...]}`. A premise is included when
it has a completed hygiene audit or a Tier-1 license, and it is excluded when an
official recall or enforcement/suspension event exists.

### `GET /v1/foods?q=...`

Search canonical food names and IFCT codes. `q` may be empty to list all items.

### `GET /v1/food/{item_id}`

`item_id` must be URL-encoded when it contains a colon:

```bash
curl 'http://127.0.0.1:8000/v1/food/item%3Ain%3Aifct%3AA001'
```

Returns `{"item": ..., "standards": [...]}` or 404.

### `POST /v1/grievance`

Request:

```json
{
  "fssai_id": "10013022000417",
  "issue_category": "spoiled_food",
  "order_reference": "ORD-123",
  "description": "Delivered with a broken seal.",
  "incident_date": "2026-11-26",
  "persist": false
}
```

`issue_category` is one of `spoiled_food`, `misbranded`,
`shelf_life_30pct_violation`, `unlicensed_or_suspended`, `foreign_matter`, or
`other`. The response contains a deterministic `packet_id`, the 15-day
`escalation_deadline`, the decoded jurisdiction, and the filing text fields.

**Persistence:** `persist` defaults to `false`. When `true`, the server returns
403 unless it was started with `--allow-grievance-persist`. That flag is for
local demos only; do not enable unauthenticated writes on a public deployment.

## Contract tests

The Postman v3 collection is the executable contract:

```bash
uv run india-ate serve --db /tmp/contract.db &
postman collection run postman/collections/india-ate-api \
  -e postman/environments/local.environment.yaml
```

CI seeds a fixture database, starts the server, and runs the collection on every
push and pull request.
