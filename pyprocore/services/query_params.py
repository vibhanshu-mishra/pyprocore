"""Shared helpers for service query parameters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def build_query_params(
    *,
    params: Mapping[str, Any] | None,
    extra_params: Mapping[str, Any],
    **filters: Any,
) -> dict[str, Any] | None:
    """Build query parameters, omitting values that are not set.

    Explicit filter keyword arguments override matching keys from ``params`` or
    ``extra_params``.
    """
    query_params = {key: value for key, value in dict(params or {}).items() if value is not None}
    query_params.update({key: value for key, value in extra_params.items() if value is not None})
    query_params.update({key: value for key, value in filters.items() if value is not None})
    return query_params or None
