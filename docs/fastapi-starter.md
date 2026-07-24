# FastAPI Read API Starter

Phase 17E adds an optional FastAPI starter template for developers who want to
copy a small read-only backend example powered by PyProcore.

## What This Is

The FastAPI starter is a copied template. It is not part of the PyProcore
runtime, and PyProcore does not host the app.

The template demonstrates read-only routes:

- `GET /health`
- `GET /projects`
- `GET /projects/{project_id}/rfis`
- `GET /projects/{project_id}/submittals`
- `GET /projects/{project_id}/analytics/project-health`

The analytics route uses Phase 17D local analytics recipes with fake/local
records only.

## Safety Boundaries

- FastAPI is not a PyProcore dependency.
- Uvicorn is not a PyProcore dependency.
- The starter is optional and copied only when a developer asks for it.
- Copying the starter does not install dependencies.
- Copying the starter does not run a server.
- Copying the starter does not call Procore.
- PyProcore does not store credentials for the copied app.
- No Procore writes are enabled.
- No create, update, delete, upload, submit, approve, payment, or mutation
  routes are included.
- No MCP execution is included.
- No Procore tool execution is included.
- No external AI/model calls are included.
- Tests in the copied template use mocked clients and local fake data only.

## Inspect Templates

```bash
procore-sdk templates list
procore-sdk templates show fastapi-read-api
procore-sdk templates show fastapi-read-api --format json
```

These commands inspect local metadata only. They do not require credentials.

## Copy The Starter

Preview files first:

```bash
procore-sdk templates copy fastapi-read-api --output-dir ./tmp-fastapi-read-api --dry-run
```

Copy the files:

```bash
procore-sdk templates copy fastapi-read-api --output-dir ./tmp-fastapi-read-api
```

Existing files are skipped by default. Use `--overwrite` only when you
intentionally want to replace local template files:

```bash
procore-sdk templates copy fastapi-read-api --output-dir ./tmp-fastapi-read-api --overwrite
```

## Copied Template Files

The template includes:

- `README.md`
- `requirements.txt`
- `.env.example`
- `app/main.py`
- `app/config.py`
- `app/procore_client.py`
- `app/routes/projects.py`
- `app/routes/rfis.py`
- `app/routes/submittals.py`
- `app/routes/analytics.py`
- `app/routes/health.py`
- `tests/test_routes_mocked.py`
- `scripts/run_local.sh`

## Before Production Use

The copied starter is educational. Before adapting it for production, add your
own authentication, authorization, deployment process, rate-limit handling,
monitoring, logging policy, and secret storage. Keep routes read-only unless a
separate write-safety design has been reviewed.
