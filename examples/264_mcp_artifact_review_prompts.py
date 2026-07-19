"""List MCP artifact review prompts for local metadata review."""

from pyprocore.mcp import list_mcp_prompts


def main() -> None:
    """Print review-oriented MCP prompt templates."""
    print("Artifact review prompts:")
    for prompt in list_mcp_prompts():
        if "review" in prompt.kind.value:
            print(f"- {prompt.name} ({prompt.kind.value})")


if __name__ == "__main__":
    main()
