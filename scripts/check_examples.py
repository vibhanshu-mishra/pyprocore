"""Validate PyProcore example scripts without running them.

This script is intentionally lightweight. It checks that every example script
has valid Python syntax and a main guard, but it never imports or executes the
examples. That keeps the check safe for CI and local development without
requiring Procore credentials.
"""

from __future__ import annotations

import py_compile
import sys
from pathlib import Path

MAIN_GUARD = 'if __name__ == "__main__":'


def find_example_files(examples_dir: Path) -> list[Path]:
    """Return Python example files in deterministic order.

    Args:
        examples_dir: Directory that contains runnable example scripts.

    Returns:
        A sorted list of Python files.
    """
    return sorted(examples_dir.glob("*.py"))


def validate_example(example_file: Path) -> list[str]:
    """Validate one example file without importing it.

    Args:
        example_file: Example script to validate.

    Returns:
        A list of beginner-friendly error messages. The list is empty when the
        example passes all checks.
    """
    errors: list[str] = []

    try:
        py_compile.compile(str(example_file), doraise=True)
    except py_compile.PyCompileError as exc:
        errors.append(f"Syntax check failed: {exc.msg}")

    try:
        source = example_file.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"Could not read file: {exc}")
        return errors

    if MAIN_GUARD not in source:
        errors.append(f"Missing main guard: {MAIN_GUARD}")

    return errors


def main() -> int:
    """Run the examples validation check.

    Returns:
        Process exit code. Returns 0 when all examples pass and 1 otherwise.
    """
    project_root = Path(__file__).resolve().parents[1]
    examples_dir = project_root / "examples"

    if not examples_dir.exists():
        print(f"Examples directory not found: {examples_dir}", file=sys.stderr)
        return 1

    example_files = find_example_files(examples_dir)
    if not example_files:
        print(f"No Python example files found in: {examples_dir}", file=sys.stderr)
        return 1

    failures: dict[Path, list[str]] = {}
    for example_file in example_files:
        errors = validate_example(example_file)
        if errors:
            failures[example_file] = errors

    if failures:
        print("Example validation failed:", file=sys.stderr)
        for example_file, errors in failures.items():
            print(f"\n- {example_file.relative_to(project_root)}", file=sys.stderr)
            for error in errors:
                print(f"  {error}", file=sys.stderr)
        print(
            "\nFix the files above, then run `make examples-check` again.",
            file=sys.stderr,
        )
        return 1

    print(f"All {len(example_files)} example scripts passed syntax and main-guard checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
