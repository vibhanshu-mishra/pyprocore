"""Copy the FastAPI read API starter into a temporary folder.

The copied files are static examples. This script does not install
dependencies, run FastAPI, call Procore, or execute template code.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from pyprocore.templates import copy_starter_template


def main() -> None:
    """Copy the starter template to a temporary directory and print file paths."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "fastapi-read-api"
        result = copy_starter_template("fastapi-read-api", output_dir)
        print(f"Copied template: {result.template_name}")
        for file in result.files:
            print(f"- {file.path}: {file.status}")
        print("No Procore API calls or write actions were performed.")


if __name__ == "__main__":
    main()
