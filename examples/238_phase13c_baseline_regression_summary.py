"""Summarize Phase 13C local eval baseline and regression helpers."""


def main() -> None:
    """Print a beginner-friendly Phase 13C summary."""
    print("Phase 13C adds local deterministic eval baselines and regression checks.")
    print("Use baselines to compare current eval scores against a known-good snapshot.")
    print("Use history snapshots to track local scores over time.")
    print(
        "No Procore calls, model calls, plugin execution, MCP execution, or tool execution occur."
    )


if __name__ == "__main__":
    main()
