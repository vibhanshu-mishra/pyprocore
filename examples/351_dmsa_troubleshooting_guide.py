"""Render likely-cause GC/Owner onboarding troubleshooting guidance."""

from pyprocore.dmsa import (
    build_gc_owner_troubleshooting_guide,
    gc_owner_troubleshooting_guide_to_markdown,
)


def main() -> None:
    """Print cautious local guidance without performing live checks."""
    print(gc_owner_troubleshooting_guide_to_markdown(build_gc_owner_troubleshooting_guide()))


if __name__ == "__main__":
    main()
