"""Build an AI-ready Procore project context package.

Set PROCORE_PROJECT_ID before running. Optionally set PROCORE_COMPANY_ID and
PROCORE_OUTPUT_DIR. File downloads are off by default to keep the package light.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import build_project_context_package


def main() -> None:
    """Run the project context package example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "project-context"))
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        result = build_project_context_package(
            int(project_id),
            company_id=int(company_id) if company_id else None,
            output_dir=output_dir,
            max_items=50,
        )
    except ValueError:
        print("Project and company IDs must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not build the project context package: {exc}")
        return

    print(f"Project context package created: {result.output_dir}")
    print(f"Manifest: {result.manifest_path}")
    print(f"Summary: {result.summary_path}")
    if result.manifest.errors:
        print("Some sections had errors. Check errors.json and manifest.json.")


if __name__ == "__main__":
    main()
