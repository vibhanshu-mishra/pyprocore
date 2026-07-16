"""Persistent storage for Procore OAuth tokens.

The token store owns file IO only. It validates token payloads, returns
``None`` when no token has been saved yet, and writes updates atomically so a
partial process failure does not corrupt the token file.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from pyprocore.core.config import AuthMode
from pyprocore.core.exceptions import AuthenticationError

DEFAULT_EXPIRY_SKEW_SECONDS = 60
DEFAULT_TOKEN_FILE = Path(__file__).resolve().parent / "token_store.json"


class StoredToken(BaseModel):
    """OAuth token data persisted by the SDK."""

    access_token: SecretStr
    expires_at: int = Field(..., gt=0)
    refresh_token: SecretStr | None = None
    token_type: str = Field(default="Bearer", min_length=1)
    scope: str | None = None
    auth_mode: AuthMode = AuthMode.AUTHORIZATION_CODE

    model_config = ConfigDict(extra="allow")

    @field_validator("token_type")
    @classmethod
    def _normalize_token_type(cls, value: str) -> str:
        """Normalize token type values for Authorization headers."""
        return value.strip()

    @classmethod
    def from_oauth_response(
        cls,
        token_response: Any,
        existing_refresh_token: str | None = None,
        auth_mode: AuthMode = AuthMode.AUTHORIZATION_CODE,
    ) -> "StoredToken":
        """Create a stored token from an OAuth response model or mapping.

        Args:
            token_response: OAuth response returned by ``auth.oauth``.
            existing_refresh_token: Refresh token to reuse if a refresh response
                does not include a replacement.

        Returns:
            A validated token suitable for persistence.
        """
        if isinstance(token_response, BaseModel):
            payload = token_response.model_dump(mode="python")
        else:
            payload = dict(token_response)

        raw_refresh_token = payload.get("refresh_token") or existing_refresh_token
        refresh_token = (
            raw_refresh_token
            if isinstance(raw_refresh_token, SecretStr) or raw_refresh_token is None
            else SecretStr(str(raw_refresh_token))
        )
        expires_in = int(payload["expires_in"])

        return cls(
            access_token=payload["access_token"],
            refresh_token=refresh_token,
            token_type=payload.get("token_type", "Bearer"),
            scope=payload.get("scope"),
            auth_mode=auth_mode,
            expires_at=int(time.time()) + expires_in,
        )

    def is_expired(self, skew_seconds: int = DEFAULT_EXPIRY_SKEW_SECONDS) -> bool:
        """Return whether the token is expired or inside the refresh window."""
        return int(time.time()) >= self.expires_at - skew_seconds

    def to_public_dict(self) -> dict[str, Any]:
        """Serialize token values for local persistence."""
        data = self.model_dump(mode="json")
        data["access_token"] = self.access_token.get_secret_value()
        if self.refresh_token is not None:
            data["refresh_token"] = self.refresh_token.get_secret_value()
        return data


class TokenStore:
    """File-backed token persistence for the Procore SDK."""

    def __init__(self, path: Path | str = DEFAULT_TOKEN_FILE) -> None:
        """Initialize the store.

        Args:
            path: Token file path. Defaults to ``auth/token_store.json``.
        """
        self._path = Path(path)

    @property
    def path(self) -> Path:
        """Return the token store file path."""
        return self._path

    def load(self) -> StoredToken | None:
        """Load a saved token from disk.

        Returns:
            The saved token, or ``None`` when no token has been stored.

        Raises:
            AuthenticationError: If the token file exists but is unreadable or
                malformed.
        """
        if not self._path.exists() or self._path.stat().st_size == 0:
            return None

        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise AuthenticationError(
                f"Unable to read token store at {self._path}. Check that the file is readable."
            ) from exc
        except json.JSONDecodeError as exc:
            raise AuthenticationError("Token store contains invalid JSON.") from exc

        if raw == {}:
            return None

        try:
            return StoredToken.model_validate(raw)
        except ValueError as exc:
            raise AuthenticationError(
                "Token store contains invalid token data. Recreate it using the configured auth flow."
            ) from exc

    def save(self, token: StoredToken) -> None:
        """Persist a token to disk atomically."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._path.with_suffix(f"{self._path.suffix}.tmp")
        payload = json.dumps(token.to_public_dict(), indent=2, sort_keys=True)

        try:
            temporary_path.write_text(f"{payload}\n", encoding="utf-8")
            temporary_path.replace(self._path)
        except OSError as exc:
            temporary_path.unlink(missing_ok=True)
            raise AuthenticationError(
                f"Unable to save token store at {self._path}. Check its parent directory permissions."
            ) from exc

    def clear(self) -> None:
        """Delete the saved token file when it exists."""
        try:
            self._path.unlink(missing_ok=True)
        except OSError as exc:
            raise AuthenticationError(
                f"Unable to clear token store at {self._path}. Check file permissions."
            ) from exc


def load_token() -> StoredToken | None:
    """Load the default stored token."""
    return TokenStore().load()


def save_token(token: StoredToken) -> None:
    """Save a token to the default token store."""
    TokenStore().save(token)
