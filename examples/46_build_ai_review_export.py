"""Build a local AI review export from an existing PyProcore package folder.

This example does not call Procore. Set PACKAGE_DIR to a local package folder
created by another workflow, such as an enhanced RFI or submittal package.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import build_ai_review_export


def main() -> None:
    """Run the local AI review export example."""
    package_dir = os.getenv("PACKAGE_DIR")
    output_dir = os.getenv("AI_EXPORT_OUTPUT_DIR")

    if not package_dir:
        print("Set PACKAGE_DIR to an existing local package folder before running this example.")
        print(
            "Example: PACKAGE_DIR=enhanced-rfi-package python3 examples/46_build_ai_review_export.py"
        )
        return

    try:
        result = build_ai_review_export(
            Path(package_dir),
            output_dir=Path(output_dir) if output_dir else None,
            overwrite=False,
        )
    except ProcoreError as exc:
        print(f"Could not build the AI review export: {exc}")
        print(
            "Tip: confirm PACKAGE_DIR exists and does not already contain a non-empty ai-export folder."
        )
        return

    print(f"AI review export created: {result.output_dir}")
    print(f"Detected package type: {result.package_type}")
    print(f"Start with: {result.ai_review_path}")
    print(f"Prompt: {result.prompt_path}")
    print("Use these files as review assistance only. Do not treat AI output as final approval.")


if __name__ == "__main__":
    main()
