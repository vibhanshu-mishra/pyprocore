"""Validate the bundled fake DMSA profile without making network calls."""

from pathlib import Path

from pyprocore.dmsa import (
    dmsa_validation_report_to_markdown,
    load_dmsa_connection_profile,
    validate_dmsa_connection_profile,
)


def main() -> None:
    """Load local JSON and print structural findings."""
    profile_path = Path(__file__).parent / "dmsa" / "dmsa_connection_profile.json"
    profile = load_dmsa_connection_profile(profile_path)
    print(dmsa_validation_report_to_markdown(validate_dmsa_connection_profile(profile)))


if __name__ == "__main__":
    main()
