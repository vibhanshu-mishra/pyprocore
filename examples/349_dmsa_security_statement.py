"""Render the GC/Owner-facing read-only security statement."""

from pyprocore.dmsa import (
    build_gc_owner_security_statement,
    gc_owner_security_statement_to_markdown,
)


def main() -> None:
    """Print local security guidance without making external calls."""
    print(gc_owner_security_statement_to_markdown(build_gc_owner_security_statement()))


if __name__ == "__main__":
    main()
