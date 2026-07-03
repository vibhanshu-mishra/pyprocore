"""Core SDK primitives for Procore API access."""

from __future__ import annotations

from typing import Any

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "ConfigurationError",
    "ProcoreAPIError",
    "ProcoreClient",
    "ProcoreError",
    "ProcoreSettings",
    "RateLimitError",
    "ResourceNotFoundError",
    "TransientAPIError",
    "ValidationError",
    "get_logger",
    "get_settings",
]


def __getattr__(name: str) -> Any:
    """Lazily expose core objects without creating import cycles."""
    if name == "ProcoreClient":
        from core.client import ProcoreClient

        return ProcoreClient

    if name in {"ProcoreSettings", "get_settings"}:
        from core.config import ProcoreSettings, get_settings

        return {"ProcoreSettings": ProcoreSettings, "get_settings": get_settings}[name]

    if name == "get_logger":
        from core.logger import get_logger

        return get_logger

    exception_names = {
        "AuthenticationError",
        "AuthorizationError",
        "ConfigurationError",
        "ProcoreAPIError",
        "ProcoreError",
        "RateLimitError",
        "ResourceNotFoundError",
        "TransientAPIError",
        "ValidationError",
    }
    if name in exception_names:
        from core import exceptions

        return getattr(exceptions, name)

    raise AttributeError(f"module 'core' has no attribute {name!r}")
