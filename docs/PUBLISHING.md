# Publishing to GitHub

The repository is ready to push. This page covers the one-time GitHub setup.

## 1. Create the repository

With the GitHub CLI:

```bash
gh auth status
gh repo create india-ate --public --source=. --remote=origin --push
```

Or create the repository in the GitHub UI, then:

```bash
git remote add origin https://github.com/<owner>/india-ate.git
git push -u origin main
```

## 2. Enable Actions and Pages

- **Actions** are enabled by default for public repositories.
- **Settings → Pages → Source: GitHub Actions**.
- The `Deploy web demo to GitHub Pages` workflow publishes
  `https://<owner>.github.io/india-ate/` on the next push to `main`.

## 3. Fill in the repository-specific links

The README intentionally avoids hard-coded owner/repo badge URLs. Once the
repository exists, optionally add badges at the top of `README.md`:

```markdown
[![CI](https://github.com/<owner>/india-ate/actions/workflows/ci.yml/badge.svg)](https://github.com/<owner>/india-ate/actions/workflows/ci.yml)
[![Deploy](https://github.com/<owner>/india-ate/actions/workflows/pages.yml/badge.svg)](https://github.com/<owner>/india-ate/actions/workflows/pages.yml)
```

Set `PUBLIC_REPO_URL` in the Pages workflow (it is already wired to
`github.server_url/github.repository`) so the site's **Source** link points at
the repository.

## 4. Recommended repository settings

- **Description:** `Open-source Food & Nutrition Premises Entity Graph for India`
- **Topics:** `fssai`, `food-safety`, `open-data`, `entity-graph`, `python`,
  `astro`, `india`, `mcp`
- **Security:** enable private vulnerability reporting and Dependabot alerts.
- **Branches:** protect `main` and require the `CI` workflow before merging.
- **Pages:** use the included workflow, not a branch folder.

## 5. First-release checklist

```bash
uv sync --extra dev
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
uv run pytest --cov=india_ate --cov-fail-under=95
uv run radon cc src/ -a -nb
cd web && npm ci && npm test && npm run check && npm run build && cd ..
git status
```

Before a tagged release, also run the mutation gate:

```bash
uv run mutmut run
uv run mutmut results
```

The demo is synthetic by design. Do not replace the fixtures with unverified
names or statuses; ingest real records through the adapters and the published
data policy instead.
