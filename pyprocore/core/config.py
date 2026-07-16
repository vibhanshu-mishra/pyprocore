"""Application configuration for the Procore SDK.

This module is the single source of truth for environment-backed settings.
Values are loaded from a local ``.env`` file when present and validated before
the rest of the SDK uses them.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from enum import StrEnum
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, ValidationError, field_validator, model_validator

from pyprocore.core.exceptions import ConfigurationError

ENV_FILE_NAME = ".env"


class AuthMode(StrEnum):
    """Supported Procore OAuth strategies."""

    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"


def normalize_auth_mode(value: Any) -> AuthMode:
    """Normalize an auth mode or raise a safe, actionable error."""
    if value is None or not str(value).strip():
        return AuthMode.AUTHORIZATION_CODE
    normalized = str(value).strip().casefold().replace("-", "_")
    try:
        return AuthMode(normalized)
    except ValueError as exc:
        supported = ", ".join(mode.value for mode in AuthMode)
        raise ValueError(
            f"Unsupported PROCORE_AUTH_MODE {normalized!r}. Supported modes: {supported}."
        ) from exc


class ProcoreSettings(BaseModel):
    """Validated runtime settings for Procore API access."""

    client_id: str = Field(..., min_length=1)
    client_secret: SecretStr
    redirect_uri: str | None = None
    login_url: str = Field(..., min_length=1)
    api_base: str = Field(..., min_length=1)
    company_id: int = Field(..., gt=0)
    auth_mode: AuthMode = AuthMode.AUTHORIZATION_CODE

    @field_validator(
        "client_id",
        "client_secret",
        "login_url",
        "api_base",
        mode="before",
    )
    @classmethod
    def _strip_required_string(cls, value: Any) -> str:
        """Normalize string values and reject empty input."""
        if value is None:
            raise ValueError("value is required")

        normalized = str(value).strip()
        if not normalized:
            raise ValueError("value cannot be empty")

        return normalized

    @field_validator("redirect_uri", mode="before")
    @classmethod
    def _strip_optional_string(cls, value: Any) -> str | None:
        """Normalize optional string values."""
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @field_validator("auth_mode", mode="before")
    @classmethod
    def _normalize_auth_mode(cls, value: Any) -> AuthMode:
        """Normalize the configured authentication mode."""
        return normalize_auth_mode(value)

    @field_validator("login_url", "api_base")
    @classmethod
    def _normalize_base_url(cls, value: str) -> str:
        """Remove trailing slashes so endpoint paths compose predictably."""
        return value.rstrip("/")

    @model_validator(mode="after")
    def _validate_auth_mode_requirements(self) -> "ProcoreSettings":
        """Validate settings required by the selected auth mode."""
        if self.auth_mode == "authorization_code" and not self.redirect_uri:
            raise ValueError("redirect_uri is required for authorization_code auth mode")
        return self


def _project_root() -> Path:
    """Return the project root directory containing this module."""
    return Path(__file__).resolve().parents[1]


def _env_path() -> Path:
    """Return the expected path to the current working directory ``.env`` file."""
    return Path.cwd() / ENV_FILE_NAME


def _load_dotenv() -> None:
    """Load ``.env`` configuration without overriding real environment variables."""
    loaded = load_dotenv(dotenv_path=_env_path(), override=False)
    if not loaded:
        load_dotenv(dotenv_path=_project_root() / ENV_FILE_NAME, override=False)


def _read_environment() -> dict[str, str | None]:
    """Read supported configuration keys from the process environment."""
    return {
        "client_id": os.getenv("PROCORE_CLIENT_ID"),
        "client_secret": os.getenv("PROCORE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("PROCORE_REDIRECT_URI"),
        "login_url": os.getenv("PROCORE_LOGIN_URL"),
        "api_base": os.getenv("PROCORE_API_BASE"),
        "company_id": os.getenv("PROCORE_COMPANY_ID"),
        "auth_mode": os.getenv("PROCORE_AUTH_MODE"),
    }


@lru_cache(maxsize=1)
def get_settings() -> ProcoreSettings:
    """Load and validate SDK settings from environment variables.

    Returns:
        A cached ``ProcoreSettings`` instance.

    Raises:
        ConfigurationError: If any required setting is missing or invalid.
    """
    _load_dotenv()

    try:
        return ProcoreSettings.model_validate(_read_environment())
    except ValidationError as exc:
        raise ConfigurationError(f"Invalid Procore SDK configuration: {exc}") from exc
