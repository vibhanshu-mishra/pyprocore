#!/usr/bin/env python3
"""Check Phase 12 AI workflow examples for local-only safety markers."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AI_PATHS = [
    PROJECT_ROOT / "pyprocore" / "workflows" / "ai_workflows.py",
    PROJECT_ROOT / "docs" / "ai-workflows.md",
    PROJECT_ROOT / "examples" / "ai_workflows",
]
EXAMPLE_RANGE = range(131, 141)
FORBIDDEN_REQUIRED_DEPENDENCY_MARKERS = (
    "openai>=",
    "anthropic>=",
    "langchain",
    "llama-index",
    "chromadb",
    "faiss",
)
FORBIDDEN_CALL_MARKERS = (
    "chat.completions",
    "embeddings.create",
    "anthropic.",
    'requests.post("https://api.openai',
    "requests.post('https://api.openai",
)
REQUIRED_SAFETY_MARKERS = (
    "does not call external AI/model APIs",
    "Tool execution remains disabled",
    "MCP remains discovery-only",
)


def main() -> int:
    """Run local AI workflow safety checks."""
    failures: list[str] = []
    for number in EXAMPLE_RANGE:
        matches = sorted((PROJECT_ROOT / "examples").glob(f"{number}_*.py"))
        if not matches:
            failures.append(f"Missing example {number}_*.py")

    for marker in REQUIRED_SAFETY_MARKERS:
        if marker not in _read_all_ai_text():
            failures.append(f"Missing safety marker: {marker}")

    pyproject = PROJECT_ROOT / "pyproject.toml"
    requirements = PROJECT_ROOT / "requirements.txt"
    dependency_text = _read_text(pyproject) + "\n" + _read_text(requirements)
    for marker in FORBIDDEN_REQUIRED_DEPENDENCY_MARKERS:
        if marker.casefold() in dependency_text.casefold():
            failures.append(f"Forbidden required AI dependency marker found: {marker}")

    source_text = _read_all_ai_text()
    for marker in FORBIDDEN_CALL_MARKERS:
        if marker.casefold() in source_text.casefold():
            failures.append(f"Forbidden external AI call marker found: {marker}")

    if failures:
        print("FAIL: Phase 12 AI workflow safety check failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASS: Phase 12 AI workflow examples are local-only and model-agnostic.")
    return 0


def _read_all_ai_text() -> str:
    """Read Phase 12 docs, examples, templates, and helper source."""
    parts: list[str] = []
    for path in AI_PATHS:
        if path.is_file():
            parts.append(_read_text(path))
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    parts.append(_read_text(child))
    for number in EXAMPLE_RANGE:
        for example in sorted((PROJECT_ROOT / "examples").glob(f"{number}_*.py")):
            parts.append(_read_text(example))
    return "\n".join(parts)


def _read_text(path: Path) -> str:
    """Read a UTF-8 text file if present."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
