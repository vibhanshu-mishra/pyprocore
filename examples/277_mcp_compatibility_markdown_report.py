"""Render the MCP compatibility report as Markdown."""

from __future__ import annotations

from pyprocore.mcp import mcp_compatibility_report_to_markdown


def main() -> None:
    """Print the first lines of the Markdown compatibility report."""
    markdown = mcp_compatibility_report_to_markdown()
    print(markdown.splitlines()[0])
    print("Markdown report generated locally.")


if __name__ == "__main__":
    main()
