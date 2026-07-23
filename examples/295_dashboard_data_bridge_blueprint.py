"""Inspect the dashboard data bridge blueprint.

This example prints local template guidance only. PyProcore does not create or
host a dashboard for you.
"""

from pyprocore.integrations import (
    get_integration_blueprint,
    integration_blueprint_to_markdown,
)


def main() -> None:
    """Print the dashboard bridge blueprint as Markdown."""
    blueprint = get_integration_blueprint("procore_dashboard_data_bridge")
    print(integration_blueprint_to_markdown(blueprint))


if __name__ == "__main__":
    main()
