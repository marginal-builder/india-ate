# Security policy

## Supported versions

This is a pre-1.0 project. Security fixes are applied to the `main` branch.

## Reporting a vulnerability

Do **not** open a public issue for a vulnerability. Use GitHub's private
vulnerability reporting (**Security → Report a vulnerability**) or contact the
maintainers listed on the repository profile. Include:

- affected version or commit;
- reproduction steps;
- impact assessment;
- any suggested fix.

Do not include real personal data, FSSAI credentials, or production database
contents.

## Deployment posture

- The REST server binds `127.0.0.1` by default. Put it behind a TLS reverse proxy
  with rate limiting before exposing it.
- HTTP grievance persistence is disabled by default. `--allow-grievance-persist`
  is intended for local demos only.
- The public API is read-mostly and sends permissive CORS headers by design. If
  you add authentication or write endpoints, tighten CORS and add authorization.
- Request bodies are capped at 1 MB. Keep the cap in place behind proxies.
- Never commit `.env` files, database files, or secrets. SQLite files and
  Parquet snapshots are ignored by git.
- The static demo uses synthetic fixtures; do not send real user reports to it.
