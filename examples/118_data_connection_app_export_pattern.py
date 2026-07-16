"""Show a safe Data Connection App scheduled export pattern.

This example prints the review steps an enterprise team can use before running
real exports. It does not request tokens and does not call Procore.
"""

from __future__ import annotations


def main() -> None:
    """Print a safe server-to-server deployment pattern."""
    print("Data Connection App scheduled export pattern:")
    print("1. Configure client credentials in a private .env on the scheduled host.")
    print("2. Validate the scheduled export plan locally.")
    print("3. Dry-run the plan and review the manifest.")
    print("4. Confirm app, company, project, and tool permissions in Procore.")
    print("5. Run real exports only from private infrastructure.")
    print()
    print("Example:")
    print(
        "  procore-sdk scheduled-export validate examples/configs/scheduled_export_client_credentials.json"
    )
    print(
        "  procore-sdk scheduled-export dry-run examples/configs/scheduled_export_client_credentials.json"
    )


if __name__ == "__main__":
    main()
