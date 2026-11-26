# Deployment

## Static demo on GitHub Pages

The `Deploy web demo to GitHub Pages` workflow builds `web/` and publishes it.

1. Push the repository to GitHub.
2. In **Settings → Pages**, set **Source** to **GitHub Actions**. The workflow
   also requests enablement on first run.
3. Push to `main` or run the workflow manually.

The default URL is:

```text
https://<owner>.github.io/<repo>/
```

The workflow sets `SITE_URL` and `BASE_PATH` from the repository automatically.
`web/src/lib/base.ts` prefixes every internal link and asset so the site works
under a project subpath.

### Custom domain

Set repository variables under **Settings → Secrets and variables → Actions →
Variables**:

| Variable | Example | Purpose |
| --- | --- | --- |
| `SITE_URL` | `https://india-ate.org` | Canonical origin |
| `BASE_PATH` | `/` | Root path for a custom domain |

Then configure the custom domain in Pages and add the DNS records GitHub
provides.

### Deploying the API

The Pages workflow publishes only static files. It does not host the Python API.
Options:

- **Local only:** leave the demo in offline/synthetic-fixture mode. This is the
  default and is clearly labelled.
- **Hosted API:** run `india-ate serve` behind a TLS reverse proxy with rate
  limiting and request-size limits. Set `PUBLIC_API_BASE` at web build time:
  ```bash
  cd web
  PUBLIC_API_BASE=https://api.example.org npm run build
  ```
- **No persistence:** leave `--allow-grievance-persist` off on public hosts. The
  grievance endpoint still builds packets; it just refuses writes.

The API sends `Access-Control-Allow-Origin: *` because the public read surface is
intended to be embeddable. If you add authenticated or write endpoints, tighten
CORS and add authentication first.

## Container/reverse-proxy notes

The server is stdlib-based and binds `127.0.0.1:8000` by default. For a
container or VM:

- run it as an unprivileged user;
- put SQLite on a persistent volume;
- terminate TLS at the proxy;
- cap request bodies and add rate limits;
- monitor disk usage for the SQLite file and logs;
- back up the database before ingesting large batches.

## Verification after deployment

```bash
curl -fsS https://api.example.org/health
curl -fsS https://api.example.org/v1/decode/10013022000417
```

For the static site, open the Pages URL and verify that the synthetic-demo
banner is visible, internal links include the repository subpath, and
`/sitemap.xml` and `/robots.txt` resolve.
