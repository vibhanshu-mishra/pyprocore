"""Authentication utilities for the Procore SDK."""

from __future__ import annotations

from typing import Any

__all__ = [
    "OAuthClient",
    "OAuthTokenResponse",
    "FileTokenStoreBackend",
    "MemoryTokenStoreBackend",
    "StoredToken",
    "TokenStoreBackend",
    "TokenStoreDiagnostic",
    "TokenManager",
    "TokenStore",
    "build_credential_rotation_checklist",
    "check_token_store_permissions",
    "diagnose_token_store",
    "get_access_token",
    "explain_credential_rotation",
    "explain_auth_error",
    "explain_permission_error",
    "explain_app_connection_issue",
    "explain_environment_mismatch",
    "explain_sandbox_production_separation",
    "explain_token_clearance",
    "explain_token_store_risk",
    "inspect_token_store",
    "is_path_inside_project",
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

    if name in {
        "FileTokenStoreBackend",
        "MemoryTokenStoreBackend",
        "StoredToken",
        "TokenStore",
        "TokenStoreBackend",
        "TokenStoreDiagnostic",
        "check_token_store_permissions",
        "diagnose_token_store",
        "explain_token_store_risk",
        "inspect_token_store",
        "is_path_inside_project",
        "load_token",
        "save_token",
    }:
        from pyprocore.auth.token_store import (
            FileTokenStoreBackend,
            MemoryTokenStoreBackend,
            StoredToken,
            TokenStore,
            TokenStoreBackend,
            TokenStoreDiagnostic,
            check_token_store_permissions,
            diagnose_token_store,
            explain_token_store_risk,
            inspect_token_store,
            is_path_inside_project,
            load_token,
            save_token,
        )

        return {
            "FileTokenStoreBackend": FileTokenStoreBackend,
            "MemoryTokenStoreBackend": MemoryTokenStoreBackend,
            "StoredToken": StoredToken,
            "TokenStore": TokenStore,
            "TokenStoreBackend": TokenStoreBackend,
            "TokenStoreDiagnostic": TokenStoreDiagnostic,
            "check_token_store_permissions": check_token_store_permissions,
            "diagnose_token_store": diagnose_token_store,
            "explain_token_store_risk": explain_token_store_risk,
            "inspect_token_store": inspect_token_store,
            "is_path_inside_project": is_path_inside_project,
            "load_token": load_token,
            "save_token": save_token,
        }[name]

    if name in {
        "build_credential_rotation_checklist",
        "explain_credential_rotation",
        "explain_auth_error",
        "explain_permission_error",
        "explain_app_connection_issue",
        "explain_environment_mismatch",
        "explain_sandbox_production_separation",
        "explain_token_clearance",
    }:
        from pyprocore.auth.permissions import (
            build_credential_rotation_checklist,
            explain_app_connection_issue,
            explain_auth_error,
            explain_credential_rotation,
            explain_environment_mismatch,
            explain_permission_error,
            explain_sandbox_production_separation,
            explain_token_clearance,
        )

        return {
            "build_credential_rotation_checklist": build_credential_rotation_checklist,
            "explain_auth_error": explain_auth_error,
            "explain_credential_rotation": explain_credential_rotation,
            "explain_permission_error": explain_permission_error,
            "explain_app_connection_issue": explain_app_connection_issue,
            "explain_environment_mismatch": explain_environment_mismatch,
            "explain_sandbox_production_separation": explain_sandbox_production_separation,
            "explain_token_clearance": explain_token_clearance,
        }[name]

    raise AttributeError(f"module 'auth' has no attribute {name!r}")
