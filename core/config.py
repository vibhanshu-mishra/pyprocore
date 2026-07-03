"""Application configuration for the Procore SDK.

This module is the single source of truth for environment-backed settings.
Values are loaded from a local ``.env`` file when present and validated before
the rest of the SDK uses them.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, ValidationError, field_validator

from core.exceptions import ConfigurationError

ENV_FILE_NAME = ".env"


class ProcoreSettings(BaseModel):
    """Validated runtime settings for Procore API access."""

    client_id: str = Field(..., min_length=1)
    client_secret: SecretStr
    redirect_uri: str = Field(..., min_length=1)
    login_url: str = Field(..., min_length=1)
    api_base: str = Field(..., min_length=1)
    company_id: int = Field(..., gt=0)

    @field_validator(
        "client_id",
        "client_secret",
        "redirect_uri",
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

    @field_validator("login_url", "api_base")
    @classmethod
    def _normalize_base_url(cls, value: str) -> str:
        """Remove trailing slashes so endpoint paths compose predictably."""
        return value.rstrip("/")


def _project_root() -> Path:
    """Return the project root directory containing this module."""
    return Path(__file__).resolve().parents[1]


def _env_path() -> Path:
    """Return the expected path to the project ``.env`` file."""
    return _project_root() / ENV_FILE_NAME


def _read_environment() -> dict[str, str | None]:
    """Read supported configuration keys from the process environment."""
    return {
        "client_id": os.getenv("PROCORE_CLIENT_ID"),
        "client_secret": os.getenv("PROCORE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("PROCORE_REDIRECT_URI"),
        "login_url": os.getenv("PROCORE_LOGIN_URL"),
        "api_base": os.getenv("PROCORE_API_BASE"),
        "company_id": os.getenv("PROCORE_COMPANY_ID"),
    }


@lru_cache(maxsize=1)
def get_settings() -> ProcoreSettings:
    """Load and validate SDK settings from environment variables.

    Returns:
        A cached ``ProcoreSettings`` instance.

    Raises:
        ConfigurationError: If any required setting is missing or invalid.
    """
    load_dotenv(dotenv_path=_env_path(), override=False)

    try:
        return ProcoreSettings.model_validate(_read_environment())
    except ValidationError as exc:
        raise ConfigurationError(f"Invalid Procore SDK configuration: {exc}") from exc
