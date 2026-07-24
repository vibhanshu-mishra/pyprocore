# PyProcore FastAPI Read API Starter

This is an optional starter template for building a small read-only FastAPI
backend with PyProcore.

## Safety Boundaries

- This folder is a copied starter template, not PyProcore runtime code.
- FastAPI and uvicorn are optional dependencies for this copied template only.
- PyProcore does not host this app.
- PyProcore does not store credentials.
- Use environment variables or your own secret manager.
- No Procore writes, uploads, approvals, payments, or delete routes are included.
- No MCP execution or Procore tool execution is included.
- No external AI/model calls are included.
- Tests use mocked clients and local fake data only.

## Local Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with your own local values. Do not commit `.env`.

## Run Locally

```bash
./scripts/run_local.sh
```

The starter exposes read-only routes:

- `GET /health`
- `GET /projects`
- `GET /projects/{project_id}/rfis`
- `GET /projects/{project_id}/submittals`
- `GET /projects/{project_id}/analytics/project-health`

## Tests

```bash
python3 -m pytest tests
```

The included tests are mocked examples. They should not call Procore.

## Production Notes

Before using this pattern in production, add your own authentication,
authorization, rate-limit handling, monitoring, logging policy, deployment
process, and secret storage. Keep routes read-only unless you intentionally
design and review a separate write-safe integration.
