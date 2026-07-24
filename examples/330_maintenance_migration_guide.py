"""Build a general local migration-readiness guide without credentials."""

from pyprocore.maintenance import build_migration_guide


def main() -> None:
    """Print the current version and review posture."""
    guide = build_migration_guide()
    print(guide.summary)
    print(f"Overall risk: {guide.overall_risk}")
    print("No files modified; human review is required.")


if __name__ == "__main__":
    main()
