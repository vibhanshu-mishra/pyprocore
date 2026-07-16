"""Build a local engineering assistant context prompt bundle.

This is a context-preparation example only. It does not perform calculations,
make design decisions, call AI/model APIs, or update Procore.
"""

from pyprocore.workflows import build_engineering_assistant_context_bundle


def main() -> None:
    """Build and print an engineering context prompt preview."""
    prompt = build_engineering_assistant_context_bundle(
        "Placeholder engineering context: reviewed drawings, specs, and RFIs."
    )
    print(prompt.title)
    print("\n".join(prompt.checklist))


if __name__ == "__main__":
    main()
