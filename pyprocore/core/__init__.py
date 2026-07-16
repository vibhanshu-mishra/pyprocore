"""Core SDK primitives for Procore API access."""

from __future__ import annotations

from typing import Any

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "AsyncProcoreClient",
    "AsyncRequest",
    "AsyncResponse",
    "AsyncTransport",
    "ConfigurationError",
    "DuplicateMatchError",
    "HttpxAsyncTransport",
    "MockAsyncTransport",
    "MultipleResultsError",
    "NotFoundError",
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
        from pyprocore.core.client import ProcoreClient

        return ProcoreClient

    if name == "AsyncProcoreClient":
        from pyprocore.core.async_client import AsyncProcoreClient

        return AsyncProcoreClient

    if name in {
        "AsyncRequest",
        "AsyncResponse",
        "AsyncTransport",
        "HttpxAsyncTransport",
        "MockAsyncTransport",
    }:
        from pyprocore.core import async_transport

        return getattr(async_transport, name)

    if name in {"ProcoreSettings", "get_settings"}:
        from pyprocore.core.config import ProcoreSettings, get_settings

        return {"ProcoreSettings": ProcoreSettings, "get_settings": get_settings}[name]

    if name == "get_logger":
        from pyprocore.core.logger import get_logger

        return get_logger

    exception_names = {
        "AuthenticationError",
        "AuthorizationError",
        "ConfigurationError",
        "DuplicateMatchError",
        "MultipleResultsError",
        "NotFoundError",
        "ProcoreAPIError",
        "ProcoreError",
        "RateLimitError",
        "ResourceNotFoundError",
        "TransientAPIError",
        "ValidationError",
    }
    if name in exception_names:
        from pyprocore.core import exceptions

        return getattr(exceptions, name)

    raise AttributeError(f"module 'core' has no attribute {name!r}")
