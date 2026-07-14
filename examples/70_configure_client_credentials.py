"""Show how to configure PyProcore for client credentials auth.

This example prints the environment variables used by Procore Data Connection
Apps. It does not request a token and does not call live Procore APIs.
"""

from __future__ import annotations


def main() -> None:
    """Print a safe client credentials configuration template."""
    print("Client credentials auth is for Procore Data Connection Apps.")
    print("Add values like these to your .env file:")
    print()
    print("PROCORE_AUTH_MODE=client_credentials")
    print("PROCORE_CLIENT_ID=your_client_id")
    print("PROCORE_CLIENT_SECRET=your_client_secret_keep_private")
    print("PROCORE_LOGIN_URL=https://login.procore.com")
    print("PROCORE_API_BASE=https://api.procore.com")
    print("PROCORE_COMPANY_ID=your_company_id")
    print()
    print("PROCORE_REDIRECT_URI is not required for client_credentials mode.")


if __name__ == "__main__":
    main()
