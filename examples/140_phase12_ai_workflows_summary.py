"""Summarize the Phase 12 model-agnostic AI workflow patterns.

This example is safe to run without credentials. It only prints local pattern
names and safety boundaries.
"""

from pyprocore.workflows import build_ai_workflow_safety_checklist


def main() -> None:
    """Print a concise Phase 12 summary."""
    patterns = [
        "RFI review assistant",
        "Submittal review assistant",
        "Project context Q&A package",
        "Drawing/spec comparison assistant",
        "Vector export pattern",
        "Engineering assistant context bundle",
        "Field issue summarizer",
        "Change-risk review package",
    ]
    print("Phase 12 AI Workflow Examples")
    for pattern in patterns:
        print(f"- {pattern}")
    print("\nSafety boundaries:")
    for boundary in build_ai_workflow_safety_checklist().boundaries:
        print(f"- {boundary}")


if __name__ == "__main__":
    main()
