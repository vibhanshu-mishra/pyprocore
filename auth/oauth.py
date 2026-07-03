"""OAuth helpers for authenticating with Procore.

The functions in this module exchange authorization codes and refresh tokens
for Procore OAuth access tokens. Configuration is loaded from ``core.config``;
callers never pass client secrets directly.
"""

from __future__ import annotations

from typing import Any

import requests
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from core.config import ProcoreSettings, get_settings
from core.exceptions import AuthenticationError

TOKEN_ENDPOINT_PATH = "/oauth/token"
DEFAULT_TIMEOUT_SECONDS = 30


class OAuthTokenResponse(BaseModel):
    """Validated OAuth token payload returned by Procore."""

    access_token: SecretStr
    token_type: str = Field(default="Bearer", min_length=1)
    expires_in: int = Field(..., gt=0)
    refresh_token: SecretStr | None = None
    scope: str | None = None
    created_at: int | None = None

    model_config = ConfigDict(extra="allow")

    @field_validator("token_type")
    @classmethod
    def _normalize_token_type(cls, value: str) -> str:
        """Normalize token type values for downstream Authorization headers."""
        return value.strip()


class OAuthClient:
    """Client for Procore OAuth token operations."""

    def __init__(
        self,
        settings: ProcoreSettings | None = None,
        session: requests.Session | None = None,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize the OAuth client.

        Args:
            settings: Optional settings instance. Defaults to environment-backed
                settings from ``get_settings()``.
            session: Optional HTTP session. A new ``requests.Session`` is used
                when omitted.
            timeout_seconds: Request timeout for token calls.
        """
        self._settings = settings or get_settings()
        self._session = session or requests.Session()
        self._timeout_seconds = timeout_seconds

    def exchange_authorization_code(
        self, authorization_code: str
    ) -> OAuthTokenResponse:
        """Exchange an OAuth authorization code for access and refresh tokens.

        Args:
            authorization_code: The authorization code returned by Procore.

        Returns:
            A validated OAuth token response.

        Raises:
            AuthenticationError: If the exchange fails or the response is invalid.
        """
        code = authorization_code.strip()
        if not code:
            raise AuthenticationError("Authorization code is required.")

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self._settings.client_id,
            "client_secret": self._settings.client_secret.get_secret_value(),
            "redirect_uri": self._settings.redirect_uri,
        }
        return self._request_token(payload)

    def refresh_access_token(self, refresh_token: str) -> OAuthTokenResponse:
        """Refresh an expired OAuth access token.

        Args:
            refresh_token: The current refresh token.

        Returns:
            A validated OAuth token response.

        Raises:
            AuthenticationError: If the refresh fails or the response is invalid.
        """
        token = refresh_token.strip()
        if not token:
            raise AuthenticationError("Refresh token is required.")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": token,
            "client_id": self._settings.client_id,
            "client_secret": self._settings.client_secret.get_secret_value(),
        }
        return self._request_token(payload)

    def _request_token(self, payload: dict[str, str]) -> OAuthTokenResponse:
        """Send a token request and validate the response."""
        token_url = f"{self._settings.login_url}{TOKEN_ENDPOINT_PATH}"

        try:
            response = self._session.post(
                token_url,
                data=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=self._timeout_seconds,
            )
        except requests.RequestException as exc:
            raise AuthenticationError(f"OAuth token request failed: {exc}") from exc

        if not response.ok:
            raise AuthenticationError(self._format_error_response(response))

        try:
            response_data: dict[str, Any] = response.json()
        except ValueError as exc:
            raise AuthenticationError(
                "OAuth token response was not valid JSON."
            ) from exc

        try:
            return OAuthTokenResponse.model_validate(response_data)
        except ValueError as exc:
            raise AuthenticationError(
                f"OAuth token response was invalid: {exc}"
            ) from exc

    @staticmethod
    def _format_error_response(response: requests.Response) -> str:
        """Build a safe error message without exposing credentials."""
        try:
            body = response.json()
        except ValueError:
            body = response.text

        return f"OAuth token request failed with status {response.status_code}: {body}"


def exchange_authorization_code(authorization_code: str) -> OAuthTokenResponse:
    """Exchange an authorization code using default environment configuration."""
    return OAuthClient().exchange_authorization_code(authorization_code)


def refresh_access_token(refresh_token: str) -> OAuthTokenResponse:
    """Refresh an access token using default environment configuration."""
    return OAuthClient().refresh_access_token(refresh_token)
