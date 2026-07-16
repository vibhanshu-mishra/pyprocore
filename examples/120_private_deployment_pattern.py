"""Print private deployment reminders for scheduled exports.

This example is documentation-as-code. It is safe to run anywhere because it
only prints local deployment guidance.
"""

from __future__ import annotations


def main() -> None:
    """Print enterprise deployment reminders."""
    print("Private scheduled export deployment checklist:")
    print("- Keep .env and token stores outside the repository.")
    print("- Separate sandbox and production folders and credentials.")
    print("- Write exports to private storage, not the source checkout.")
    print("- Rotate Data Connection App credentials on a documented schedule.")
    print("- Review permissions before adding projects or resources.")
    print("- Keep agent tool execution disabled unless a future release enables it explicitly.")


if __name__ == "__main__":
    main()
