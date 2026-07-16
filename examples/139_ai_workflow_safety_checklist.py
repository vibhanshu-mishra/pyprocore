"""Print the Phase 12 AI workflow safety checklist.

The checklist is local-only and model-agnostic. It reminds users that PyProcore
does not call external AI/model APIs or enable Procore tool execution.
"""

from pyprocore.workflows import build_ai_workflow_safety_checklist


def main() -> None:
    """Print the local AI workflow safety checklist."""
    checklist = build_ai_workflow_safety_checklist()
    print(checklist.title)
    print("\nChecklist:")
    for item in checklist.items:
        print(f"- {item}")
    print("\nBoundaries:")
    for boundary in checklist.boundaries:
        print(f"- {boundary}")


if __name__ == "__main__":
    main()
