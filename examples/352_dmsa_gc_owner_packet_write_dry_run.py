"""Preview GC/Owner packet artifacts without writing files."""

from pyprocore.dmsa import (
    build_gc_owner_installation_packet,
    gc_owner_packet_write_result_to_markdown,
    write_gc_owner_installation_packet,
)


def main() -> None:
    """Print a local dry-run artifact list."""
    result = write_gc_owner_installation_packet(
        build_gc_owner_installation_packet(),
        "./exports/gc-owner-packet",
        dry_run=True,
    )
    print(gc_owner_packet_write_result_to_markdown(result))


if __name__ == "__main__":
    main()
