#!/usr/bin/env bash
set -euo pipefail

# Run from the repository root:
# ./examples/docker/run-workflow-in-docker.sh examples/workflow_plans/lightweight_sync.json exports/docker-dry-run

PLAN_PATH="${1:-}"
OUTPUT_DIR="${2:-exports/docker-dry-run}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker was not found. Install Docker Desktop or Docker Engine, then try again."
  exit 1
fi

if [ -z "$PLAN_PATH" ]; then
  echo "Please provide a workflow plan path."
  echo "Example: ./examples/docker/run-workflow-in-docker.sh examples/workflow_plans/lightweight_sync.json"
  exit 1
fi

if [ ! -f "$PLAN_PATH" ]; then
  echo "Workflow plan not found: $PLAN_PATH"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "Building the local PyProcore Docker image..."
docker build -t pyprocore:local .

echo "Running workflow plan in dry-run mode..."
docker run --rm \
  -v "$PWD/exports:/app/exports" \
  pyprocore:local \
  procore-sdk workflow-plan run "$PLAN_PATH" --output-dir "$OUTPUT_DIR" --dry-run

echo "Docker workflow dry-run finished. Output folder: $OUTPUT_DIR"
