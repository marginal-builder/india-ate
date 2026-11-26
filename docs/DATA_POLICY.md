# Data & provenance policy

india-ate exists to make food-premises records **traceable**, not to publish
confident-sounding guesses. The rules below are enforced by the models and
services, and are part of the repository's engineering constitution.

## The zero-hallucination rule

Agents and contributors must never generate or infer:

- FSSAI license or registration numbers;
- legal entity names;
- enforcement, recall, suspension, or hygiene statuses;
- nutrition or toxicology values.

Every production entity field must trace to a real `EvidenceProvenance` record
with a real source URL and content hash. Ambiguous records go to quarantine, not
into live entity fields.

## Verification tiers

| Tier | Meaning | Used in official Fact Receipts? |
| --- | --- | --- |
| `official_registry` | A snapshot of an official registry or regulator feed | Yes |
| `peer_reviewed_science` | A peer-reviewed publication or official composition table | Yes |
| `user_verified_snapshot` | A user submission, including grievance tickets | No |
| `synthetic_demo` | Illustrative fixtures in the static web demo only | No |

`build_fact_receipt()` filters to the first two tiers. User-submitted grievance
events never appear under "Official Authoritative Records" and never change
`last_verified_at`. Nearby-switch eligibility also ignores user-submitted
events.

## The static demo dataset

`web/src/data/seed.ts` is a **synthetic demo fixture**:

- names are prefixed with `Demo` and marked `(Synthetic)`;
- provenance sources are labelled `Synthetic demo fixture — ...`;
- source URLs use the reserved `example.com` domain;
- hashes are the all-zero placeholder, making it obvious that no real snapshot
  exists;
- every web page renders a visible synthetic-demo banner and tier labels;
- generated record pages are `noindex` and the sitemap lists only the landing
  page while the data is synthetic.

The demo is intentionally separate from backend stores. It is not imported by
`src/india_ate/` and cannot enter an official Fact Receipt.

## HTTP grievance persistence

Generating a grievance packet is a read-like operation: it validates the ID,
builds deterministic text, and returns it. HTTP persistence is disabled by
default. The CLI's `india-ate grievance --persist` is an explicit local operator
action.

If a server is started with `--allow-grievance-persist`, a persisted ticket is
stored with `verification_tier = "user_verified_snapshot"` and is still excluded
from official receipts. Do not enable this on a public, unauthenticated
deployment.

## Ingestion

Adapters fetch or read public data, parse it strictly, and emit an
`IngestionBatch` containing valid entities plus quarantine records. Invalid or
ambiguous rows are never coerced into entities. The CLI exposes:

```bash
uv run india-ate ingest hygiene --from-file snapshot.html --db data/india_ate.db
uv run india-ate ingest recall --from-file recall.json --db data/india_ate.db
uv run india-ate ingest enforcement --from-file enforcement.json --db data/india_ate.db
uv run india-ate ingest ondc --from-file ondc.json --db data/india_ate.db
uv run india-ate ingest ifct --from-file ifct.csv --db data/india_ate.db
```

Inspect quarantined rows with the store APIs before retrying them with a
corrected source.

## Reporting a data error

Open an issue with the FSSAI ID, the field, the current value, and the official
source URL that contradicts it. Do not include personal data. Data corrections
that cannot be traced to a public source will be rejected.
