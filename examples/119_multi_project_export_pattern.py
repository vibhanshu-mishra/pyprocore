"""Preview a multi-project export plan safely."""

from __future__ import annotations

from pathlib import Path

from pyprocore import export_plan_to_manifest
from pyprocore.core.exceptions import ProcoreError


def main() -> None:
    """Print the planned files for a placeholder multi-project export."""
    plan_path = Path("examples/configs/scheduled_export_multi_project.json")
    try:
        manifest = export_plan_to_manifest(plan_path)
    except ProcoreError as exc:
        print(f"Could not build the dry-run manifest: {exc}")
        return

    print(f"Plan: {manifest.plan_name}")
    print(f"Planned files: {len(manifest.files)}")
    for file_plan in manifest.files[:10]:
        print(f"- {file_plan.output_path}")
    if len(manifest.files) > 10:
        print("- ...")


if __name__ == "__main__":
    main()
