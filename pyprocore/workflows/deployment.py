"""Local private deployment readiness helpers.

The helpers in this module are intentionally local-only. They inspect paths,
deployment choices, and scheduled-export planning flags, but they never call
Procore, read token values, schedule jobs, or contact external services.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field

from pyprocore.auth.token_store import check_token_store_permissions, is_path_inside_project
from pyprocore.models.base import ProcoreModel

EnterpriseReadinessSeverity = Literal["pass", "info", "warn", "fail"]


class EnterpriseReadinessFinding(ProcoreModel):
    """One local private-deployment readiness finding."""

    severity: EnterpriseReadinessSeverity
    code: str
    message: str
    suggested_action: str | None = None


class EnterpriseReadinessReport(ProcoreModel):
    """Local readiness report for a private PyProcore deployment."""

    environment_name: str | None = None
    auth_mode: str
    token_store_path: Path | None = None
    export_output_dir: Path | None = None
    log_dir: Path | None = None
    scheduled_export_plan_path: Path | None = None
    dry_run_required: bool = True
    findings: list[EnterpriseReadinessFinding] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Return whether the report has no failing findings."""
        return not any(finding.severity == "fail" for finding in self.findings)

    @property
    def warnings(self) -> list[EnterpriseReadinessFinding]:
        """Return warning findings."""
        return [finding for finding in self.findings if finding.severity == "warn"]

    @property
    def failures(self) -> list[EnterpriseReadinessFinding]:
        """Return failing findings."""
        return [finding for finding in self.findings if finding.severity == "fail"]


def build_enterprise_readiness_checklist(auth_mode: str = "client_credentials") -> list[str]:
    """Build a safe private deployment checklist.

    Args:
        auth_mode: Planned authentication mode.

    Returns:
        Plain-English checklist items.
    """
    auth_guidance = (
        "Use Client Credentials / Data Connection App auth for server-to-server jobs."
        if auth_mode == "client_credentials"
        else "Use Authorization Code only for user-driven local workflows."
    )
    return [
        "Choose a named environment such as sandbox, staging, or production.",
        auth_guidance,
        "Keep .env outside source control and restrict access to operators.",
        "Store token files outside the repository with owner-only permissions where possible.",
        "Write exports, logs, downloads, and manifests to private runtime folders.",
        "Validate scheduled export plans before every production rollout.",
        "Run a dry-run before enabling or resuming any schedule.",
        "Confirm company, project, and tool permissions before the first production run.",
        "Keep sandbox and production credentials, token stores, and output folders separate.",
        "Do not enable agent tool execution; Phase 9D remains discovery and guidance only.",
    ]


def evaluate_private_deployment_config(
    *,
    auth_mode: str = "client_credentials",
    token_store_path: Path | str | None = None,
    export_output_dir: Path | str | None = None,
    log_dir: Path | str | None = None,
    environment_name: str | None = None,
    scheduled_export_plan_path: Path | str | None = None,
    dry_run_required: bool = True,
    server_to_server: bool = True,
    repo_root: Path | str | None = None,
) -> EnterpriseReadinessReport:
    """Evaluate local private-deployment configuration choices.

    Args:
        auth_mode: Planned auth mode.
        token_store_path: Local token-store path.
        export_output_dir: Local export output directory.
        log_dir: Local log directory.
        environment_name: Named deployment environment.
        scheduled_export_plan_path: Optional scheduled export plan path.
        dry_run_required: Whether a dry-run is required before production use.
        server_to_server: Whether this is planned as an unattended deployment.
        repo_root: Optional repository root for path safety checks.

    Returns:
        Local readiness report with safe findings.
    """
    findings: list[EnterpriseReadinessFinding] = []
    normalized_auth_mode = auth_mode.strip() if auth_mode else ""
    root = Path(repo_root).resolve() if repo_root is not None else _find_project_root(Path.cwd())

    if not environment_name or not environment_name.strip():
        findings.append(
            EnterpriseReadinessFinding(
                severity="warn",
                code="missing_environment_name",
                message="No environment name was provided.",
                suggested_action="Name the deployment sandbox, staging, or production.",
            )
        )
    elif environment_name.casefold() in {"production", "prod", "sandbox", "staging"}:
        findings.append(
            EnterpriseReadinessFinding(
                severity="pass",
                code="environment_named",
                message=f"Environment is named: {environment_name}.",
            )
        )
    else:
        findings.append(
            EnterpriseReadinessFinding(
                severity="info",
                code="custom_environment_name",
                message=f"Environment is named: {environment_name}.",
            )
        )

    if normalized_auth_mode not in {"authorization_code", "client_credentials"}:
        findings.append(
            EnterpriseReadinessFinding(
                severity="fail",
                code="unsupported_auth_mode",
                message="Auth mode must be authorization_code or client_credentials.",
                suggested_action="Use client_credentials for private scheduled exports.",
            )
        )
    elif server_to_server and normalized_auth_mode != "client_credentials":
        findings.append(
            EnterpriseReadinessFinding(
                severity="warn",
                code="server_to_server_auth_mode",
                message="Server-to-server scheduled exports should use client_credentials.",
                suggested_action="Use a Procore Data Connection App for unattended jobs.",
            )
        )
    else:
        findings.append(
            EnterpriseReadinessFinding(
                severity="pass",
                code="auth_mode_supported",
                message=f"Auth mode is supported: {normalized_auth_mode}.",
            )
        )

    _evaluate_path(
        findings,
        name="token_store_path",
        path=token_store_path,
        repo_root=root,
        private_action="Place token stores outside the repository.",
    )
    if token_store_path is not None:
        for warning in check_token_store_permissions(token_store_path):
            findings.append(
                EnterpriseReadinessFinding(
                    severity="warn",
                    code="token_store_permissions",
                    message=warning,
                    suggested_action=(
                        "Use owner-only permissions such as chmod 600 where supported."
                    ),
                )
            )

    _evaluate_path(
        findings,
        name="export_output_dir",
        path=export_output_dir,
        repo_root=root,
        private_action="Write exports to a private runtime directory outside the repository.",
    )
    _evaluate_path(
        findings,
        name="log_dir",
        path=log_dir,
        repo_root=root,
        private_action="Write logs to a private runtime directory outside the repository.",
    )

    if scheduled_export_plan_path is None:
        findings.append(
            EnterpriseReadinessFinding(
                severity="info",
                code="no_scheduled_export_plan",
                message="No scheduled export plan path was provided.",
            )
        )
    else:
        _evaluate_path(
            findings,
            name="scheduled_export_plan_path",
            path=scheduled_export_plan_path,
            repo_root=root,
            private_action="Keep plan files free of secrets and review them before production use.",
            warn_inside_repo=False,
        )

    if dry_run_required:
        findings.append(
            EnterpriseReadinessFinding(
                severity="pass",
                code="dry_run_required",
                message="Dry-run is required before production execution.",
            )
        )
    else:
        findings.append(
            EnterpriseReadinessFinding(
                severity="warn",
                code="dry_run_not_required",
                message="Scheduled exports are planned without a required dry-run.",
                suggested_action=(
                    "Validate and dry-run every plan before enabling production schedules."
                ),
            )
        )

    if _environment_separation_unclear(environment_name):
        findings.append(
            EnterpriseReadinessFinding(
                severity="warn",
                code="environment_separation_unclear",
                message="Sandbox/production separation is unclear.",
                suggested_action=(
                    "Use separate .env files, token stores, export folders, and logs "
                    "per environment."
                ),
            )
        )
    else:
        findings.append(
            EnterpriseReadinessFinding(
                severity="pass",
                code="environment_separation_guidance",
                message="Environment naming supports sandbox/production separation.",
            )
        )

    findings.append(
        EnterpriseReadinessFinding(
            severity="info",
            code="phase9d_safety_boundary",
            message=(
                "Phase 9D performs local readiness checks only. It does not call Procore, "
                "schedule jobs, call external AI/model APIs, or enable agent tool execution."
            ),
        )
    )
    return EnterpriseReadinessReport(
        environment_name=environment_name,
        auth_mode=normalized_auth_mode or auth_mode,
        token_store_path=Path(token_store_path).expanduser() if token_store_path else None,
        export_output_dir=Path(export_output_dir).expanduser() if export_output_dir else None,
        log_dir=Path(log_dir).expanduser() if log_dir else None,
        scheduled_export_plan_path=(
            Path(scheduled_export_plan_path).expanduser() if scheduled_export_plan_path else None
        ),
        dry_run_required=dry_run_required,
        findings=findings,
    )


def explain_private_deployment_pattern(pattern: str = "local") -> str:
    """Explain a private deployment pattern without provisioning anything."""
    normalized = pattern.strip().casefold().replace("_", "-") if pattern else "local"
    patterns = {
        "local": (
            "Local-only deployment runs PyProcore from an operator workstation. "
            "Use Authorization Code for user-driven workflows or Client Credentials "
            "for repeatable local exports. Keep .env, token stores, logs, downloads, "
            "and exports outside source control."
        ),
        "private-server": (
            "Private server deployment runs PyProcore on infrastructure your team "
            "controls. Use Client Credentials / Data Connection App auth, private "
            "runtime folders, dry-run validation, and external scheduling such as cron."
        ),
        "cron": (
            "Cron deployment uses your operating system scheduler to run an existing "
            "PyProcore command or script. PyProcore does not install cron jobs; validate "
            "and dry-run plans before adding a schedule."
        ),
        "docker": (
            "Docker private export runner deployment packages PyProcore with your "
            "runtime. Mount .env, token-store, logs, and exports as private volumes. "
            "The provided templates are illustrative and do not start hosted services."
        ),
    }
    return patterns.get(
        normalized,
        "Unknown deployment pattern. Supported patterns: local, private-server, cron, docker.",
    )


def build_production_runbook_summary(auth_mode: str = "client_credentials") -> list[str]:
    """Build a concise production runbook summary."""
    auth_line = (
        "Use Client Credentials / Data Connection App auth for unattended exports."
        if auth_mode == "client_credentials"
        else "Use Authorization Code only when a user is intentionally driving the workflow."
    )
    return [
        "Confirm .env, token stores, logs, exports, downloads, and project data are private.",
        auth_line,
        "Run token-store status and enterprise readiness checks before deployment.",
        "Validate scheduled export plans and perform a dry-run.",
        "Review 401/403 guidance before the first production run.",
        "Monitor logs and output manifests after each run.",
        "Rotate credentials with a dry-run before resuming schedules.",
        "If secrets leak, revoke credentials, clear token stores, rotate secrets, and audit logs.",
        "Rollback by disabling the external schedule and restoring the last known good config.",
        "Decommission by disabling schedules, archiving outputs, clearing tokens, "
        "and revoking access.",
    ]


def sample_private_folder_layout(root: Path | str = "/opt/pyprocore") -> str:
    """Return a safe private deployment folder layout example."""
    base = Path(root)
    return "\n".join(
        [
            f"{base}/",
            "  config/",
            "    sandbox.env",
            "    production.env",
            "  token-stores/",
            "    sandbox/token_store.json",
            "    production/token_store.json",
            "  plans/",
            "    nightly_project_context.json",
            "  exports/",
            "    sandbox/",
            "    production/",
            "  logs/",
            "    sandbox/",
            "    production/",
            "",
            "Keep this folder outside your source checkout and restrict access to operators.",
        ]
    )


def _evaluate_path(
    findings: list[EnterpriseReadinessFinding],
    *,
    name: str,
    path: Path | str | None,
    repo_root: Path | None,
    private_action: str,
    warn_inside_repo: bool = True,
) -> None:
    """Add local path safety findings."""
    if path is None:
        findings.append(
            EnterpriseReadinessFinding(
                severity="warn",
                code=f"missing_{name}",
                message=f"No {name.replace('_', ' ')} was provided.",
                suggested_action=private_action,
            )
        )
        return

    candidate = Path(path).expanduser()
    if warn_inside_repo and repo_root is not None and is_path_inside_project(candidate, repo_root):
        findings.append(
            EnterpriseReadinessFinding(
                severity="warn",
                code=f"{name}_inside_repo",
                message=f"{name.replace('_', ' ').title()} appears to be inside the repository.",
                suggested_action=private_action,
            )
        )
    else:
        findings.append(
            EnterpriseReadinessFinding(
                severity="pass",
                code=f"{name}_configured",
                message=f"{name.replace('_', ' ').title()} is configured.",
            )
        )


def _environment_separation_unclear(environment_name: str | None) -> bool:
    """Return whether environment naming is too vague for private deployment."""
    if not environment_name:
        return True
    normalized = environment_name.strip().casefold()
    return normalized in {"default", "local", "dev", "development", "test", "unknown"}


def _find_project_root(start: Path) -> Path | None:
    """Find the nearest Git project root from a starting path."""
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None
