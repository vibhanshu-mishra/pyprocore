# Windows Task Scheduler

Windows Task Scheduler can run PyProcore workflow plans through PowerShell.

## Before You Start

Validate and dry-run the plan from PowerShell:

```powershell
cd C:\path\to\pyprocore
procore-sdk workflow-plan validate examples\workflow_plans\nightly_project_context.json
procore-sdk workflow-plan run examples\workflow_plans\nightly_project_context.json --dry-run
```

## PowerShell Runner

Use:

```text
examples\scheduled\run_workflow_plan.ps1
```

Manual run:

```powershell
powershell -ExecutionPolicy Bypass -File examples\scheduled\run_workflow_plan.ps1 `
  -PlanPath examples\workflow_plans\nightly_project_context.json `
  -OutputDir runs\nightly-project-context
```

## Task Scheduler Setup

1. Open Task Scheduler.
2. Choose **Create Basic Task**.
3. Pick a trigger, such as Daily or Weekly.
4. Choose **Start a Program**.
5. Program/script:

   ```text
   powershell.exe
   ```

6. Arguments:

   ```text
   -ExecutionPolicy Bypass -File C:\path\to\pyprocore\examples\scheduled\run_workflow_plan.ps1 -PlanPath C:\path\to\pyprocore\examples\workflow_plans\nightly_project_context.json -OutputDir C:\path\to\pyprocore\runs\nightly-project-context
   ```

7. Start in:

   ```text
   C:\path\to\pyprocore
   ```

## Environment and Logs

Keep `.env` in the project working directory. The runner changes to the project
root before calling the CLI. Configure Task Scheduler history or redirect output
from a wrapper script if you need persistent logs.

## Troubleshooting

- Use full Windows paths in the task.
- Confirm Task Scheduler uses the same user account that completed OAuth.
- Run the PowerShell command manually first.
- Use dry-run before enabling a recurring trigger.
- If auth fails, confirm the token store strategy for the scheduled user.
