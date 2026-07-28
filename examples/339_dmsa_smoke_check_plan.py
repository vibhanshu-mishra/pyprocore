"""Build a non-executing read-only DMSA smoke-check plan."""

from pathlib import Path

from pyprocore.dmsa import (
    build_dmsa_smoke_check_plan,
    dmsa_smoke_check_plan_to_markdown,
    load_dmsa_connection_profile,
)


def main() -> None:
    """Print intended checks without obtaining a token or calling Procore."""
    profile_path = Path(__file__).parent / "dmsa" / "dmsa_connection_profile.json"
    profile = load_dmsa_connection_profile(profile_path)
    print(dmsa_smoke_check_plan_to_markdown(build_dmsa_smoke_check_plan(profile)))


if __name__ == "__main__":
    main()
