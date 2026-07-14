"""Show a safe automation pattern for client credentials auth.

This example is a local planning aid. It prints the commands you would combine
for scheduled exports after configuring a Data Connection App. It does not call
Procore and does not run workflow plans.
"""

from __future__ import annotations

import os


def main() -> None:
    """Print a beginner-friendly export pattern."""
    plan_path = os.getenv(
        "WORKFLOW_PLAN_PATH",
        "examples/workflow_plans/nightly_project_context.json",
    )
    print("Client credentials scheduled export pattern:")
    print()
    print("1. Configure .env with PROCORE_AUTH_MODE=client_credentials.")
    print("2. Save a token:")
    print("   procore-sdk auth client-credentials-token")
    print("3. Validate the workflow plan without live writes:")
    print(f"   procore-sdk workflow-plan validate {plan_path}")
    print("4. Dry-run first:")
    print(f"   procore-sdk workflow-plan run {plan_path} --dry-run")
    print("5. Run for real only after reviewing output and permissions.")


if __name__ == "__main__":
    main()
