"""Build a local readiness report for an integration blueprint.

This example checks local environment/output readiness only. It does not call
Procore and does not require real credentials.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from pyprocore.integrations import (
    build_integration_readiness_report,
    integration_readiness_report_to_markdown,
)


def main() -> None:
    """Print a beginner-friendly readiness report."""
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "exports"
        report = build_integration_readiness_report(
            "procore_to_csv_sync_worker",
            output_dir,
            env={
                "PROCORE_CLIENT_ID": "example-client-id",
                "PROCORE_CLIENT_SECRET": "replace-me",
            },
        )
        print(integration_readiness_report_to_markdown(report))
        print("Tip: warnings are expected until your local .env and output paths are ready.")


if __name__ == "__main__":
    main()
