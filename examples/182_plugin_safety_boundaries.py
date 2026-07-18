"""Summarize Phase 11A plugin safety boundaries.

This example is intentionally text-only. It documents what the plugin foundation
does not do yet.
"""


def main() -> None:
    """Print beginner-friendly plugin safety boundaries."""
    boundaries = [
        "No plugin installation",
        "No remote plugin registry",
        "No arbitrary plugin imports",
        "No plugin code execution",
        "No Procore write or mutation actions",
        "No live Procore calls",
        "No external AI/model calls",
        "Agent tool execution remains disabled",
        "MCP remains discovery-only",
    ]
    print("Phase 11A plugin safety boundaries")
    for boundary in boundaries:
        print(f"- {boundary}")


if __name__ == "__main__":
    main()
