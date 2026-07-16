"""Local diagnostics for PyProcore setup."""

from __future__ import annotations

import importlib
import json
import os
import sys
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from dotenv import dotenv_values

from pyprocore.auth.token_store import DEFAULT_TOKEN_FILE, inspect_token_store
from pyprocore.core.config import normalize_auth_mode
from pyprocore.core.exceptions import ProcoreError
from pyprocore.models import ProcoreModel

CheckStatus = Literal["pass", "warn", "fail"]

CONFIG_ENV_VARS = (
    "PROCORE_CLIENT_ID",
    "PROCORE_CLIENT_SECRET",
    "PROCORE_REDIRECT_URI",
    "PROCORE_LOGIN_URL",
    "PROCORE_API_BASE",
    "PROCORE_COMPANY_ID",
    "PROCORE_AUTH_MODE",
)
AUTH_CODE_REQUIRED_ENV_VARS = (
    "PROCORE_CLIENT_ID",
    "PROCORE_CLIENT_SECRET",
    "PROCORE_REDIRECT_URI",
    "PROCORE_LOGIN_URL",
    "PROCORE_API_BASE",
    "PROCORE_COMPANY_ID",
)
CLIENT_CREDENTIALS_REQUIRED_ENV_VARS = (
    "PROCORE_CLIENT_ID",
    "PROCORE_CLIENT_SECRET",
    "PROCORE_LOGIN_URL",
    "PROCORE_API_BASE",
    "PROCORE_COMPANY_ID",
)

RUNTIME_DEPENDENCIES = ("requests", "dotenv", "pydantic", "tenacity")


class DoctorCheck(ProcoreModel):
    """One local setup diagnostic result."""

    name: str
    status: CheckStatus
    message: str
    details: str | None = None
    suggested_fix: str | None = None


class DoctorSummary(ProcoreModel):
    """Aggregated doctor result counts."""

    passed: int
    warnings: int
    failed: int


class DoctorReport(ProcoreModel):
    """Complete PyProcore doctor report."""

    checks: list[DoctorCheck]
    summary: DoctorSummary
    live: bool = False

    @property
    def exit_code(self) -> int:
        """Return the process exit code represented by this report."""
        return 1 if self.summary.failed else 0


def run_doctor(
    *,
    live: bool = False,
    env_path: Path | str | None = None,
    token_store_path: Path | str = DEFAULT_TOKEN_FILE,
    logs_dir: Path | str = "logs",
    downloads_dir: Path | str = "downloads",
    environ: Mapping[str, str] | None = None,
    live_check: Callable[[], object] | None = None,
) -> DoctorReport:
    """Run local PyProcore setup diagnostics.

    Args:
        live: Whether to include an authenticated Procore connectivity check.
        env_path: Optional path to the local ``.env`` file.
        token_store_path: Path to the OAuth token store.
        logs_dir: Directory used by SDK logs.
        downloads_dir: Directory used for downloaded files.
        environ: Environment mapping to inspect. Defaults to ``os.environ``.
        live_check: Optional callable used to perform a live API check.

    Returns:
        Structured diagnostics and summary counts.
    """
    resolved_env_path = Path(env_path) if env_path is not None else Path.cwd() / ".env"
    resolved_token_path = Path(token_store_path)
    environment = os.environ if environ is None else environ
    config_values = _read_config_values(resolved_env_path, environment)

    checks: list[DoctorCheck] = []
    checks.extend(_configuration_checks(resolved_env_path, config_values))
    checks.extend(_token_checks(resolved_token_path))
    checks.extend(
        _filesystem_checks(
            logs_dir=Path(logs_dir),
            downloads_dir=Path(downloads_dir),
            token_store_path=resolved_token_path,
        )
    )
    checks.extend(_package_checks())

    if live:
        checks.append(_live_api_check(live_check))

    return _build_report(checks, live=live)


def format_doctor_report(report: DoctorReport) -> str:
    """Format a doctor report for human CLI output.

    Args:
        report: Structured doctor report.

    Returns:
        A readable multi-line report.
    """
    lines = ["PyProcore Doctor"]
    for check in report.checks:
        lines.append(f"{check.status.upper():<5} {check.name}: {check.message}")
        if check.details:
            lines.append(f"      Details: {check.details}")
        if check.suggested_fix:
            lines.append(f"      Suggested fix: {check.suggested_fix}")

    lines.append(
        "Summary: "
        f"{report.summary.passed} passed, "
        f"{report.summary.warnings} warning"
        f"{'' if report.summary.warnings == 1 else 's'}, "
        f"{report.summary.failed} failed"
    )

    suggested_steps = [
        check.suggested_fix
        for check in report.checks
        if check.status in {"warn", "fail"} and check.suggested_fix
    ]
    if suggested_steps:
        lines.append("Suggested next step:")
        lines.append(suggested_steps[0])

    return "\n".join(lines)


def _read_config_values(env_path: Path, environ: Mapping[str, str]) -> dict[str, str | None]:
    """Read Procore configuration from ``.env`` and process environment."""
    dotenv_config = dotenv_values(env_path) if env_path.exists() else {}
    values: dict[str, str | None] = {}

    for key in CONFIG_ENV_VARS:
        raw_value = environ.get(key)
        if raw_value is None:
            raw_value = dotenv_config.get(key)
        values[key] = str(raw_value).strip() if raw_value is not None else None

    return values


def _configuration_checks(
    env_path: Path, config_values: Mapping[str, str | None]
) -> list[DoctorCheck]:
    """Return checks for local configuration values."""
    checks = [
        _check(
            "Environment file",
            "pass" if env_path.exists() else "warn",
            ".env file found." if env_path.exists() else ".env file was not found.",
            details=str(env_path),
            suggested_fix=(
                None
                if env_path.exists()
                else "Create a .env file or export the required PROCORE_* variables."
            ),
        )
    ]

    try:
        auth_mode = normalize_auth_mode(config_values.get("PROCORE_AUTH_MODE")).value
    except ValueError as exc:
        checks.append(
            _check(
                "Auth mode",
                "fail",
                "Configured authentication mode is unsupported.",
                details=str(exc),
                suggested_fix="Set PROCORE_AUTH_MODE to authorization_code or client_credentials.",
            )
        )
        return checks
    checks.append(
        _check(
            "Auth mode",
            "pass",
            auth_mode,
            details=(
                "Authorization-code OAuth"
                if auth_mode == "authorization_code"
                else "Client credentials / Data Connection App"
            ),
        )
    )

    required_keys = _required_env_vars(auth_mode)
    missing_keys = [key for key in required_keys if not config_values.get(key)]
    checks.append(
        _check(
            "Required configuration",
            "fail" if missing_keys else "pass",
            (
                "All required Procore configuration values are present."
                if not missing_keys
                else "Some required Procore configuration values are missing."
            ),
            details=", ".join(missing_keys) if missing_keys else None,
            suggested_fix=(
                None
                if not missing_keys
                else "Add the missing PROCORE_* values to .env or your shell environment."
            ),
        )
    )

    for key, label in (
        ("PROCORE_API_BASE", "PROCORE_API_BASE URL"),
        ("PROCORE_LOGIN_URL", "PROCORE_LOGIN_URL URL"),
    ):
        value = config_values.get(key)
        if value:
            checks.append(_url_check(label, value))

    return checks


def _token_checks(token_store_path: Path) -> list[DoctorCheck]:
    """Return checks for local OAuth token storage."""
    if not token_store_path.exists():
        return [
            _check(
                "Token store",
                "fail",
                "Token store file was not found.",
                details=str(token_store_path),
                suggested_fix="Complete OAuth once so PyProcore can save a token store.",
            )
        ]

    checks = [
        _check(
            "Token store",
            "pass",
            "Token store file found.",
            details=str(token_store_path),
        )
    ]

    try:
        raw_token = json.loads(token_store_path.read_text(encoding="utf-8"))
    except OSError as exc:
        checks.append(
            _check(
                "Token store readable",
                "fail",
                "Token store could not be read.",
                details=str(exc),
                suggested_fix="Check file permissions for the token store.",
            )
        )
        return checks
    except json.JSONDecodeError:
        checks.append(
            _check(
                "Token store readable",
                "fail",
                "Token store is not valid JSON.",
                suggested_fix="Run the OAuth flow again to recreate the token store.",
            )
        )
        return checks

    if not isinstance(raw_token, dict) or not raw_token:
        checks.append(
            _check(
                "Token data",
                "fail",
                "Token store does not contain token data.",
                suggested_fix="Run the OAuth flow again to save fresh tokens.",
            )
        )
        return checks

    checks.append(_token_presence_check(raw_token, "access_token", "Access token", required=True))
    token_auth_mode = str(raw_token.get("auth_mode") or "authorization_code")
    refresh_required = token_auth_mode != "client_credentials"
    checks.append(
        _token_presence_check(
            raw_token,
            "refresh_token",
            "Refresh token",
            required=False,
            client_credentials_optional=not refresh_required,
        )
    )
    checks.append(_token_expiry_check(raw_token))
    diagnostics = inspect_token_store(token_store_path)
    for warning in diagnostics.warnings:
        checks.append(
            _check(
                "Token store safety",
                "warn",
                warning,
                suggested_fix=(
                    "Move token stores outside the repository and restrict file permissions."
                ),
            )
        )
    return checks


def _filesystem_checks(
    *,
    logs_dir: Path,
    downloads_dir: Path,
    token_store_path: Path,
) -> list[DoctorCheck]:
    """Return checks for SDK-writable local directories."""
    return [
        _writable_directory_check("logs directory", logs_dir),
        _writable_directory_check("downloads directory", downloads_dir),
        _writable_directory_check("Token store parent", token_store_path.parent),
    ]


def _package_checks() -> list[DoctorCheck]:
    """Return checks for Python and package imports."""
    version = sys.version_info
    python_ok = version >= (3, 12)
    checks = [
        _check(
            "Python version",
            "pass" if python_ok else "fail",
            f"{version.major}.{version.minor}.{version.micro}",
            suggested_fix=None if python_ok else "Use Python 3.12 or newer.",
        ),
        _package_version_check(),
    ]

    for dependency in RUNTIME_DEPENDENCIES:
        checks.append(_dependency_check(dependency))

    return checks


def _live_api_check(live_check: Callable[[], object] | None) -> DoctorCheck:
    """Run the optional authenticated API check."""
    check = live_check or _default_live_check
    try:
        check()
    except ProcoreError as exc:
        return _check(
            "Live Procore API check",
            "fail",
            "Authenticated Procore request failed.",
            details=str(exc),
            suggested_fix="Review the failed check above, then retry `procore-sdk doctor --live`.",
        )
    except Exception as exc:  # pragma: no cover - defensive normalization
        return _check(
            "Live Procore API check",
            "fail",
            "Unexpected error during the live Procore check.",
            details=str(exc),
        )

    return _check(
        "Live Procore API check",
        "pass",
        "Authenticated Procore request succeeded.",
    )


def _default_live_check() -> object:
    """Run the lightest existing authenticated service call."""
    from pyprocore.services import list_companies

    return list_companies()


def _url_check(name: str, value: str) -> DoctorCheck:
    """Validate that a configuration value looks like an HTTP URL."""
    parsed = urlparse(value)
    ok = parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    return _check(
        name,
        "pass" if ok else "fail",
        "Looks like a valid URL." if ok else "Does not look like a valid URL.",
        details=None if ok else _mask_secret(value),
        suggested_fix=None if ok else "Use a full URL such as https://api.procore.com.",
    )


def _token_presence_check(
    raw_token: Mapping[str, object],
    key: str,
    name: str,
    *,
    required: bool,
    client_credentials_optional: bool = False,
) -> DoctorCheck:
    """Return a safe presence-only token check."""
    present = bool(raw_token.get(key))
    if present:
        return _check(name, "pass", f"{name} is present.")

    if client_credentials_optional:
        return _check(
            name,
            "pass",
            f"{name} is not required for client credentials auth.",
        )

    return _check(
        name,
        "fail" if required else "warn",
        f"{name} is missing.",
        suggested_fix="Run the OAuth authorization-code exchange again.",
    )


def _token_expiry_check(raw_token: Mapping[str, object]) -> DoctorCheck:
    """Return a token expiry parsing and freshness check."""
    raw_expiry = raw_token.get("expires_at")
    if raw_expiry is None:
        return _check(
            "Token expiry",
            "warn",
            "Token expiry was not found.",
            suggested_fix="Run the OAuth flow again so token expiry can be stored.",
        )

    if not isinstance(raw_expiry, int | float | str):
        return _check(
            "Token expiry",
            "fail",
            "Token expiry could not be parsed.",
            suggested_fix="Run the OAuth flow again to save a fresh token store.",
        )

    try:
        expires_at = int(raw_expiry)
    except ValueError:
        return _check(
            "Token expiry",
            "fail",
            "Token expiry could not be parsed.",
            suggested_fix="Run the OAuth flow again to save a fresh token store.",
        )

    if expires_at <= int(time.time()):
        auth_mode = str(raw_token.get("auth_mode") or "authorization_code")
        refresh_present = bool(raw_token.get("refresh_token"))
        if auth_mode == "client_credentials":
            return _check(
                "Token expiry",
                "warn",
                "Client credentials access token is expired.",
                suggested_fix=(
                    "Run `procore-sdk auth client-credentials-token` "
                    "or any SDK command that requests a fresh token."
                ),
            )
        return _check(
            "Token expiry",
            "warn" if refresh_present else "fail",
            "Access token is expired.",
            suggested_fix=(
                "Run a PyProcore command so the SDK can refresh the token."
                if refresh_present
                else "Run the OAuth flow again because no refresh token is available."
            ),
        )

    return _check("Token expiry", "pass", "Access token is not expired.")


def _writable_directory_check(name: str, directory: Path) -> DoctorCheck:
    """Check that a directory can be created and written to."""
    test_path = directory / ".pyprocore_write_test"
    try:
        directory.mkdir(parents=True, exist_ok=True)
        test_path.write_text("ok", encoding="utf-8")
        test_path.unlink(missing_ok=True)
    except OSError as exc:
        return _check(
            name,
            "fail",
            "Directory is not writable.",
            details=f"{directory}: {exc}",
            suggested_fix="Choose a writable directory or update local file permissions.",
        )

    return _check(name, "pass", "Directory is writable.", details=str(directory))


def _package_version_check() -> DoctorCheck:
    """Return a check for the imported PyProcore version."""
    try:
        package = importlib.import_module("pyprocore")
        version = getattr(package, "__version__")
    except (ImportError, AttributeError):
        return _check(
            "PyProcore version",
            "warn",
            "Could not detect the imported pyprocore version.",
        )

    return _check("PyProcore version", "pass", str(version))


def _dependency_check(module_name: str) -> DoctorCheck:
    """Return a check for an importable runtime dependency."""
    try:
        importlib.import_module(module_name)
    except ImportError:
        return _check(
            f"Dependency: {module_name}",
            "fail",
            "Required runtime dependency is not importable.",
            suggested_fix="Reinstall PyProcore with its runtime dependencies.",
        )

    return _check(f"Dependency: {module_name}", "pass", "Importable.")


def _auth_mode(value: str | None) -> str:
    """Return the normalized auth mode used by doctor checks."""
    return normalize_auth_mode(value).value


def _required_env_vars(auth_mode: str) -> tuple[str, ...]:
    """Return required environment variables for the selected auth mode."""
    if auth_mode == "client_credentials":
        return CLIENT_CREDENTIALS_REQUIRED_ENV_VARS
    return AUTH_CODE_REQUIRED_ENV_VARS


def _build_report(checks: list[DoctorCheck], *, live: bool) -> DoctorReport:
    """Build a report and summary counts from checks."""
    summary = DoctorSummary(
        passed=sum(1 for check in checks if check.status == "pass"),
        warnings=sum(1 for check in checks if check.status == "warn"),
        failed=sum(1 for check in checks if check.status == "fail"),
    )
    return DoctorReport(checks=checks, summary=summary, live=live)


def _check(
    name: str,
    status: CheckStatus,
    message: str,
    *,
    details: str | None = None,
    suggested_fix: str | None = None,
) -> DoctorCheck:
    """Create one diagnostic check."""
    return DoctorCheck(
        name=name,
        status=status,
        message=message,
        details=details,
        suggested_fix=suggested_fix,
    )


def _mask_secret(value: str) -> str:
    """Return a redacted representation of a sensitive or user-provided value."""
    if len(value) <= 4:
        return "****"
    return f"{value[:2]}...{value[-2:]}"
