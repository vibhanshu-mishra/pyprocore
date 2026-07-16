"""Build a local change-risk review prompt package.

This example prepares a checklist-style prompt from placeholder change context.
It performs no Procore writes and no external AI/model calls.
"""

from pyprocore.workflows import build_change_risk_review_prompt_pack


def main() -> None:
    """Build and print a change-risk review prompt preview."""
    prompt = build_change_risk_review_prompt_pack(
        "Placeholder change context: sample scope, schedule, and cost notes."
    )
    print(prompt.title)
    print("\n".join(prompt.checklist))


if __name__ == "__main__":
    main()
