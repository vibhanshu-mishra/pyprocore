# Run a PyProcore workflow plan from Windows PowerShell or Task Scheduler.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File examples\scheduled\run_workflow_plan.ps1 `
#     -PlanPath examples\workflow_plans\nightly_project_context.json `
#     -OutputDir runs\nightly

param(
    [Parameter(Mandatory = $true)]
    [string]$PlanPath,

    [Parameter(Mandatory = $false)]
    [string]$OutputDir
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

$env:PYTHONPATH = ".;$env:PYTHONPATH"

Write-Host "Starting PyProcore workflow plan: $PlanPath"

if ($OutputDir) {
    procore-sdk workflow-plan run $PlanPath --output-dir $OutputDir
} else {
    procore-sdk workflow-plan run $PlanPath
}

Write-Host "PyProcore workflow plan finished."
