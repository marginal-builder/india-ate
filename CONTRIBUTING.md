# Contributing

## Setup

```bash
uv sync --extra dev
cd web && npm ci && cd ..
```

Read `.swarmforge/constitution.prompt` and the relevant role prompt before
changing code. The repository uses a strict test-first workflow and Clean
Architecture boundaries.

## Before opening a pull request

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
uv run pytest --cov=india_ate --cov-fail-under=95
uv run radon cc src/ -a -nb
cd web && npm test && npm run check && npm run build && cd ..
```

All gates must pass. CI also builds the package, runs the Postman contract suite,
and builds the static site under a GitHub Pages subpath.

## Rules

- **Test first.** Add a failing test before production code.
- **Do not modify `models/base.py`** without architect review.
- **No framework imports in `models/`.** The dependency rule is inward-only.
- **No fabricated data.** Never generate FSSAI IDs, legal names, regulatory
  statuses, or nutrition values. See [docs/DATA_POLICY.md](docs/DATA_POLICY.md).
- **Demo data stays demo.** Synthetic fixtures belong in `web/src/data/seed.ts`,
  must be labelled `synthetic_demo`, and must not enter backend stores.
- **No secrets.** Use environment variables and document them in `.env.example`.
- **Keep the API contract in sync.** Update the Postman collection and
  [docs/API.md](docs/API.md) with endpoint changes.

## Commit style

Use Conventional Commits, for example:

```text
feat(api): add non-persisted grievance packet contract
fix(web): respect GitHub Pages base path in internal links
docs: add data policy and deployment guide
```

## Reporting issues

Use GitHub Issues with a minimal reproduction, the command or endpoint, expected
behavior, and actual behavior. Security issues should follow
[SECURITY.md](SECURITY.md).
