#!/usr/bin/env bash
# Run a PyProcore workflow plan from macOS/Linux cron or a terminal.
#
# Usage:
#   ./examples/scheduled/run_workflow_plan.sh examples/workflow_plans/nightly_project_context.json ./runs/nightly

set -euo pipefail

PLAN_PATH="${1:-}"
OUTPUT_DIR="${2:-}"

if [[ -z "$PLAN_PATH" ]]; then
  echo "Missing workflow plan path."
  echo "Usage: $0 path/to/workflow.json [output-dir]"
  exit 2
fi

cd "$(dirname "$0")/../.."
export PYTHONPATH=".:${PYTHONPATH:-}"

echo "Starting PyProcore workflow plan: $PLAN_PATH"

if [[ -n "$OUTPUT_DIR" ]]; then
  procore-sdk workflow-plan run "$PLAN_PATH" --output-dir "$OUTPUT_DIR"
else
  procore-sdk workflow-plan run "$PLAN_PATH"
fi

echo "PyProcore workflow plan finished."
