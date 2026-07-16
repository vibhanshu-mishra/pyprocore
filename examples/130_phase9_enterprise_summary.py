"""Summarize Phase 9 enterprise readiness boundaries.

This example is safe to run without credentials. It does not call Procore or
external AI/model APIs, and it does not enable tool execution.
"""

from pyprocore import __version__


def main() -> None:
    """Run the example."""
    print(f"PyProcore version: {__version__}")
    print("Phase 9D private deployment guidance is unreleased branch work.")
    print("Client Credentials is recommended for server-to-server scheduled exports.")
    print("Authorization Code remains supported for user-driven local workflows.")
    print("Tool execution remains disabled.")
    print("MCP remains discovery-only.")


if __name__ == "__main__":
    main()
