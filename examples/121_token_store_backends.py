"""Show file and memory token-store backend patterns without live Procore calls."""

from __future__ import annotations

import time
from pathlib import Path

from pyprocore.auth.token_store import MemoryTokenStoreBackend, StoredToken, TokenStore


def main() -> None:
    """Demonstrate safe token-store backend construction."""
    print("PyProcore token-store backend examples")
    print("File backend path example:")
    print(Path("~/.config/pyprocore/token_store.json").expanduser())
    print()

    token = StoredToken(
        access_token="placeholder-access-token",
        refresh_token="placeholder-refresh-token",
        expires_at=int(time.time()) + 3600,
    )
    memory_store = TokenStore(backend=MemoryTokenStoreBackend(token))
    diagnostic = memory_store.diagnostics()
    print("Memory backend diagnostic:")
    print(f"Backend: {diagnostic.backend_type}")
    print(f"Contains token: {diagnostic.contains_token}")
    print("Memory backends are for tests/examples only.")


if __name__ == "__main__":
    main()
