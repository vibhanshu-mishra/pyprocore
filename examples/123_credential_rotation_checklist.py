"""Print credential rotation guidance without rotating anything."""

from __future__ import annotations

import os

from pyprocore.auth.permissions import (
    build_credential_rotation_checklist,
    explain_credential_rotation,
    explain_sandbox_production_separation,
)


def main() -> None:
    """Show local-only credential rotation guidance."""
    auth_mode = os.getenv("PROCORE_AUTH_MODE", "authorization_code")
    print("Credential rotation checklist")
    print(f"Auth mode: {auth_mode}")
    print(explain_credential_rotation(auth_mode))
    for item in build_credential_rotation_checklist(auth_mode):
        print(f"- {item}")
    print(explain_sandbox_production_separation())
    print("No Procore API calls were made.")


if __name__ == "__main__":
    main()
