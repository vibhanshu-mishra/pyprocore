# Docker Automation

Docker is optional. It gives teams a repeatable way to run PyProcore commands
locally, in scheduled jobs, or in CI without depending on a developer laptop's
Python environment.

## What this includes

- Root `Dockerfile`
- Root `docker-compose.yml`
- Docker examples in `examples/docker/`
- Optional Makefile helpers

## Build the image

```bash
make docker-build
```

Check the CLI:

```bash
make docker-help
```

The default container command is safe:

```bash
procore-sdk --help
```

## Run a workflow plan in dry-run mode

```bash
make docker-run-plan PLAN=examples/workflow_plans/lightweight_sync.json
```

Or use the helper script:

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

Run the safe default command:

```bash
docker compose run --rm pyprocore
```

The compose file reads environment variables from your shell. Docker Compose
also reads a local `.env` file for variable substitution when present.

## Secrets and token stores

Do not commit:

- `.env`
- token stores
- downloads
- logs
- run outputs
- webhook event stores

For live Procore workflows, the container needs valid OAuth configuration and a
deliberate token-store strategy. Dry-run commands are the safest first step.

## Troubleshooting

If Docker cannot find the plan file, run the command from the repository root.

If generated files do not appear locally, confirm the output folder is mounted
as a volume.

If live commands cannot authenticate, confirm `.env` values and token-store
handling. Docker does not automatically inherit your local token files unless
you mount them intentionally.
