"""Render the current local compatibility contract as Markdown."""

from pyprocore.maintenance import (
    build_current_compatibility_contract,
    compatibility_contract_to_markdown,
)


def main() -> None:
    """Print readable compatibility metadata for human review."""
    contract = build_current_compatibility_contract()
    print(compatibility_contract_to_markdown(contract).rstrip())


if __name__ == "__main__":
    main()
