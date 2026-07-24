"""List optional PyProcore starter templates without running them.

This example does not call Procore, does not import FastAPI, and does not
execute copied template code.
"""

from __future__ import annotations

from pyprocore.templates import list_starter_templates


def main() -> None:
    """Print the local starter template inventory."""
    templates = list_starter_templates()
    print(f"Starter templates available: {len(templates)}")
    for template in templates:
        print(f"- {template.name}: {template.summary}")
    print("No Procore API calls were made.")


if __name__ == "__main__":
    main()
