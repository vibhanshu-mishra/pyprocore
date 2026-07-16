"""Print a concise Phase 10C async batch safety summary."""

from __future__ import annotations


def main() -> None:
    """Print Phase 10C safety boundaries."""
    print("Phase 10C adds read-only async multi-project batch helpers.")
    print("Dry-run and validate commands do not call Procore.")
    print("Examples use placeholder IDs, mock clients, or temporary folders.")
    print(
        "No Procore writes, uploads, external AI calls, MCP execution, or tool execution are enabled."
    )


if __name__ == "__main__":
    main()
