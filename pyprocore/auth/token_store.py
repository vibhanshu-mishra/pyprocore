"""Persistent storage for Procore OAuth tokens.

The token store owns file IO only. It validates token payloads, returns
``None`` when no token has been saved yet, and writes updates atomically so a
partial process failure does not corrupt the token file.
"""

from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from pyprocore.core.config import AuthMode
from pyprocore.core.exceptions import AuthenticationError

DEFAULT_EXPIRY_SKEW_SECONDS = 60
DEFAULT_TOKEN_FILE = Path(__file__).resolve().parent / "token_store.json"
TOKEN_STORE_PATH_ENV = "PROCORE_TOKEN_STORE_PATH"
TOKEN_STORE_BACKEND_ENV = "PROCORE_TOKEN_STORE_BACKEND"
SAFE_TOKEN_FILE_MODE = 0o600


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


class TokenStoreDiagnostic(BaseModel):
    """Safe local diagnostic report for a token-store backend."""

    backend_type: str
    description: str
    path: str | None = None
    exists: bool = False
    readable: bool = False
    contains_token: bool = False
    access_token_present: bool = False
    refresh_token_present: bool = False
    auth_mode: str | None = None
    expires_at: int | None = None
    token_status: str = "Unknown"
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    @property
    def is_usable(self) -> bool:
        """Return whether the backend currently contains readable token data."""
        return self.readable and self.contains_token and not self.errors


class TokenStoreBackend(ABC):
    """Interface for safe token-store backends."""

    @abstractmethod
    def load(self) -> StoredToken | None:
        """Load a token, returning ``None`` when no token is present."""

    @abstractmethod
    def save(self, token: StoredToken) -> None:
        """Persist a token."""

    @abstractmethod
    def clear(self) -> None:
        """Clear the stored token."""

    @abstractmethod
    def exists(self) -> bool:
        """Return whether token data exists."""

    @abstractmethod
    def describe(self) -> str:
        """Return a safe backend description."""

    @abstractmethod
    def diagnostics(self) -> TokenStoreDiagnostic:
        """Return safe diagnostics without token values."""


class FileTokenStoreBackend(TokenStoreBackend):
    """File-backed token persistence backend."""

    def __init__(self, path: Path | str | None = None) -> None:
        """Initialize the file backend.

        Args:
            path: Token file path. Defaults to ``auth/token_store.json``.
        """
        self._path = Path(path) if path is not None else _default_token_path()

    @property
    def path(self) -> Path:
        """Return the token store file path."""
        return self._path

    def exists(self) -> bool:
        """Return whether the token file exists and is a file."""
        return self._path.is_file()

    def describe(self) -> str:
        """Return a safe backend description."""
        return f"file token store at {self._path}"

    def load(self) -> StoredToken | None:
        """Load a saved token from disk.

        Returns:
            The saved token, or ``None`` when no token has been stored.

        Raises:
            AuthenticationError: If the token file exists but is unreadable or
                malformed.
        """
        if not self._path.exists():
            return None
        if not self._path.is_file():
            raise AuthenticationError(
                f"Token store path is not a file: {self._path}. Choose a token-store file path."
            )
        if self._path.stat().st_size == 0:
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
                "Token store contains invalid token data. Recreate it using "
                "the configured auth flow."
            ) from exc

    def save(self, token: StoredToken) -> None:
        """Persist a token to disk atomically."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise AuthenticationError(
                f"Unable to create token store directory at {self._path.parent}."
            ) from exc

        temporary_path = self._path.with_name(f".{self._path.name}.{os.getpid()}.tmp")
        payload = json.dumps(token.to_public_dict(), indent=2, sort_keys=True)

        try:
            temporary_path.write_text(f"{payload}\n", encoding="utf-8")
            _chmod_if_supported(temporary_path, SAFE_TOKEN_FILE_MODE)
            temporary_path.replace(self._path)
            _chmod_if_supported(self._path, SAFE_TOKEN_FILE_MODE)
        except OSError as exc:
            temporary_path.unlink(missing_ok=True)
            raise AuthenticationError(
                f"Unable to save token store at {self._path}. Check its "
                "parent directory permissions."
            ) from exc

    def clear(self) -> None:
        """Delete the saved token file when it exists."""
        if self._path.exists() and not self._path.is_file():
            raise AuthenticationError(
                f"Refusing to clear token store because path is not a file: {self._path}."
            )
        try:
            self._path.unlink(missing_ok=True)
        except OSError as exc:
            raise AuthenticationError(
                f"Unable to clear token store at {self._path}. Check file permissions."
            ) from exc

    def diagnostics(self) -> TokenStoreDiagnostic:
        """Return safe file-token-store diagnostics."""
        return inspect_token_store(self._path, backend_type="file")


class MemoryTokenStoreBackend(TokenStoreBackend):
    """In-memory token persistence backend for tests and examples."""

    def __init__(self, token: StoredToken | None = None) -> None:
        """Initialize an in-memory backend with an optional token."""
        self._token = token

    def load(self) -> StoredToken | None:
        """Load the in-memory token."""
        return self._token

    def save(self, token: StoredToken) -> None:
        """Save a token in memory for the life of the process."""
        self._token = token

    def clear(self) -> None:
        """Clear the in-memory token."""
        self._token = None

    def exists(self) -> bool:
        """Return whether an in-memory token exists."""
        return self._token is not None

    def describe(self) -> str:
        """Return a safe backend description."""
        return "memory token store; process-local and not persistent"

    def diagnostics(self) -> TokenStoreDiagnostic:
        """Return safe in-memory diagnostics."""
        token = self._token
        return _diagnostic_from_token(
            token=token,
            backend_type="memory",
            description=self.describe(),
            path=None,
            exists=token is not None,
            readable=True,
            warnings=[
                "Memory token stores are useful for tests/examples only and are not persistent."
            ],
        )


class TokenStore:
    """Token persistence facade for the Procore SDK."""

    def __init__(
        self,
        path: Path | str | None = None,
        backend: TokenStoreBackend | None = None,
    ) -> None:
        """Initialize the token store.

        Args:
            path: Optional file token-store path.
            backend: Optional backend implementation. When provided, ``path``
                is ignored unless the backend itself exposes a path.
        """
        self._backend = backend or FileTokenStoreBackend(path)

    @property
    def path(self) -> Path:
        """Return the token store file path when using a file backend."""
        if isinstance(self._backend, FileTokenStoreBackend):
            return self._backend.path
        return Path("<memory-token-store>")

    @property
    def backend(self) -> TokenStoreBackend:
        """Return the configured token-store backend."""
        return self._backend

    def load(self) -> StoredToken | None:
        """Load a saved token from the configured backend."""
        return self._backend.load()

    def save(self, token: StoredToken) -> None:
        """Persist a token using the configured backend."""
        self._backend.save(token)

    def clear(self) -> None:
        """Clear the configured token backend."""
        self._backend.clear()

    def exists(self) -> bool:
        """Return whether token data exists."""
        return self._backend.exists()

    def describe_backend(self) -> str:
        """Return a safe backend description."""
        return self._backend.describe()

    def diagnostics(self) -> TokenStoreDiagnostic:
        """Return safe backend diagnostics."""
        return self._backend.diagnostics()


def _default_token_path() -> Path:
    """Return the default token path, honoring environment override."""
    configured = os.getenv(TOKEN_STORE_PATH_ENV)
    return Path(configured).expanduser() if configured else DEFAULT_TOKEN_FILE


def _chmod_if_supported(path: Path, mode: int) -> None:
    """Best-effort chmod that is ignored on unsupported platforms."""
    try:
        path.chmod(mode)
    except OSError:
        return


def _diagnostic_from_token(
    *,
    token: StoredToken | None,
    backend_type: str,
    description: str,
    path: str | None,
    exists: bool,
    readable: bool,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> TokenStoreDiagnostic:
    """Build safe diagnostics from an already parsed token."""
    warning_list = list(warnings or [])
    token_status = "Missing"
    if token is not None:
        token_status = "Expired" if token.is_expired(skew_seconds=0) else "Valid"
    return TokenStoreDiagnostic(
        backend_type=backend_type,
        description=description,
        path=path,
        exists=exists,
        readable=readable,
        contains_token=token is not None,
        access_token_present=token is not None and bool(token.access_token.get_secret_value()),
        refresh_token_present=(
            token is not None
            and token.refresh_token is not None
            and bool(token.refresh_token.get_secret_value())
        ),
        auth_mode=token.auth_mode.value if token is not None else None,
        expires_at=token.expires_at if token is not None else None,
        token_status=token_status,
        warnings=warning_list,
        errors=list(errors or []),
    )


def inspect_token_store(
    path: Path | str | None = None,
    *,
    backend_type: str = "file",
) -> TokenStoreDiagnostic:
    """Inspect a file token store without exposing token values.

    Args:
        path: Optional token-store file path.
        backend_type: Safe backend label to include in diagnostics.

    Returns:
        Safe token-store diagnostics.
    """
    token_path = Path(path).expanduser() if path is not None else _default_token_path()
    warnings = explain_token_store_risk(token_path)
    warnings.extend(check_token_store_permissions(token_path))
    description = f"{backend_type} token store at {token_path}"
    exists = token_path.exists()

    if not exists:
        return TokenStoreDiagnostic(
            backend_type=backend_type,
            description=description,
            path=str(token_path),
            exists=False,
            readable=True,
            token_status="Missing",
            warnings=warnings,
        )

    if not token_path.is_file():
        return TokenStoreDiagnostic(
            backend_type=backend_type,
            description=description,
            path=str(token_path),
            exists=True,
            readable=False,
            token_status="Unreadable",
            warnings=warnings,
            errors=["Token store path exists but is not a file."],
        )

    legacy_warning = False
    try:
        raw = json.loads(token_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return TokenStoreDiagnostic(
            backend_type=backend_type,
            description=description,
            path=str(token_path),
            exists=True,
            readable=False,
            token_status="Unreadable",
            warnings=warnings,
            errors=[f"Token store could not be read: {exc}"],
        )
    except json.JSONDecodeError:
        return TokenStoreDiagnostic(
            backend_type=backend_type,
            description=description,
            path=str(token_path),
            exists=True,
            readable=False,
            token_status="Malformed",
            warnings=warnings,
            errors=["Token store contains malformed JSON."],
        )

    if raw == {}:
        return TokenStoreDiagnostic(
            backend_type=backend_type,
            description=description,
            path=str(token_path),
            exists=True,
            readable=True,
            token_status="Empty",
            warnings=warnings,
        )
    if not isinstance(raw, dict):
        return TokenStoreDiagnostic(
            backend_type=backend_type,
            description=description,
            path=str(token_path),
            exists=True,
            readable=False,
            token_status="Malformed",
            warnings=warnings,
            errors=["Token store JSON must be an object."],
        )

    if "auth_mode" not in raw:
        legacy_warning = True

    try:
        token = StoredToken.model_validate(raw)
    except ValueError as exc:
        return TokenStoreDiagnostic(
            backend_type=backend_type,
            description=description,
            path=str(token_path),
            exists=True,
            readable=False,
            token_status="Invalid",
            warnings=warnings,
            errors=[f"Token store contains invalid token metadata: {exc}"],
        )

    if legacy_warning:
        warnings.append(
            "Token store does not include auth_mode metadata; treating it as authorization_code."
        )
    return _diagnostic_from_token(
        token=token,
        backend_type=backend_type,
        description=description,
        path=str(token_path),
        exists=True,
        readable=True,
        warnings=warnings,
    )


def diagnose_token_store(path: Path | str | None = None) -> TokenStoreDiagnostic:
    """Alias for ``inspect_token_store`` for CLI and scripts."""
    return inspect_token_store(path)


def explain_token_store_risk(path: Path | str) -> list[str]:
    """Return safe warnings for risky token-store locations."""
    token_path = Path(path).expanduser()
    warnings: list[str] = []
    project_root = _find_project_root(Path.cwd())
    if project_root is not None and is_path_inside_project(token_path, project_root):
        warnings.append(
            "Token store appears to be inside the repository. Prefer a private path "
            "outside source control."
        )
    if token_path.name in {".env", ".env.local"}:
        warnings.append("Token store path should not be the same file as an environment file.")
    return warnings


def check_token_store_permissions(path: Path | str) -> list[str]:
    """Return warnings for broad file permissions when detectable."""
    token_path = Path(path).expanduser()
    if not token_path.exists() or not token_path.is_file():
        return []
    try:
        mode = token_path.stat().st_mode & 0o777
    except OSError:
        return ["Could not inspect token-store file permissions on this platform."]
    if mode & 0o077:
        return [
            "Token store file permissions appear broader than owner-only. "
            "Prefer chmod 600 where supported."
        ]
    return []


def is_path_inside_project(path: Path | str, project_root: Path | str | None = None) -> bool:
    """Return whether a path is inside a project/repository root."""
    root = Path(project_root) if project_root is not None else _find_project_root(Path.cwd())
    if root is None:
        return False
    candidate = Path(path).expanduser()
    try:
        candidate.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def _find_project_root(start: Path) -> Path | None:
    """Find the nearest Git project root from a starting path."""
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def load_token() -> StoredToken | None:
    """Load the default stored token."""
    return TokenStore().load()


def save_token(token: StoredToken) -> None:
    """Save a token to the default token store."""
    TokenStore().save(token)
