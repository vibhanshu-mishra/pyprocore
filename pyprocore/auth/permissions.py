"""Local-only explanations for Procore authentication and permission errors."""

from __future__ import annotations

import json
from typing import Any

from pyprocore.core.config import AuthMode, normalize_auth_mode


def _safe_error_summary(response_body: Any) -> str | None:
    """Extract a short message while excluding token and secret fields."""
    if isinstance(response_body, str):
        text = response_body.strip()
        return text[:240] if text and "token" not in text.casefold() else None
    if isinstance(response_body, dict):
        safe = {
            str(key): value
            for key, value in response_body.items()
            if not any(word in str(key).casefold() for word in ("token", "secret", "authorization"))
        }
        for key in ("message", "error", "error_description", "detail"):
            value = safe.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:240]
        if safe:
            return json.dumps(safe, default=str)[:240]
    return None


def explain_auth_error(status_code: int, response_body: Any = None, auth_mode: Any = None) -> str:
    """Explain supplied HTTP auth data without making a network request."""
    mode = normalize_auth_mode(auth_mode)
    if status_code == 401:
        renewal = (
            "PyProcore requests a new access token; client-credentials tokens "
            "do not need a refresh token."
            if mode is AuthMode.CLIENT_CREDENTIALS
            else (
                "Reauthorize if the access token is expired and no usable "
                "refresh token is stored."
            )
        )
        explanation = (
            "401 Unauthorized usually means a missing, expired, malformed, or "
            f"wrong-environment token. {renewal}"
        )
    elif status_code == 403:
        explanation = explain_permission_error(status_code, response_body, mode)
    else:
        explanation = (
            f"HTTP {status_code} is not a standard OAuth authentication status; "
            "inspect the safe server message and request context."
        )
    summary = _safe_error_summary(response_body)
    return f"{explanation} Server message: {summary}" if summary else explanation


def explain_permission_error(
    status_code: int, response_body: Any = None, auth_mode: Any = None
) -> str:
    """Explain likely local permission causes from supplied response data."""
    mode = normalize_auth_mode(auth_mode)
    if status_code != 403:
        return explain_auth_error(status_code, response_body, mode)
    principal = (
        "the Data Connection App/service account"
        if mode is AuthMode.CLIENT_CREDENTIALS
        else "the authenticated user"
    )
    return (
        f"403 Forbidden usually means {principal} lacks company, project, or tool access, "
        "or the app is not connected to the company. Confirm the app-company "
        "connection and Procore permissions."
    )


def explain_app_connection_issue(auth_mode: Any = None) -> str:
    """Explain app-company connection requirements."""
    mode = normalize_auth_mode(auth_mode)
    if mode is AuthMode.CLIENT_CREDENTIALS:
        return (
            "Client Credentials access requires the Data Connection App to be "
            "installed/connected for the target company and its service account "
            "to have the required permissions."
        )
    return (
        "Authorization Code access depends on the installed app configuration "
        "and the authenticated user's company, project, and tool permissions."
    )


def explain_environment_mismatch(login_url: str | None, api_base: str | None) -> str:
    """Explain a likely sandbox/production mismatch using URLs only."""
    sandbox_markers = ("sandbox", "monthly")
    appears_mixed = any(
        marker in (login_url or "").casefold() for marker in sandbox_markers
    ) != any(marker in (api_base or "").casefold() for marker in sandbox_markers)
    if appears_mixed:
        return (
            "The configured login and API URLs appear to target different "
            "environments. Sandbox credentials and URLs must stay together, as "
            "must production credentials and URLs."
        )
    return (
        "Confirm that the credentials, login URL, API URL, and target company "
        "all belong to the same Procore environment (sandbox or production)."
    )
