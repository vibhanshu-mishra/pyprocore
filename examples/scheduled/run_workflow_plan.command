#!/usr/bin/env bash
# Double-click friendly macOS runner for PyProcore workflow plans.
#
# Edit PLAN_PATH and OUTPUT_DIR below, or run this file from Terminal with:
#   ./examples/scheduled/run_workflow_plan.command examples/workflow_plans/nightly_project_context.json ./runs/nightly

set -euo pipefail

PLAN_PATH="${1:-examples/workflow_plans/nightly_project_context.json}"
OUTPUT_DIR="${2:-./runs/nightly-project-context}"

cd "$(dirname "$0")/../.."
export PYTHONPATH=".:${PYTHONPATH:-}"

echo "Starting PyProcore scheduled workflow."
echo "Plan: $PLAN_PATH"
echo "Output: $OUTPUT_DIR"

procore-sdk workflow-plan run "$PLAN_PATH" --output-dir "$OUTPUT_DIR"

echo "PyProcore scheduled workflow finished."
