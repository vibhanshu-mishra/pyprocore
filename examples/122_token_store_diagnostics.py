"""Inspect token-store safety without printing token values or calling Procore."""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.auth.token_store import inspect_token_store


def main() -> None:
    """Run safe token-store diagnostics."""
    path = Path(os.getenv("PROCORE_TOKEN_STORE_PATH", "pyprocore/auth/token_store.json"))
    result = inspect_token_store(path)
    print("Token-store diagnostics")
    print(f"Path: {result.path}")
    print(f"Exists: {result.exists}")
    print(f"Token status: {result.token_status}")
    print(f"Auth mode: {result.auth_mode or 'unknown'}")
    for warning in result.warnings:
        print(f"Warning: {warning}")
    for error in result.errors:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
