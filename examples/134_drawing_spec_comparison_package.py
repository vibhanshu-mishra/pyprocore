"""Prepare a drawing/spec comparison prompt with placeholder notes.

No live Procore calls, write actions, model calls, or vector database calls are
performed by this example.
"""

from pyprocore.workflows import build_drawing_spec_comparison_prompt_pack


def main() -> None:
    """Build and print a drawing/spec comparison prompt preview."""
    prompt = build_drawing_spec_comparison_prompt_pack(
        drawing_summary="Placeholder drawing note: Detail A references section 000000.",
        specification_summary="Placeholder spec note: Section 000000 lists sample requirements.",
    )
    print(prompt.title)
    print(prompt.user_prompt[:600])


if __name__ == "__main__":
    main()
