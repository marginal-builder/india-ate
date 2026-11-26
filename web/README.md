# india-ate web demo

A static Astro UI for the india-ate Fact Receipt API. It has three modes:

1. **API connected** — the lookup form calls `india-ate serve` at the configured
   `PUBLIC_API_BASE` (default `http://127.0.0.1:8000`).
2. **API offline** — the UI decodes IDs deterministically and falls back to the
   synthetic fixtures in `src/data/seed.ts`, with visible demo labels.
3. **GitHub Pages** — a fully static build under a repository subpath.

## Commands

```bash
npm ci
npm run dev       # http://localhost:4321
npm test          # Vitest
npm run check     # Astro/TypeScript diagnostics
npm run build     # static output in dist/
```

## Configuration

Copy `.env.example` to `.env` if you want to override defaults:

| Variable | Default | Purpose |
| --- | --- | --- |
| `PUBLIC_API_BASE` | `http://127.0.0.1:8000` | API base shown in the lookup form |
| `PUBLIC_REPO_URL` | unset | Adds a "Source" link to the navigation |
| `SITE_URL` | `https://india-ate.org` | Astro canonical origin |
| `BASE_PATH` | `/` | Deployment subpath, e.g. `/india-ate/` |

`SITE_URL` and `BASE_PATH` are also set by the GitHub Pages workflow.

## Demo data

`src/data/seed.ts` is synthetic:

- names are prefixed `Demo` and suffixed `(Synthetic)`;
- provenance is `synthetic_demo`;
- source URLs use `example.com`;
- hashes are all-zero placeholders.

Every page renders a synthetic-demo banner. Generated record pages are
`noindex`, and the sitemap advertises only the landing page while the demo data
is synthetic. Do not replace these fixtures with real names or statuses without
ingesting source-backed records through the backend. See
[../docs/DATA_POLICY.md](../docs/DATA_POLICY.md).

## Deployment

The root workflow `.github/workflows/pages.yml` builds and deploys `dist/`.
Internal links use `src/lib/base.ts` so the site works at
`https://<owner>.github.io/<repo>/`.
