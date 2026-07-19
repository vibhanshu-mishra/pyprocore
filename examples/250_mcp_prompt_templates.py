"""Inspect local PyProcore MCP prompt templates."""

from pyprocore.mcp import list_mcp_prompts


def main() -> None:
    """Print prompt template names and required inputs."""
    prompts = list_mcp_prompts()
    print(f"Found {len(prompts)} local MCP prompt templates.")
    for prompt in prompts:
        arguments = ", ".join(argument.name for argument in prompt.arguments) or "none"
        print(f"- {prompt.name}: {arguments}")
    print("These are templates only. No model API was called.")


if __name__ == "__main__":
    main()
