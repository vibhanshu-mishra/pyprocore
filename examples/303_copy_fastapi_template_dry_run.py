"""Preview copying the FastAPI read API starter into a temporary folder.

This is a dry run only. It does not write files, install FastAPI, run a server,
or call Procore.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from pyprocore.templates import copy_starter_template, template_copy_result_to_markdown


def main() -> None:
    """Preview the static template files in a temporary destination."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "fastapi-read-api"
        result = copy_starter_template("fastapi-read-api", output_dir, dry_run=True)
        print(template_copy_result_to_markdown(result))


if __name__ == "__main__":
    main()
