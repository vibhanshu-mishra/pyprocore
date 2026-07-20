"""Print beginner-friendly MCP client integration notes.

Use this as a checklist before integrating an MCP client with PyProcore's
discovery-only metadata surface.
"""

from __future__ import annotations

from pyprocore.mcp import build_mcp_compatibility_report


def main() -> None:
    """Print local MCP integrator notes."""
    report = build_mcp_compatibility_report()
    print("MCP integration notes:")
    for note in report.integrator_notes:
        print(f"- {note}")
    print("Keep tool execution disabled unless a future guarded release documents otherwise.")


if __name__ == "__main__":
    main()
