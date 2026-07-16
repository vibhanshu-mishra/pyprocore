"""Build a local submittal review assistant prompt package.

The data here is placeholder-only. PyProcore prepares local text; users choose
their own AI/model stack separately.
"""

from pyprocore.workflows import build_submittal_review_prompt_pack


def main() -> None:
    """Build and print a submittal review prompt preview."""
    prompt = build_submittal_review_prompt_pack(
        {"number": "SUBMITTAL-PLACEHOLDER", "title": "Placeholder product data"},
        context="Placeholder specification notes and reviewer comments.",
    )
    print(prompt.title)
    print("\n".join(prompt.checklist))
    print("\nTool execution remains disabled; MCP remains discovery-only.")


if __name__ == "__main__":
    main()
