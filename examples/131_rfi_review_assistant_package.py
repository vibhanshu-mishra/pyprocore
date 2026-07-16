"""Build a local RFI review assistant prompt package with placeholder data.

This example does not call Procore or any AI/model API. It shows how a user
could prepare local prompt text, then copy selected files into their own model
workflow after review.
"""

from pyprocore.workflows import build_rfi_review_prompt_pack


def main() -> None:
    """Build and print a safe RFI review prompt preview."""
    prompt = build_rfi_review_prompt_pack(
        {"number": "RFI-PLACEHOLDER", "title": "Placeholder wall detail question"},
        context="Local placeholder context from an exported RFI package.",
    )
    print(prompt.title)
    print(prompt.user_prompt[:500])
    print("\nNo Procore or external AI/model calls were made.")


if __name__ == "__main__":
    main()
