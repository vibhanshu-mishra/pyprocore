# macOS launchd Scheduling

`launchd` is macOS's built-in scheduler. It is a good option when you want a
workflow plan to run regularly on your Mac.

## Before You Start

Validate and dry-run the plan from Terminal:

```bash
cd /absolute/path/to/pyprocore
PYTHONPATH=. procore-sdk workflow-plan validate examples/workflow_plans/nightly_project_context.json
PYTHONPATH=. procore-sdk workflow-plan run examples/workflow_plans/nightly_project_context.json --dry-run
```

## Template Plist

Start from:

```text
examples/scheduled/com.pyprocore.nightly-project-context.plist
```

Replace every `/absolute/path/to/pyprocore` value with your real project path.
`launchd` is strict about paths, so do not use `~` or relative paths.

## Install

Copy the edited plist into your LaunchAgents folder:

```bash
cp examples/scheduled/com.pyprocore.nightly-project-context.plist \
  ~/Library/LaunchAgents/com.pyprocore.nightly-project-context.plist
```

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.pyprocore.nightly-project-context.plist
```

Unload it:

```bash
launchctl unload ~/Library/LaunchAgents/com.pyprocore.nightly-project-context.plist
```

## Logs

The template writes to:

```text
logs/launchd-nightly-project-context.log
logs/launchd-nightly-project-context.err
```

Create the `logs/` folder before loading the plist.

## Troubleshooting

- Use absolute paths everywhere.
- Run the helper script manually before loading the plist.
- Confirm `.env` is in the working directory.
- Check both the standard output and error log files.
- Dry-run first, then schedule the real run.
