"""Compare PyProcore's supported authentication modes.

This example prints a local overview only. It does not inspect credentials,
request tokens, or call live Procore APIs.
"""

from __future__ import annotations


def main() -> None:
    """Print a short auth-mode comparison."""
    print("PyProcore auth modes")
    print()
    print("authorization_code")
    print("- Default mode")
    print("- User grants access in a browser")
    print("- Requires PROCORE_REDIRECT_URI")
    print("- Uses access and refresh tokens")
    print("- Start with: procore-sdk auth login-url")
    print()
    print("client_credentials")
    print("- For Procore Data Connection Apps")
    print("- Server-to-server token request")
    print("- Does not require PROCORE_REDIRECT_URI")
    print("- Refresh token may be absent and is not required")
    print("- Start with: procore-sdk auth client-credentials-token")


if __name__ == "__main__":
    main()
