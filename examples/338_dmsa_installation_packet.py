"""Print a plain-English DMSA installation packet for a GC/Owner."""

from pyprocore.dmsa import (
    build_dmsa_installation_packet,
    dmsa_installation_packet_to_markdown,
)


def main() -> None:
    """Render local installation guidance without creating a DMSA."""
    packet = build_dmsa_installation_packet("Contact: integration-owner@example.invalid")
    print(dmsa_installation_packet_to_markdown(packet))


if __name__ == "__main__":
    main()
