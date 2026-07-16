"""Build a local field issue summarizer prompt package.

Use reviewed local notes from observations, photos, daily logs, or RFIs. This
example uses placeholder text and does not call external services.
"""

from pyprocore.workflows import build_field_issue_summary_prompt_pack


def main() -> None:
    """Build and print a field issue summary prompt preview."""
    prompt = build_field_issue_summary_prompt_pack(
        "Placeholder issue notes: sample field condition needs human review."
    )
    print(prompt.title)
    print(prompt.user_prompt[:500])


if __name__ == "__main__":
    main()
