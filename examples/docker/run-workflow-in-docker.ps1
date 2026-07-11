param(
    [Parameter(Mandatory = $true)]
    [string]$PlanPath,

    [string]$OutputDir = "exports/docker-dry-run"
)

# Run from the repository root:
# .\examples\docker\run-workflow-in-docker.ps1 examples/workflow_plans/lightweight_sync.json exports/docker-dry-run

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker was not found. Install Docker Desktop or Docker Engine, then try again."
    exit 1
}

if (-not (Test-Path $PlanPath)) {
    Write-Host "Workflow plan not found: $PlanPath"
    exit 1
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

Write-Host "Building the local PyProcore Docker image..."
docker build -t pyprocore:local .

Write-Host "Running workflow plan in dry-run mode..."
docker run --rm `
    -v "${PWD}/exports:/app/exports" `
    pyprocore:local `
    procore-sdk workflow-plan run $PlanPath --output-dir $OutputDir --dry-run

Write-Host "Docker workflow dry-run finished. Output folder: $OutputDir"
