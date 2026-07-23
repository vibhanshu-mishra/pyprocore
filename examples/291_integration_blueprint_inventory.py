"""List built-in local integration blueprints.

This example does not require Procore credentials. It only prints metadata for
local templates that can help you design sync workers, webhook receivers, or
read-only internal services.
"""

from pyprocore.integrations import list_integration_blueprints


def main() -> None:
    """Print local integration blueprint names."""
    blueprints = list_integration_blueprints()
    print("Available PyProcore integration blueprints:")
    for blueprint in blueprints:
        print(f"- {blueprint.name}: {blueprint.title}")
    print("\nThese are templates only. No Procore API calls were made.")


if __name__ == "__main__":
    main()
