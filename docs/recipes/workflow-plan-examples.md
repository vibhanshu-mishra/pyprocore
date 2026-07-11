# Workflow Plan Examples

## What this does

Shows small JSON workflow plans for repeatable local automation. Plans describe
existing PyProcore workflows and options; they do not run shell commands.

## When to use it

Use these examples as starting points for scheduled syncs, project context
exports, and AI review package generation.

## Before you start

Use placeholder IDs while learning. Replace `project_id`, `company_id`, and item
numbers with values from your own Procore account before a real run.

Useful environment variables:

- `WORKFLOW_PLAN_PATH`
- `WORKFLOW_RUN_OUTPUT_DIR`

## Code

```json
{
  "name": "project-context-and-ai-export",
  "defaults": {
    "company_id": 456,
    "project_id": 123,
    "output_root": "./exports/project-context-and-ai-export"
  },
  "steps": [
    {
      "id": "project_context",
      "workflow": "project_context",
      "options": {
        "include": ["project", "rfis", "submittals"],
        "output_dir": "{output_root}/project-context"
      }
    },
    {
      "id": "ai_export",
      "workflow": "ai_review_export",
      "depends_on": ["project_context"],
      "options": {
        "package_dir": "{steps.project_context.output_dir}",
        "output_dir": "{output_root}/ai-export"
      }
    }
  ]
}
```

CLI example:

```bash
procore-sdk workflow-plan run examples/workflow_plans/project_context_and_ai_export.json --dry-run
```

## Expected output

Dry-run output shows the resolved step order and the local folders each step
would use. A real run writes the same manifest files plus whatever files the
underlying workflows create.

## Common issues

- If `{steps.some_step.output_dir}` cannot resolve, confirm the referenced step
  appears earlier in the plan.
- If a real run fails with Procore permissions, validate that the OAuth user can
  access the company, project, and tool.
- Start with `--dry-run` before using cron or other schedulers.
- Use `procore-sdk workflow-plan list` to see supported workflow names.
