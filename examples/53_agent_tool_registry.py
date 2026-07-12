"""List PyProcore tools that are available to future agent integrations.

This example does not require Procore credentials and does not call Procore.
It only reads the local metadata registry included with PyProcore.
"""

from pyprocore.agent import list_agent_tools


def main() -> None:
    """Print registered agent tool names and descriptions."""
    tools = list_agent_tools()
    print(f"PyProcore has {len(tools)} registered agent tools.")
    print("These are metadata records only; this script does not execute them.\n")

    for tool in tools:
        print(f"- {tool.name}: {tool.description}")


if __name__ == "__main__":
    main()
