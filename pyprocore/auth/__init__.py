"""Authentication utilities for the Procore SDK."""

from __future__ import annotations

from typing import Any

__all__ = [
    "OAuthClient",
    "OAuthTokenResponse",
    "StoredToken",
    "TokenManager",
    "TokenStore",
    "get_access_token",
    "load_token",
    "save_token",
]


def __getattr__(name: str) -> Any:
    """Lazily expose auth objects without creating import cycles."""
    if name in {"OAuthClient", "OAuthTokenResponse"}:
        from pyprocore.auth.oauth import OAuthClient, OAuthTokenResponse

        return {"OAuthClient": OAuthClient, "OAuthTokenResponse": OAuthTokenResponse}[name]

    if name in {"TokenManager", "get_access_token"}:
        from pyprocore.auth.token_manager import TokenManager, get_access_token

        return {"TokenManager": TokenManager, "get_access_token": get_access_token}[name]

    if name in {"StoredToken", "TokenStore", "load_token", "save_token"}:
        from pyprocore.auth.token_store import StoredToken, TokenStore, load_token, save_token

        return {
            "StoredToken": StoredToken,
            "TokenStore": TokenStore,
            "load_token": load_token,
            "save_token": save_token,
        }[name]

    raise AttributeError(f"module 'auth' has no attribute {name!r}")
