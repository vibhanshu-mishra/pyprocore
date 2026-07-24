"""Build deterministic compatibility metadata for the current local package."""

from pyprocore.maintenance import (
    ApiCompatibilityContractOptions,
    build_current_compatibility_contract,
)


def main() -> None:
    """Print current version and compatibility inventory counts."""
    contract = build_current_compatibility_contract(
        ApiCompatibilityContractOptions(generated_at="2026-07-24T00:00:00Z")
    )
    print(f"PyProcore version: {contract.pyprocore_version}")
    print(f"Resource families: {len(contract.resources)}")
    print("Metadata only; this is not production compatibility certification.")


if __name__ == "__main__":
    main()
