"""Print Phase 10E safety boundaries for financial and contract async coverage."""

from __future__ import annotations


def main() -> None:
    """Print a concise safety summary."""
    print(
        "Phase 10E async financial, contract, billing, and project-management coverage is read-only."
    )
    print(
        "Not included: create, update, delete, upload, approve, reject, submit, complete, or pay."
    )
    print(
        "No budget edits, contract edits, invoice submissions, payment actions, or schedule imports."
    )
    print("Agent tool execution remains disabled; MCP remains discovery-only.")


if __name__ == "__main__":
    main()
