"""Demonstrate safe token-store clearance using a temporary example file."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

from pyprocore.auth.token_store import StoredToken, TokenStore


def main() -> None:
    """Create and clear a temporary token store."""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "token_store.json"
        store = TokenStore(path)
        store.save(
            StoredToken(
                access_token="placeholder-access-token",
                refresh_token="placeholder-refresh-token",
                expires_at=int(time.time()) + 3600,
            )
        )
        print(f"Temporary token store created: {path.exists()}")
        store.clear()
        print(f"Temporary token store cleared: {not path.exists()}")
    print("This example does not touch your real token store.")


if __name__ == "__main__":
    main()
