"""Render the FastAPI read API starter template report.

The report is metadata-only. It does not install dependencies, run FastAPI, or
call Procore.
"""

from __future__ import annotations

from pyprocore.templates import get_starter_template, template_metadata_to_markdown


def main() -> None:
    """Print the FastAPI read API starter report as Markdown."""
    template = get_starter_template("fastapi-read-api")
    print(template_metadata_to_markdown(template))


if __name__ == "__main__":
    main()
