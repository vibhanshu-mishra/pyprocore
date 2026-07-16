"""Inspect token-store metadata without printing token values."""

from pyprocore.auth.token_store import TokenStore


def safe_status(store: TokenStore) -> dict[str, object]:
    token = store.load()
    return {
        "path": str(store.path),
        "exists": store.path.exists(),
        "auth_mode": token.auth_mode.value if token else None,
        "expired": token.is_expired(skew_seconds=0) if token else None,
        "refresh_token_available": token.refresh_token is not None if token else False,
    }


if __name__ == "__main__":
    print("Pass an explicitly configured TokenStore to safe_status(); no network request is made.")
