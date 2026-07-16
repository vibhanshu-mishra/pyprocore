"""Prepare a local project context Q&A prompt package.

Use this pattern after building a project context package with PyProcore. This
example uses placeholder text and does not call Procore or an AI/model API.
"""

from pyprocore.workflows import build_project_qa_prompt_pack


def main() -> None:
    """Build and print a project Q&A prompt preview."""
    prompt = build_project_qa_prompt_pack(
        "Placeholder summary: RFIs, submittals, drawings, and specifications "
        "were exported to local files for human review."
    )
    print(prompt.title)
    print(prompt.system_context)
    print("\nUsers can send reviewed local files to their chosen model stack.")


if __name__ == "__main__":
    main()
