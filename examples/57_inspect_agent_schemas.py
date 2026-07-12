"""Inspect local PyProcore agent JSON Schema metadata.

This example prints a small summary of the registered tools and their
input/output schemas. It does not require Procore credentials and does not call
the Procore API.
"""

from __future__ import annotations

from pyprocore.agent import build_agent_tool_schemas


def main() -> None:
    """Print a beginner-friendly schema summary."""
    schema_export = build_agent_tool_schemas()
    tools = schema_export["tools"]

    print("PyProcore agent schema export is available locally.")
    print(f"Package version: {schema_export['version']}")
    print(f"Registered tools: {schema_export['tool_count']}")
    print("")
    print("A few tool schemas:")

    for tool_name in sorted(tools)[:5]:
        tool = tools[tool_name]
        required = tool["input_schema"].get("required", [])
        print(f"- {tool_name}: required inputs = {required}")

    print("")
    print("No Procore credentials were required and no live API calls were made.")


if __name__ == "__main__":
    main()
