"""Local JSON helpers for safe DMSA connection profiles."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import SecretStr
from pydantic import ValidationError as PydanticValidationError

from pyprocore.core.config import AuthMode, ProcoreSettings
from pyprocore.core.exceptions import ConfigurationError, ValidationError
from pyprocore.dmsa.models import (
    DmsaConnectionProfile,
    DmsaConnectionProfileInput,
    DmsaConnectionProfileValidationFinding,
    DmsaConnectionProfileValidationReport,
    DmsaConnectionSummary,
)

_ENV_VAR_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")
_SENSITIVE_ASSIGNMENT = re.compile(
    r"(?i)\b(access[_ -]?token|refresh[_ -]?token|client[_ -]?secret|authorization)"
    r"\s*[:=]\s*\S+"
)


def build_dmsa_connection_profile(
    profile_input: DmsaConnectionProfileInput | None = None,
    **values: Any,
) -> DmsaConnectionProfile:
    """Build a local DMSA profile without resolving or storing credentials."""
    if profile_input is not None and values:
        raise ValidationError("Provide profile_input or keyword values, not both.")
    source = profile_input.model_dump() if profile_input is not None else values
    return DmsaConnectionProfile.model_validate(source)


def load_dmsa_connection_profile(path: str | Path) -> DmsaConnectionProfile:
    """Load a DMSA profile from a local JSON object."""
    source = Path(path).expanduser()
    if source.suffix.casefold() != ".json":
        raise ValidationError("DMSA connection profiles must be local JSON files.")
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValidationError(f"Could not read DMSA profile {source}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"DMSA profile {source} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValidationError("A DMSA profile JSON document must contain an object.")
    try:
        return DmsaConnectionProfile.model_validate(payload)
    except PydanticValidationError as exc:
        raise ValidationError(f"Invalid DMSA profile {source}: {exc}") from exc


def validate_dmsa_connection_profile(
    profile: DmsaConnectionProfile,
) -> DmsaConnectionProfileValidationReport:
    """Validate structural DMSA metadata without reading credentials or calling Procore."""
    findings: list[DmsaConnectionProfileValidationFinding] = []

    def add(
        level: Literal["error", "warning", "info"],
        code: str,
        message: str,
        review: str,
    ) -> None:
        findings.append(
            DmsaConnectionProfileValidationFinding(
                level=level,
                code=code,
                message=message,
                recommended_review=review,
            )
        )

    if profile.company_id is None or profile.company_id <= 0:
        add(
            "error",
            "missing_company_id",
            "A positive GC/Owner company_id is required.",
            "Confirm the company ID with the GC/Owner administrator.",
        )
    for field_name, value in (
        ("client_id_env_var", profile.client_id_env_var),
        ("client_secret_env_var", profile.client_secret_env_var),
    ):
        if not value:
            add(
                "error",
                f"missing_{field_name}",
                f"{field_name} must name an environment variable.",
                "Add an environment-variable name; do not put the credential in JSON.",
            )
        elif not _ENV_VAR_PATTERN.fullmatch(value):
            add(
                "error",
                f"invalid_{field_name}",
                f"{field_name} is not a conventional environment-variable name.",
                "Use uppercase letters, digits, and underscores only.",
            )
    if not profile.allowed_project_ids:
        add(
            "warning",
            "no_allowed_projects",
            "No permitted project IDs are documented in this profile.",
            "Ask the GC/Owner which projects were assigned to the DMSA.",
        )
    if any(project_id <= 0 for project_id in profile.allowed_project_ids):
        add(
            "error",
            "invalid_project_id",
            "All allowed_project_ids must be positive integers.",
            "Remove placeholders and confirm project IDs with the GC/Owner.",
        )
    if profile.token_store_backend == "file" and not profile.token_store_path:
        add(
            "info",
            "default_token_store_path",
            "The default local token-store path will be used.",
            "Set token_store_path when the deployment requires an explicit location.",
        )
    return DmsaConnectionProfileValidationReport(
        profile_name=profile.profile_name,
        valid=not any(item.level == "error" for item in findings),
        findings=findings,
    )


def redact_dmsa_connection_profile(profile: DmsaConnectionProfile) -> dict[str, Any]:
    """Return serialized profile metadata with secret-looking text removed."""

    def redact(value: Any, key: str = "") -> Any:
        key_lower = key.casefold()
        if isinstance(value, dict):
            return {item_key: redact(item, item_key) for item_key, item in value.items()}
        if isinstance(value, list):
            return [redact(item, key) for item in value]
        if isinstance(value, str):
            if (
                any(marker in key_lower for marker in ("secret", "token", "authorization"))
                and not key_lower.endswith("_env_var")
                and key_lower not in {"token_store_backend", "token_store_path"}
            ):
                return "[REDACTED]"
            return _SENSITIVE_ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)
        return value

    return cast(dict[str, Any], redact(profile.model_dump(mode="json")))


def summarize_dmsa_connection_profile(
    profile: DmsaConnectionProfile,
) -> DmsaConnectionSummary:
    """Create a redacted, human-readable profile summary."""
    redacted = redact_dmsa_connection_profile(profile)
    return DmsaConnectionSummary(
        profile_name=profile.profile_name,
        company_id=profile.company_id,
        allowed_project_ids=profile.allowed_project_ids,
        api_base_url=profile.api_base_url,
        login_url=profile.login_url,
        credential_references={
            "client_id_env_var": profile.client_id_env_var,
            "client_secret_env_var": profile.client_secret_env_var,
        },
        token_store_backend=profile.token_store_backend,
        token_store_path=profile.token_store_path,
        created_for=profile.created_for,
        notes=list(redacted["notes"]),
        safety_boundaries=[
            "GC/Owner controls installation, permitted projects, and tool permissions.",
            "Profile loading and validation make no Procore calls.",
            "No Procore write actions are enabled.",
        ],
    )


def write_dmsa_connection_profile_template(
    path: str | Path,
    overwrite: bool = False,
) -> Path:
    """Write a secret-free local JSON profile template."""
    destination = _safe_json_destination(path)
    if destination.exists() and not overwrite:
        raise ValidationError(
            f"Refusing to overwrite existing DMSA profile: {destination}. "
            "Pass overwrite=True explicitly."
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    profile = build_dmsa_connection_profile(
        profile_name="gc-owner-read-only",
        company_id=None,
        allowed_project_ids=[],
        created_for="Your organization",
        notes=["Replace metadata placeholders after GC/Owner installation."],
        app_version_key_reference="Ask the GC/Owner administrator",
    )
    destination.write_text(
        json.dumps(redact_dmsa_connection_profile(profile), indent=2) + "\n",
        encoding="utf-8",
    )
    return destination


def settings_from_dmsa_connection_profile(
    profile: DmsaConnectionProfile,
) -> ProcoreSettings:
    """Resolve profile credential references into existing client-credentials settings."""
    report = validate_dmsa_connection_profile(profile)
    if not report.valid:
        errors = "; ".join(
            finding.message for finding in report.findings if finding.level == "error"
        )
        raise ConfigurationError(f"Invalid DMSA connection profile: {errors}")
    assert profile.company_id is not None
    assert profile.client_id_env_var is not None
    assert profile.client_secret_env_var is not None
    client_id = os.getenv(profile.client_id_env_var)
    client_secret = os.getenv(profile.client_secret_env_var)
    missing = [
        name
        for name, value in (
            (profile.client_id_env_var, client_id),
            (profile.client_secret_env_var, client_secret),
        )
        if not value
    ]
    if missing:
        raise ConfigurationError(
            "Missing DMSA credential environment variables: " + ", ".join(missing)
        )
    assert client_id is not None
    assert client_secret is not None
    return ProcoreSettings(
        client_id=client_id,
        client_secret=SecretStr(client_secret),
        redirect_uri=None,
        login_url=profile.login_url,
        api_base=profile.api_base_url,
        company_id=profile.company_id,
        auth_mode=AuthMode.CLIENT_CREDENTIALS,
        token_store_backend=profile.token_store_backend,
        token_store_path=profile.token_store_path,
    )


def _safe_json_destination(path: str | Path) -> Path:
    """Resolve a local JSON destination and reject parent traversal."""
    candidate = Path(path).expanduser()
    if ".." in candidate.parts:
        raise ValidationError("Parent-directory traversal is not allowed for profile output.")
    if candidate.suffix.casefold() != ".json":
        raise ValidationError("DMSA connection profile templates must use a .json extension.")
    return candidate.resolve()
