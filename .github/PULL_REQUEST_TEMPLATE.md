## Summary

Describe the change and link the issue.

## Checklist

- [ ] A failing test existed before the implementation (or this is docs/config only).
- [ ] `uv run ruff check src/ tests/` passes.
- [ ] `uv run ruff format --check src/ tests/` passes.
- [ ] `uv run mypy src/` passes.
- [ ] `uv run pytest --cov=india_ate --cov-fail-under=95` passes.
- [ ] `uv run radon cc src/ -a -nb` has no grade C or worse.
- [ ] `cd web && npm ci && npm test && npm run check && npm run build` passes (if web changed).
- [ ] The Postman contract and `docs/API.md` are updated (if the API changed).
- [ ] No fabricated FSSAI IDs, names, statuses, or nutrition values were added.
- [ ] No secrets, `.env` files, or database files are included.
