# Workflows

PyProcore workflows build local files from existing SDK read operations. They are
intended for reporting, handoff, scheduled syncs, and AI-ready review packages.

## CSV And JSONL Exports

Use CSV when a spreadsheet is the target. Use JSONL when another program should
process one complete item per line.

```bash
procore-sdk export-rfis --project 352338 --output ./exports/rfis.csv
procore-sdk export-submittals --project 352338 --output ./exports/submittals.csv
```

## Sync RFIs, Submittals, And Documents

Sync workflows create local folders containing metadata, optional summaries,
manifest files, and optional downloaded attachments.

```bash
procore-sdk sync-rfis --project 352338 --output ./exports/rfis --dry-run
procore-sdk sync-submittals --project 352338 --output ./exports/submittals
procore-sdk sync-documents --project 352338 --output ./exports/documents
```

## Project Context Package

Project context packages gather selected project sections into a local folder
with JSON, JSONL, Markdown, and manifest files.

```bash
procore-sdk project-context --project 352338 --include rfis,submittals,daily_logs
```

## Enhanced RFI And Submittal Packages

Enhanced packages gather an item plus related context from other project areas.

```bash
procore-sdk enhanced-rfi-package --project 352338 --rfi-number 15
procore-sdk enhanced-submittal-package --project 352338 --submittal-number 27
```

## AI Review Export

AI review exports transform an existing local package into source indexes,
prompt files, chunk files, and checklists. They do not call Procore or an AI API.

```bash
procore-sdk ai-review-export --package-dir ./rfi-package
procore-sdk ai-prompt-pack --package-dir ./submittal-package --review-type submittal
```

## Workflow Plan Runner

Workflow plans let repeatable jobs live in JSON files.

```bash
procore-sdk workflow-plan list
procore-sdk workflow-plan validate examples/workflow_plans/nightly_project_context.json
procore-sdk workflow-plan run examples/workflow_plans/nightly_project_context.json --dry-run
```

## Scheduled Workflows

Scheduled examples are available for cron, launchd, Windows Task Scheduler, and
GitHub Actions. Start with [Automation](automation.md) and dry-run every plan
before scheduling it.
