"""Request a client credentials token only when explicitly opted in.

By default, this example prints the safe CLI command. To actually request a
token from Procore, set PYPROCORE_RUN_LIVE_EXAMPLE=1 and make sure your `.env`
uses PROCORE_AUTH_MODE=client_credentials.
"""

from __future__ import annotations

import os

from pyprocore.auth.diagnostics import (
    format_client_credentials_result,
    request_client_credentials_token_and_save,
)


def main() -> None:
    """Show or run the client credentials token helper."""
    if os.getenv("PYPROCORE_RUN_LIVE_EXAMPLE") != "1":
        print("This example is safe by default and did not call Procore.")
        print("To request a token manually, run:")
        print("procore-sdk auth client-credentials-token")
        print()
        print("Or opt in to the live example:")
        print("PYPROCORE_RUN_LIVE_EXAMPLE=1 python3 examples/71_client_credentials_token.py")
        return

    result = request_client_credentials_token_and_save()
    print(format_client_credentials_result(result))


if __name__ == "__main__":
    main()
