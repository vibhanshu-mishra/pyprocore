"""Show Phase 11C plugin configuration safety boundaries.

This example is explanatory and local. It does not require credentials or make
network calls.
"""

from __future__ import annotations


def main() -> None:
    """Print what plugin config files are allowed to do."""
    print("Phase 11C safety boundaries")
    print("- JSON metadata only")
    print("- no plugin installation")
    print("- no remote fetching")
    print("- no arbitrary plugin loading")
    print("- no config-driven hook execution")
    print("- no Procore writes or live API calls")


if __name__ == "__main__":
    main()
