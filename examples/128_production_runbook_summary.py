"""Print a concise production runbook summary.

This example is local-only and does not call Procore.
"""

from pyprocore.workflows import build_production_runbook_summary


def main() -> None:
    """Run the example."""
    for item in build_production_runbook_summary("client_credentials"):
        print(f"- {item}")


if __name__ == "__main__":
    main()
