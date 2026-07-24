"""Configuration helpers for the optional copied FastAPI starter."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """Minimal starter configuration loaded from environment variables."""

    company_id: int | None
    project_id: int | None
    use_fake_client: bool = True


def _optional_int(value: str | None) -> int | None:
    return int(value) if value and value.isdigit() else None


def get_config() -> AppConfig:
    """Return local starter configuration without reading secrets."""
    return AppConfig(
        company_id=_optional_int(os.getenv("PROCORE_COMPANY_ID")),
        project_id=_optional_int(os.getenv("PROCORE_PROJECT_ID")),
        use_fake_client=os.getenv("PYPROCORE_USE_FAKE_CLIENT", "true").casefold() == "true",
    )
