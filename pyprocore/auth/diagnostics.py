"""Beginner-friendly authentication diagnostics and CLI helpers."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

from dotenv import dotenv_values

from pyprocore.auth.oauth import OAuthTokenResponse, exchange_authorization_code
from pyprocore.auth.token_manager import TokenManager
from pyprocore.auth.token_store import StoredToken, TokenStore
from pyprocore.core.config import AuthMode, ProcoreSettings, get_settings, normalize_auth_mode
from pyprocore.core.exceptions import AuthenticationError
from pyprocore.models import ProcoreModel

AUTHORIZATION_ENDPOINT_PATH = "/oauth/authorize"
AUTH_CONFIG_KEYS = (
    "PROCORE_CLIENT_ID",
    "PROCORE_CLIENT_SECRET",
    "PROCORE_REDIRECT_URI",
    "PROCORE_LOGIN_URL",
    "PROCORE_API_BASE",
    "PROCORE_COMPANY_ID",
    "PROCORE_AUTH_MODE",
)
AUTH_CODE_REQUIRED_CONFIG_KEYS = (
    "PROCORE_CLIENT_ID",
    "PROCORE_CLIENT_SECRET",
    "PROCORE_REDIRECT_URI",
    "PROCORE_LOGIN_URL",
    "PROCORE_API_BASE",
    "PROCORE_COMPANY_ID",
)
CLIENT_CREDENTIALS_REQUIRED_CONFIG_KEYS = (
    "PROCORE_CLIENT_ID",
    "PROCORE_CLIENT_SECRET",
    "PROCORE_LOGIN_URL",
    "PROCORE_API_BASE",
    "PROCORE_COMPANY_ID",
)


class AuthStatusReport(ProcoreModel):
    """Safe local authentication status for CLI output."""

    token_store_path: str
    token_store_exists: bool
    token_store_readable: bool
    access_token_present: bool
    refresh_token_present: bool
    expires_at: int | None = None
    expires_at_utc: str | None = None
    token_status: str = "Unknown"
    auth_mode: str = "authorization_code"
    login_url: str | None = None
    redirect_uri: str | None = None
    api_base: str | None = None
    company_id: int | None = None
    missing_configuration: list[str]
    errors: list[str]
    warnings: list[str]

    @property
    def exit_code(self) -> int:
        """Return the CLI exit code for this auth status."""
        if self.errors:
            return 1
        return 0


class AuthRefreshResult(ProcoreModel):
    """Result of refreshing a local OAuth token."""

    success: bool
    message: str
    expires_at: int | None = None
    expires_at_utc: str | None = None
    error: str | None = None

    @property
    def exit_code(self) -> int:
        """Return the CLI exit code for this refresh attempt."""
        return 0 if self.success else 1


class AuthLoginUrlResult(ProcoreModel):
    """Authorization URL and next-step guidance."""

    authorization_url: str
    redirect_uri: str


class AuthExchangeResult(ProcoreModel):
    """Result of exchanging and saving an OAuth authorization code."""

    success: bool
    message: str
    token_store_updated: bool = False
    access_token_present: bool = False
    refresh_token_present: bool = False
    expires_at: int | None = None
    expires_at_utc: str | None = None
    error: str | None = None

    @property
    def exit_code(self) -> int:
        """Return the CLI exit code for this exchange attempt."""
        return 0 if self.success else 1


class AuthClientCredentialsResult(ProcoreModel):
    """Result of requesting and saving a client credentials token."""

    success: bool
    message: str
    token_store_updated: bool = False
    access_token_present: bool = False
    refresh_token_present: bool = False
    token_type: str | None = None
    expires_at: int | None = None
    expires_at_utc: str | None = None
    error: str | None = None

    @property
    def exit_code(self) -> int:
        """Return the CLI exit code for this token request."""
        return 0 if self.success else 1


def get_auth_status(
    *,
    token_store: TokenStore | None = None,
    env_path: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> AuthStatusReport:
    """Inspect local auth configuration and token storage without secrets.

    Args:
        token_store: Optional token store to inspect.
        env_path: Optional ``.env`` file path.
        environ: Optional environment mapping. Defaults to ``os.environ``.

    Returns:
        A safe auth status report suitable for human or JSON output.
    """
    store = token_store or TokenStore()
    environment = os.environ if environ is None else environ
    config = _read_auth_config(
        Path(env_path) if env_path is not None else Path.cwd() / ".env", environment
    )
    mode_error: str | None = None
    try:
        auth_mode = normalize_auth_mode(config.get("PROCORE_AUTH_MODE")).value
    except ValueError as exc:
        auth_mode = str(config.get("PROCORE_AUTH_MODE") or "").strip()
        mode_error = str(exc)
    required_config = _required_config_keys(auth_mode)
    missing_configuration = [key for key in required_config if not config.get(key)]
    errors: list[str] = []
    warnings: list[str] = []

    if mode_error:
        errors.append(mode_error)

    if missing_configuration:
        errors.append("Required auth configuration is missing.")

    token: StoredToken | None = None
    token_store_exists = store.path.exists()
    token_store_readable = False

    if not token_store_exists:
        errors.append("Token store is missing.")
    else:
        try:
            token = store.load()
        except AuthenticationError as exc:
            errors.append(f"Token store is unreadable: {exc}")
        else:
            token_store_readable = True
            if token is None:
                errors.append("Token store does not contain token data.")

    access_token_present = token is not None and bool(token.access_token.get_secret_value())
    refresh_token_present = (
        token is not None
        and token.refresh_token is not None
        and bool(token.refresh_token.get_secret_value())
    )
    if token is not None and not refresh_token_present and auth_mode != "client_credentials":
        warnings.append("Refresh token is missing.")
    if token is not None and token.auth_mode.value != auth_mode and not mode_error:
        warnings.append(
            f"Stored token auth mode is {token.auth_mode.value}; configured auth mode is {auth_mode}."
        )

    expires_at = token.expires_at if token is not None else None
    expires_at_utc = _format_expiry(expires_at)
    token_status = _token_status(token)

    return AuthStatusReport(
        token_store_path=str(store.path),
        token_store_exists=token_store_exists,
        token_store_readable=token_store_readable,
        access_token_present=access_token_present,
        refresh_token_present=refresh_token_present,
        expires_at=expires_at,
        expires_at_utc=expires_at_utc,
        token_status=token_status,
        auth_mode=auth_mode,
        login_url=config.get("PROCORE_LOGIN_URL"),
        redirect_uri=config.get("PROCORE_REDIRECT_URI"),
        api_base=config.get("PROCORE_API_BASE"),
        company_id=_parse_company_id(config.get("PROCORE_COMPANY_ID")),
        missing_configuration=missing_configuration,
        errors=errors,
        warnings=warnings,
    )


def refresh_auth_token(token_manager: TokenManager | None = None) -> AuthRefreshResult:
    """Refresh the stored OAuth access token using existing auth logic.

    Args:
        token_manager: Optional token manager, primarily for tests.

    Returns:
        A safe refresh result that never exposes token values.
    """
    manager = token_manager or TokenManager()
    try:
        token = manager.refresh_token()
    except AuthenticationError as exc:
        return AuthRefreshResult(
            success=False,
            message="Access token refresh failed.",
            error=str(exc),
        )

    return AuthRefreshResult(
        success=True,
        message="Access token refreshed successfully.",
        expires_at=token.expires_at,
        expires_at_utc=_format_expiry(token.expires_at),
    )


def exchange_code_and_save(
    authorization_code: str,
    *,
    token_manager: TokenManager | None = None,
    exchange_func: Callable[[str], OAuthTokenResponse] = exchange_authorization_code,
) -> AuthExchangeResult:
    """Exchange an authorization code and save the returned token.

    Args:
        authorization_code: OAuth authorization code copied from Procore.
        token_manager: Optional token manager, primarily for tests.
        exchange_func: Optional OAuth exchange function, primarily for tests.

    Returns:
        A safe exchange result that never exposes token values.
    """
    code = authorization_code.strip()
    if not code:
        return AuthExchangeResult(
            success=False,
            message="Authorization code exchange failed.",
            error="Authorization code is required.",
        )

    manager = token_manager or TokenManager()
    try:
        token_response = exchange_func(code)
        stored_token = manager.save_oauth_response(token_response)
    except AuthenticationError as exc:
        return AuthExchangeResult(
            success=False,
            message="Authorization code exchange failed.",
            error=str(exc),
        )

    return AuthExchangeResult(
        success=True,
        message="Authorization code exchanged successfully.",
        token_store_updated=True,
        access_token_present=bool(stored_token.access_token.get_secret_value()),
        refresh_token_present=(
            stored_token.refresh_token is not None
            and bool(stored_token.refresh_token.get_secret_value())
        ),
        expires_at=stored_token.expires_at,
        expires_at_utc=_format_expiry(stored_token.expires_at),
    )


def request_client_credentials_token_and_save(
    token_manager: TokenManager | None = None,
) -> AuthClientCredentialsResult:
    """Request and save a client credentials access token.

    Args:
        token_manager: Optional token manager, primarily for tests.

    Returns:
        A safe result that never exposes token values.
    """
    manager = token_manager or TokenManager()
    try:
        stored_token = manager.request_client_credentials_token()
    except AuthenticationError as exc:
        return AuthClientCredentialsResult(
            success=False,
            message="Client credentials token request failed.",
            error=str(exc),
        )

    return AuthClientCredentialsResult(
        success=True,
        message="Client credentials token saved successfully.",
        token_store_updated=True,
        access_token_present=bool(stored_token.access_token.get_secret_value()),
        refresh_token_present=(
            stored_token.refresh_token is not None
            and bool(stored_token.refresh_token.get_secret_value())
        ),
        token_type=stored_token.token_type,
        expires_at=stored_token.expires_at,
        expires_at_utc=_format_expiry(stored_token.expires_at),
    )


def build_authorization_url(settings: ProcoreSettings | None = None) -> AuthLoginUrlResult:
    """Build the Procore OAuth authorization URL.

    Args:
        settings: Optional validated settings. Defaults to environment-backed
            settings from ``get_settings()``.

    Returns:
        Authorization URL and redirect URI.

    Raises:
        ConfigurationError: If required configuration is missing.
    """
    configured = settings or get_settings()
    if configured.auth_mode == "client_credentials":
        raise AuthenticationError(
            "`procore-sdk auth login-url` is only used for authorization-code OAuth. "
            "For client credentials auth, run `procore-sdk auth client-credentials-token`."
        )
    if not configured.redirect_uri:
        raise AuthenticationError(
            "PROCORE_REDIRECT_URI is required for authorization-code OAuth login URLs."
        )
    base_url = configured.login_url.rstrip("/")
    query = urlencode(
        {
            "response_type": "code",
            "client_id": configured.client_id,
            "redirect_uri": configured.redirect_uri,
        }
    )
    return AuthLoginUrlResult(
        authorization_url=f"{base_url}{AUTHORIZATION_ENDPOINT_PATH}?{query}",
        redirect_uri=configured.redirect_uri,
    )


def format_auth_status(report: AuthStatusReport) -> str:
    """Format auth status for human CLI output."""
    lines = [
        "PyProcore Auth Status",
        f"Auth mode: {report.auth_mode}",
        f"Token store: {'Found' if report.token_store_exists else 'Missing'}",
        f"Token store readable: {'Yes' if report.token_store_readable else 'No'}",
        f"Access token: {'Present' if report.access_token_present else 'Missing'}",
        f"Refresh token: {_format_refresh_token_status(report)}",
        f"Expires at: {report.expires_at_utc or 'Unknown'}",
        f"Token status: {report.token_status}",
        f"Login URL: {report.login_url or 'Missing'}",
        f"API base: {report.api_base or 'Missing'}",
        f"Redirect URI: {report.redirect_uri or 'Missing'}",
        f"Company ID: {report.company_id if report.company_id is not None else 'Missing'}",
        f"Token store path: {report.token_store_path}",
    ]
    if report.missing_configuration:
        lines.append(f"Missing configuration: {', '.join(report.missing_configuration)}")

    lines.append("Next step:")
    lines.append(_auth_status_next_step(report))
    lines.append("Permission guidance:")
    lines.append(
        "401 usually indicates a token, credential, expiry, or environment problem. "
        "403 usually indicates company/project/tool permissions or an app-company connection problem."
    )
    if report.auth_mode == "client_credentials":
        lines.append(
            "Client Credentials renews by requesting a new token (not by using refresh_token); "
            "access is controlled by Data Connection App/service-account permissions."
        )
    else:
        lines.append(
            "Authorization Code access is controlled by the authenticated user's permissions."
        )
    lines.append("Sandbox and production credentials, login URLs, and API URLs must match.")
    return "\n".join(lines)


def format_auth_refresh(result: AuthRefreshResult) -> str:
    """Format an auth refresh result for human CLI output."""
    if result.success:
        suffix = f" New expiry: {result.expires_at_utc}." if result.expires_at_utc else ""
        return f"{result.message}{suffix}"

    detail = f"\nDetails: {result.error}" if result.error else ""
    return (
        f"{result.message}{detail}\nNext step: Run `procore-sdk auth login-url` and repeat OAuth."
    )


def format_auth_exchange(result: AuthExchangeResult) -> str:
    """Format an auth exchange result for human CLI output."""
    if result.success:
        return "\n".join(
            [
                result.message,
                f"Token store: {'Updated' if result.token_store_updated else 'Not updated'}",
                f"Refresh token: {'Present' if result.refresh_token_present else 'Missing'}",
                f"Access token: {'Present' if result.access_token_present else 'Missing'}",
                "Next step:",
                "Run `procore-sdk auth status` to confirm your setup.",
            ]
        )

    lines = [
        result.message,
        "Reason:",
        ("Procore rejected the authorization code, or your OAuth " "configuration is incomplete."),
    ]
    if result.error:
        lines.extend(["Details:", result.error])
    lines.extend(
        [
            "Suggested fixes:",
            "- Confirm PROCORE_CLIENT_ID is set.",
            "- Confirm PROCORE_CLIENT_SECRET is set.",
            "- Confirm PROCORE_REDIRECT_URI matches your Procore app settings.",
            "- Generate a fresh authorization code with `procore-sdk auth login-url`.",
        ]
    )
    return "\n".join(lines)


def format_client_credentials_result(result: AuthClientCredentialsResult) -> str:
    """Format a client credentials token result for human CLI output."""
    if result.success:
        lines = [
            result.message,
            f"Token store: {'Updated' if result.token_store_updated else 'Not updated'}",
            f"Access token: {'Present' if result.access_token_present else 'Missing'}",
            f"Refresh token: {'Present' if result.refresh_token_present else 'Not required'}",
        ]
        if result.expires_at_utc:
            lines.append(f"Expires at: {result.expires_at_utc}")
        lines.extend(
            [
                "Next step:",
                "Run `procore-sdk auth status` to confirm your setup.",
            ]
        )
        return "\n".join(lines)

    lines = [
        result.message,
        "Reason:",
        (
            "Procore rejected the client credentials request, "
            "or the local configuration is incomplete."
        ),
    ]
    if result.error:
        lines.extend(["Details:", result.error])
    lines.extend(
        [
            "Suggested fixes:",
            "- Confirm PROCORE_AUTH_MODE=client_credentials.",
            "- Confirm PROCORE_CLIENT_ID is set.",
            "- Confirm PROCORE_CLIENT_SECRET is set.",
            "- Confirm PROCORE_LOGIN_URL matches the Procore environment.",
            "- Confirm the Data Connection App is configured for the target company.",
        ]
    )
    return "\n".join(lines)


def format_login_url(result: AuthLoginUrlResult) -> str:
    """Format an authorization URL with beginner-friendly next steps."""
    return "\n".join(
        [
            "Open this URL in your browser to authorize PyProcore:",
            result.authorization_url,
            "After approving access, Procore will redirect to your redirect URI with a code.",
            "Copy the code value and run `procore-sdk auth exchange-code YOUR_CODE`.",
        ]
    )


def _read_auth_config(env_path: Path, environ: Mapping[str, str]) -> dict[str, str | None]:
    """Read auth configuration from ``.env`` and process environment."""
    dotenv_config = dotenv_values(env_path) if env_path.exists() else {}
    config: dict[str, str | None] = {}
    for key in AUTH_CONFIG_KEYS:
        value = environ.get(key)
        if value is None:
            value = dotenv_config.get(key)
        config[key] = str(value).strip() if value is not None else None
    return config


def _auth_mode(value: str | None) -> str:
    """Return the normalized auth mode used by diagnostics."""
    return normalize_auth_mode(value).value


def _required_config_keys(auth_mode: str) -> tuple[str, ...]:
    """Return required config keys for the selected auth mode."""
    if auth_mode == "client_credentials":
        return CLIENT_CREDENTIALS_REQUIRED_CONFIG_KEYS
    return AUTH_CODE_REQUIRED_CONFIG_KEYS


def _token_status(token: StoredToken | None) -> str:
    """Return a beginner-friendly token status label."""
    if token is None:
        return "Missing"
    if token.is_expired(skew_seconds=0):
        return "Expired"
    return "Valid"


def _format_expiry(expires_at: int | None) -> str | None:
    """Format an epoch expiry timestamp in UTC."""
    if expires_at is None:
        return None
    return datetime.fromtimestamp(expires_at, tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def _parse_company_id(value: str | None) -> int | None:
    """Parse a configured company ID when possible."""
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _auth_status_next_step(report: AuthStatusReport) -> str:
    """Return one practical next step for auth status output."""
    if report.errors:
        if "Token store is missing." in report.errors:
            if report.auth_mode == "client_credentials":
                return "Run `procore-sdk auth client-credentials-token` to save a token."
            return "Run `procore-sdk auth login-url` and complete OAuth once."
        return (
            "Fix the missing or unreadable auth setup above, "
            "then run `procore-sdk auth status` again."
        )
    if not report.refresh_token_present and report.auth_mode != "client_credentials":
        return (
            "Complete the OAuth authorization-code exchange again so PyProcore "
            "can refresh expired tokens automatically."
        )
    if report.token_status == "Expired":
        if report.auth_mode == "client_credentials":
            return "Run `procore-sdk auth client-credentials-token` to request a fresh token."
        return "Run `procore-sdk auth refresh` to refresh the access token."
    return "You are ready to make authenticated SDK calls."


def _format_refresh_token_status(report: AuthStatusReport) -> str:
    """Return a human-readable refresh token status."""
    if report.refresh_token_present:
        return "Present"
    if report.auth_mode == "client_credentials":
        return "Not required"
    return "Missing"
