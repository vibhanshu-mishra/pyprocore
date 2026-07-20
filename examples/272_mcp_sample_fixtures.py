"""List static MCP sample fixture files.

These fixtures are safe local examples for MCP client compatibility checks.
They are not recorded from a live Procore account.
"""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    """Print the bundled MCP fixture filenames."""
    fixtures_dir = Path(__file__).resolve().parent / "mcp_fixtures"
    fixtures = sorted(fixtures_dir.glob("*.json"))
    print(f"Found {len(fixtures)} local MCP fixture files:")
    for fixture in fixtures:
        print(f"- {fixture.name}")


if __name__ == "__main__":
    main()
