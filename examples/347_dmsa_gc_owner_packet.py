"""Build a complete placeholder-only GC/Owner installation packet."""

from pyprocore.dmsa import (
    build_gc_owner_installation_packet,
    gc_owner_installation_packet_to_markdown,
)


def main() -> None:
    """Print a local packet without credentials or Procore calls."""
    print(gc_owner_installation_packet_to_markdown(build_gc_owner_installation_packet()))


if __name__ == "__main__":
    main()
