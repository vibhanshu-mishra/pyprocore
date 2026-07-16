"""Compare private deployment pattern explanations.

This example prints local guidance only. It does not provision infrastructure.
"""

from pyprocore.workflows import explain_private_deployment_pattern


def main() -> None:
    """Run the example."""
    for pattern in ("local", "private-server", "cron", "docker"):
        print(f"\n{pattern}")
        print(explain_private_deployment_pattern(pattern))


if __name__ == "__main__":
    main()
