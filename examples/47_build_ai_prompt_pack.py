"""Build a local AI prompt pack from an existing PyProcore package folder.

This example does not call Procore. It reads local Markdown, JSON, JSONL, and
text files from PACKAGE_DIR and creates prompt-focused files for AI review.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import build_ai_prompt_pack


def main() -> None:
    """Run the local AI prompt-pack example."""
    package_dir = os.getenv("PACKAGE_DIR")
    output_dir = os.getenv("AI_PROMPT_PACK_OUTPUT_DIR")
    review_type = os.getenv("AI_REVIEW_TYPE", "general")

    if not package_dir:
        print("Set PACKAGE_DIR to an existing local package folder before running this example.")
        print("Example: PACKAGE_DIR=submittal-package python3 examples/47_build_ai_prompt_pack.py")
        return

    try:
        result = build_ai_prompt_pack(
            Path(package_dir),
            output_dir=Path(output_dir) if output_dir else None,
            review_type=review_type,
            overwrite=False,
        )
    except ProcoreError as exc:
        print(f"Could not build the AI prompt pack: {exc}")
        print(
            "Tip: confirm PACKAGE_DIR exists and does not already contain a non-empty "
            "ai-prompt-pack folder."
        )
        return

    print(f"AI prompt pack created: {result.output_dir}")
    print(f"Detected package type: {result.package_type}")
    print(f"Prompt: {result.prompt_path}")
    print(f"System context: {result.system_context_path}")
    print("The prompt pack is local-file-only and does not send data to an AI service.")


if __name__ == "__main__":
    main()
