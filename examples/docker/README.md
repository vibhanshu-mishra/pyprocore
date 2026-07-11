# Docker Examples

These examples show how to run PyProcore in a repeatable Docker environment.
Docker is optional. You can keep using the normal Python and CLI setup.

## Before You Start

Install Docker Desktop or Docker Engine, then run commands from the repository
root.

Do not commit real `.env` files, token stores, downloads, logs, or generated
workflow outputs. Use `.env.example` as a template only.

## Build the Image

```bash
make docker-build
```

Check the CLI inside the image:

```bash
make docker-help
```

## Dry-Run a Workflow Plan

```bash
./examples/docker/run-workflow-in-docker.sh \
  examples/workflow_plans/lightweight_sync.json \
  exports/docker-dry-run
```

PowerShell:

```powershell
.\examples\docker\run-workflow-in-docker.ps1 `
  examples/workflow_plans/lightweight_sync.json `
  exports/docker-dry-run
```

## Docker Compose

The root `docker-compose.yml` runs a safe default command:

```bash
docker compose run --rm pyprocore
```

The example compose file focuses on workflow plans:

```bash
docker compose -f examples/docker/workflow-runner.docker-compose.yml run --rm pyprocore-workflow
```

## Notes

- Dry-run first.
- Mount output folders so generated files stay on your machine.
- For CI or scheduled live runs, use encrypted secrets and a deliberate OAuth
  token-store strategy.
- These examples do not mutate Procore data.
