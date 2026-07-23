"""Print the local discovery safety report as Markdown.

This example is a quick way to inspect PyProcore discovery boundaries. It does
not call Procore, execute tools, or contact external AI/model APIs.
"""

from __future__ import annotations

from pyprocore.discovery import build_discovery_report, discovery_report_to_markdown


def main() -> None:
    """Render the local discovery report."""
    report = build_discovery_report()
    print(discovery_report_to_markdown(report).rstrip())


if __name__ == "__main__":
    main()
