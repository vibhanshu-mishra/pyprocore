"""Local integration blueprint inventory and readiness checks."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pyprocore.integrations.models import (
    IntegrationBlueprint,
    IntegrationCredentialRequirement,
    IntegrationEndpoint,
    IntegrationFindingSeverity,
    IntegrationReadinessFinding,
    IntegrationReadinessReport,
    IntegrationSyncPlan,
)


def list_integration_blueprints() -> list[IntegrationBlueprint]:
    """Return built-in local integration blueprints.

    Returns:
        Blueprint metadata. These are local templates only and do not call
        Procore, schedule jobs, create services, or enable write actions.
    """
    return [_build_blueprint(definition) for definition in _BLUEPRINT_DEFINITIONS]


def get_integration_blueprint(name: str) -> IntegrationBlueprint:
    """Return one built-in integration blueprint by name.

    Args:
        name: Stable blueprint name.

    Returns:
        Matching blueprint metadata.

    Raises:
        KeyError: If no blueprint exists for the name.
    """
    for blueprint in list_integration_blueprints():
        if blueprint.name == name:
            return blueprint
    raise KeyError(f"Unknown integration blueprint: {name}")


def build_integration_readiness_report(
    blueprint_name: str,
    output_dir: Path | str,
    *,
    env: dict[str, str] | None = None,
    token_store_path: Path | str | None = None,
    sync_log_dir: Path | str | None = None,
    webhook_secret_env: str = "PROCORE_WEBHOOK_SECRET",
    create_output_dir: bool = False,
) -> IntegrationReadinessReport:
    """Build a local readiness report for an integration blueprint.

    Args:
        blueprint_name: Built-in blueprint name.
        output_dir: Local output directory to inspect.
        env: Optional environment mapping for tests.
        token_store_path: Optional token store path to inspect.
        sync_log_dir: Optional sync log directory to inspect.
        webhook_secret_env: Environment variable name used for webhook secrets.
        create_output_dir: Whether to create the output directory if missing.

    Returns:
        Local readiness report with findings.
    """
    blueprint = get_integration_blueprint(blueprint_name)
    environment = dict(os.environ if env is None else env)
    output_path = Path(output_dir)
    findings: list[IntegrationReadinessFinding] = []

    if output_path.exists():
        if output_path.is_dir():
            findings.append(
                _finding(
                    "info",
                    "output_dir_exists",
                    f"Output directory exists: {output_path}",
                )
            )
        else:
            findings.append(
                _finding(
                    "error",
                    "output_path_not_directory",
                    f"Output path exists but is not a directory: {output_path}",
                    "Choose a directory path for integration output.",
                )
            )
    elif create_output_dir:
        output_path.mkdir(parents=True, exist_ok=True)
        findings.append(
            _finding("info", "output_dir_created", f"Created output directory: {output_path}")
        )
    else:
        findings.append(
            _finding(
                "warning",
                "output_dir_missing",
                f"Output directory does not exist yet: {output_path}",
                "Create it before running scheduled jobs, or dry-run first.",
            )
        )

    findings.extend(_environment_findings(blueprint, environment))
    findings.extend(_token_store_findings(token_store_path))
    findings.extend(_sync_log_findings(sync_log_dir))

    if "webhook" in blueprint.name and not environment.get(webhook_secret_env):
        findings.append(
            _finding(
                "warning",
                "webhook_secret_missing",
                f"{webhook_secret_env} is not set for local webhook signature tests.",
                "Set a local webhook secret environment variable for fixture verification.",
            )
        )

    if not blueprint.safety_boundaries:
        findings.append(
            _finding(
                "error",
                "safety_boundaries_missing",
                "Blueprint does not declare safety boundaries.",
            )
        )
    else:
        findings.append(
            _finding(
                "info",
                "safety_boundaries_declared",
                "Blueprint declares local-only safety boundaries.",
            )
        )

    error_count = sum(finding.severity == IntegrationFindingSeverity.ERROR for finding in findings)
    return IntegrationReadinessReport(
        blueprint_name=blueprint.name,
        output_dir=str(output_path),
        ready=error_count == 0,
        finding_count=len(findings),
        findings=findings,
    )


def _environment_findings(
    blueprint: IntegrationBlueprint,
    environment: dict[str, str],
) -> list[IntegrationReadinessFinding]:
    findings: list[IntegrationReadinessFinding] = []
    for requirement in blueprint.required_environment_variables:
        if requirement.required and not environment.get(requirement.name):
            findings.append(
                _finding(
                    "warning",
                    "required_env_missing",
                    f"Required environment variable is not set: {requirement.name}",
                    "Configure it in your shell, secret manager, or local .env file.",
                )
            )
        elif requirement.required:
            findings.append(
                _finding(
                    "info",
                    "required_env_present",
                    f"Required environment variable is present: {requirement.name}",
                )
            )
    if environment.get("PROCORE_CLIENT_SECRET") in {"changeme", "replace-me", "TODO"}:
        findings.append(
            _finding(
                "error",
                "placeholder_secret",
                "PROCORE_CLIENT_SECRET appears to be a placeholder.",
                "Replace placeholder values before using a production template.",
            )
        )
    return findings


def _token_store_findings(
    token_store_path: Path | str | None,
) -> list[IntegrationReadinessFinding]:
    if token_store_path is None:
        return [
            _finding(
                "info",
                "token_store_not_configured",
                "No token store path was provided for this readiness check.",
            )
        ]
    path = Path(token_store_path)
    repo_root = Path.cwd().resolve()
    try:
        inside_repo = path.resolve().is_relative_to(repo_root)
    except OSError:
        inside_repo = False
    if inside_repo:
        return [
            _finding(
                "warning",
                "token_store_inside_repo",
                f"Token store path appears to be inside the repository: {path}",
                "Prefer a path outside the checkout or make sure it is ignored.",
            )
        ]
    return [
        _finding(
            "info",
            "token_store_outside_repo",
            f"Token store path appears outside the current repository: {path}",
        )
    ]


def _sync_log_findings(sync_log_dir: Path | str | None) -> list[IntegrationReadinessFinding]:
    if sync_log_dir is None:
        return [
            _finding(
                "info",
                "sync_log_dir_not_configured",
                "No sync log directory was provided for this readiness check.",
            )
        ]
    path = Path(sync_log_dir)
    if path.exists() and path.is_dir():
        return [_finding("info", "sync_log_dir_exists", f"Sync log directory exists: {path}")]
    return [
        _finding(
            "warning",
            "sync_log_dir_missing",
            f"Sync log directory does not exist yet: {path}",
            "Create it before scheduled runs, or let your local runner create it.",
        )
    ]


def _finding(
    severity: str,
    code: str,
    message: str,
    suggested_action: str | None = None,
) -> IntegrationReadinessFinding:
    return IntegrationReadinessFinding(
        severity=IntegrationFindingSeverity(severity),
        code=code,
        message=message,
        suggested_action=suggested_action,
    )


def _credential(name: str, description: str, *, secret: bool = False) -> dict[str, object]:
    return {"name": name, "description": description, "secret": secret}


def _build_blueprint(definition: dict[str, Any]) -> IntegrationBlueprint:
    credentials = [
        IntegrationCredentialRequirement.model_validate(item)
        for item in definition["required_environment_variables"]
    ]
    endpoints = [
        IntegrationEndpoint.model_validate(item) for item in definition.get("endpoints", [])
    ]
    sync_plan_data = definition.get("sync_plan")
    sync_plan = IntegrationSyncPlan.model_validate(sync_plan_data) if sync_plan_data else None
    return IntegrationBlueprint(
        name=str(definition["name"]),
        title=str(definition["title"]),
        description=str(definition["description"]),
        intended_use=str(definition["intended_use"]),
        required_environment_variables=credentials,
        required_pyprocore_capabilities=list(definition["required_pyprocore_capabilities"]),
        endpoints=endpoints,
        sync_plan=sync_plan,
        local_output_files=list(definition["local_output_files"]),
        safety_boundaries=_DEFAULT_SAFETY_BOUNDARIES
        + list(definition.get("safety_boundaries", [])),
        suggested_deployment_notes=list(definition["suggested_deployment_notes"]),
        no_secrets_guidance=_NO_SECRETS_GUIDANCE,
        test_strategy=list(definition["test_strategy"]),
        example_commands=list(definition["example_commands"]),
        pseudocode=list(definition["pseudocode"]),
    )


_COMMON_ENV = [
    _credential("PROCORE_CLIENT_ID", "OAuth client identifier."),
    _credential("PROCORE_CLIENT_SECRET", "OAuth client secret.", secret=True),
    _credential("PROCORE_REDIRECT_URI", "OAuth redirect URI."),
    _credential("PROCORE_LOGIN_URL", "Procore OAuth login URL."),
    _credential("PROCORE_API_BASE", "Procore REST API base URL."),
    _credential("PROCORE_COMPANY_ID", "Default Procore company identifier."),
]

_DEFAULT_SAFETY_BOUNDARIES = [
    "Blueprint metadata only; no hosted service is created.",
    "No Procore API calls are made by blueprint commands.",
    "No Procore create/update/delete/upload/approve/submit/payment actions are enabled.",
    "No database dependency is required.",
    "No automatic scheduler is enabled.",
    "No external AI/model calls are made.",
    "MCP remains discovery-only and tool execution remains disabled.",
]

_NO_SECRETS_GUIDANCE = [
    "Never commit .env files, token stores, OAuth client secrets, or webhook secrets.",
    "Store production secrets in your deployment platform or local secret manager.",
    "Redact tokens and Authorization headers from sync logs and audit events.",
]

_BLUEPRINT_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "procore_to_csv_sync_worker",
        "title": "Procore to CSV Sync Worker",
        "description": (
            "Template guidance for exporting read-only Procore resources to local CSV files."
        ),
        "intended_use": "Scheduled local or CI jobs that produce CSV snapshots for reporting.",
        "required_environment_variables": _COMMON_ENV,
        "required_pyprocore_capabilities": ["rfis", "submittals", "documents", "directory"],
        "sync_plan": {
            "name": "csv_snapshot",
            "description": "Read resources and write local CSV files.",
            "resources": ["companies", "projects", "rfis", "submittals"],
            "output_files": ["exports/*.csv", "sync_runs/*.json", "sync_runs/*.jsonl"],
        },
        "local_output_files": ["exports/rfis.csv", "exports/submittals.csv", "sync_runs/run.json"],
        "suggested_deployment_notes": [
            "Run from cron, launchd, Task Scheduler, or GitHub Actions after OAuth setup.",
            "Use absolute output paths and rotate local logs.",
        ],
        "test_strategy": [
            "Mock PyProcore clients.",
            "Run dry-runs against local fixtures.",
            "Assert CSV headers and redacted logs.",
        ],
        "example_commands": [
            "procore-sdk integrations sync-run sample --output-dir ./exports",
        ],
        "pseudocode": [
            "load settings",
            "create local sync run record",
            "call read-only SDK list helpers",
            "write CSV outputs",
            "complete or fail local sync run record",
        ],
    },
    {
        "name": "procore_to_jsonl_sync_worker",
        "title": "Procore to JSONL Sync Worker",
        "description": "Template guidance for writing read-only Procore snapshots as local JSONL.",
        "intended_use": "Append-friendly exports for downstream indexing or internal analytics.",
        "required_environment_variables": _COMMON_ENV,
        "required_pyprocore_capabilities": ["documents", "drawings", "specifications", "photos"],
        "sync_plan": {
            "name": "jsonl_snapshot",
            "description": "Read resources and append local JSONL records.",
            "resources": ["documents", "drawings", "specifications", "photos"],
            "output_files": ["exports/*.jsonl", "sync_runs/*.json"],
        },
        "local_output_files": ["exports/documents.jsonl", "exports/drawings.jsonl"],
        "suggested_deployment_notes": [
            "Write one JSON object per line.",
            "Keep generated JSONL out of source control unless intentionally committed.",
        ],
        "test_strategy": ["Use local fixture rows.", "Validate each line parses as JSON."],
        "example_commands": [
            "procore-sdk integrations blueprint procore_to_jsonl_sync_worker",
        ],
        "pseudocode": ["for resource in resources", "serialize typed model with model_dump"],
    },
    {
        "name": "procore_webhook_receiver",
        "title": "Procore Webhook Receiver Template",
        "description": "Local blueprint for a webhook receiver design and signature test fixtures.",
        "intended_use": "Teams designing their own webhook ingestion service.",
        "required_environment_variables": _COMMON_ENV
        + [
            _credential(
                "PROCORE_WEBHOOK_SECRET", "Local webhook signature test secret.", secret=True
            )
        ],
        "required_pyprocore_capabilities": ["webhook helpers", "workflow plan dispatch"],
        "endpoints": [
            {
                "name": "receive_webhook",
                "description": "Example path a user-owned service might expose.",
                "method": "POST",
                "path": "/webhooks/procore",
                "read_only": True,
                "pseudocode": ["verify local signature", "write sanitized event JSONL"],
            }
        ],
        "local_output_files": ["webhooks/events.jsonl", "webhooks/sample_event.json"],
        "suggested_deployment_notes": [
            "This repo does not start or host a webhook receiver.",
            "Match signature headers to your configured provider format.",
        ],
        "test_strategy": [
            "Use local HMAC fixture helpers.",
            "Test valid and invalid signatures without network calls.",
        ],
        "example_commands": [
            "procore-sdk integrations webhook sample-event --output ./webhooks/sample.json",
        ],
        "pseudocode": [
            "receive request in your service",
            "verify signature",
            "persist sanitized event",
        ],
    },
    {
        "name": "procore_fastapi_read_api",
        "title": "FastAPI Read API Template",
        "description": "Static guidance for a user-owned read-only internal API.",
        "intended_use": "Internal teams building their own read-only Procore data API.",
        "required_environment_variables": _COMMON_ENV,
        "required_pyprocore_capabilities": ["companies", "projects", "rfis", "submittals"],
        "endpoints": [
            {
                "name": "list_rfis",
                "description": "Example read-only endpoint shape.",
                "method": "GET",
                "path": "/projects/{project_id}/rfis",
                "pseudocode": ["return client.rfis.list_rfis(project_id)"],
            }
        ],
        "local_output_files": ["docs/internal-api-plan.md"],
        "suggested_deployment_notes": [
            "FastAPI is mentioned as a design option only; PyProcore does not "
            "add it as a dependency.",
            "Keep auth and rate limiting in your own service layer.",
        ],
        "test_strategy": [
            "Mock PyProcore service calls.",
            "Assert no write routes are exposed.",
        ],
        "example_commands": ["procore-sdk integrations blueprint procore_fastapi_read_api"],
        "pseudocode": [
            "define read-only routes",
            "inject PyProcore client",
            "return typed model JSON",
        ],
    },
    {
        "name": "procore_dashboard_data_bridge",
        "title": "Dashboard Data Bridge Blueprint",
        "description": "Template guidance for preparing local files consumed by a dashboard.",
        "intended_use": (
            "Teams that need dashboard-ready JSON/CSV snapshots without a hosted " "dashboard here."
        ),
        "required_environment_variables": _COMMON_ENV,
        "required_pyprocore_capabilities": [
            "project context",
            "daily logs",
            "rfis",
            "submittals",
        ],
        "sync_plan": {
            "name": "dashboard_snapshot",
            "description": "Prepare read-only dashboard data files.",
            "resources": ["project health", "rfis", "submittals", "daily logs"],
            "output_files": ["dashboard/project_health.json", "dashboard/open_items.csv"],
        },
        "local_output_files": ["dashboard/project_health.json", "dashboard/open_items.csv"],
        "suggested_deployment_notes": [
            "Point your own dashboard at generated files or copy them to your storage layer.",
        ],
        "test_strategy": ["Use local JSON fixtures.", "Validate schema and no secret fields."],
        "example_commands": [
            "procore-sdk integrations blueprint procore_dashboard_data_bridge",
        ],
        "pseudocode": ["build local project health summary", "write dashboard JSON"],
    },
    {
        "name": "procore_scheduled_export_worker",
        "title": "Scheduled Export Worker Blueprint",
        "description": "Template guidance for scheduled read-only exports.",
        "intended_use": "Cron, launchd, Task Scheduler, or GitHub Actions jobs.",
        "required_environment_variables": _COMMON_ENV,
        "required_pyprocore_capabilities": ["workflow plans", "scheduled exports"],
        "sync_plan": {
            "name": "scheduled_export",
            "description": "Run a local workflow plan on a user-managed schedule.",
            "resources": ["workflow plan", "project context", "AI-ready exports"],
            "output_files": ["exports/nightly/*", "sync_runs/*.jsonl"],
        },
        "local_output_files": ["exports/nightly/manifest.json", "sync_runs/nightly.json"],
        "suggested_deployment_notes": [
            "PyProcore does not schedule jobs automatically.",
            "Use your operating system or CI scheduler.",
        ],
        "test_strategy": ["Validate plan files.", "Run dry-runs before live reads."],
        "example_commands": [
            "procore-sdk workflow-plan validate "
            "examples/workflow_plans/nightly_project_context.json",
        ],
        "pseudocode": [
            "scheduler invokes CLI",
            "workflow plan validates",
            "local outputs are written",
        ],
    },
    {
        "name": "procore_project_health_feed",
        "title": "Project Health Feed Blueprint",
        "description": "Template guidance for local read-only project health snapshots.",
        "intended_use": "Internal reporting, executive summaries, or AI-ready local context packs.",
        "required_environment_variables": _COMMON_ENV,
        "required_pyprocore_capabilities": ["project context", "rfis", "submittals", "daily logs"],
        "sync_plan": {
            "name": "project_health_feed",
            "description": "Write local project health feed files.",
            "resources": ["rfis", "submittals", "daily logs", "observations"],
            "output_files": ["health/project_health.json", "health/project_health.md"],
        },
        "local_output_files": ["health/project_health.json", "health/project_health.md"],
        "suggested_deployment_notes": [
            "Treat health feeds as generated artifacts.",
            "Review permissions before sharing exported content.",
        ],
        "test_strategy": ["Mock resource summaries.", "Assert output contains no tokens."],
        "example_commands": [
            "procore-sdk integrations readiness procore_project_health_feed --output-dir ./health",
        ],
        "pseudocode": ["read project context", "summarize open items", "write local feed"],
    },
]
