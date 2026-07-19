"""Filter MCP prompt templates by kind without running a model."""

from pyprocore.mcp import list_mcp_prompts


def main() -> None:
    """Print eval-report review prompts using the kind filter."""
    prompts = list_mcp_prompts(kind="eval_report_review")
    print(f"Found {len(prompts)} eval report review prompt(s):")
    for prompt in prompts:
        print(f"- {prompt.name}")


if __name__ == "__main__":
    main()
