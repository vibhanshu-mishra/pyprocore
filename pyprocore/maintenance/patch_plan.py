"""Safe suggested-diff rendering and local patch artifact writing."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from pyprocore.core.exceptions import ValidationError
from pyprocore.maintenance.models import (
    MigrationPatchArtifact,
    MigrationPatchHunk,
    MigrationPatchPlan,
    MigrationPatchReport,
    MigrationPatchSuggestion,
    MigrationSafetyFinding,
)


def render_unified_diff_suggestion(
    suggestion: MigrationPatchSuggestion,
) -> MigrationPatchHunk | None:
    """Render a non-applied diff hunk for a safe documentation CLI review.

    Args:
        suggestion: Typed migration suggestion.

    Returns:
        Suggested hunk for a non-Python CLI reference, otherwise ``None``.
    """
    if (
        suggestion.category != "update_cli_command_docs"
        or not suggestion.exact_change_safe
        or suggestion.line_number is None
        or suggestion.source_snippet is None
        or Path(suggestion.file_path).suffix.lower() == ".py"
    ):
        return None
    review_line = _review_comment_for_path(suggestion.file_path)
    original = suggestion.source_snippet
    suggested = f"{review_line}\n{original}"
    unified = "\n".join(
        [
            f"--- a/{suggestion.file_path}",
            f"+++ b/{suggestion.file_path}",
            f"@@ -{suggestion.line_number},1 +{suggestion.line_number},2 @@",
            f"+{review_line}",
            f" {original}",
        ]
    )
    return MigrationPatchHunk(
        file_path=suggestion.file_path,
        line_number=suggestion.line_number,
        original_text=original,
        suggested_text=suggested,
        unified_diff=unified,
    )


def write_migration_patch_artifacts(
    plan: MigrationPatchPlan,
    output_dir: str | Path,
    *,
    dry_run: bool = True,
    overwrite: bool = False,
) -> MigrationPatchReport:
    """Plan or write migration artifacts beneath one explicit output directory.

    Args:
        plan: Typed local migration patch plan.
        output_dir: Directory reserved for generated review artifacts.
        dry_run: Validate and list artifacts without writing.
        overwrite: Permit replacing existing artifact files.

    Returns:
        Typed dry-run or artifact-write report.

    Raises:
        ValidationError: If a path escapes the output directory or an existing
            artifact would be overwritten without explicit permission.
    """
    from pyprocore.maintenance.patch_reports import build_migration_patch_artifacts

    root = Path(output_dir).expanduser().resolve()
    artifacts = build_migration_patch_artifacts(plan)
    destinations: list[tuple[MigrationPatchArtifact, Path]] = []
    for artifact in artifacts:
        relative_path = _validate_artifact_path(artifact.relative_path)
        destination = (root / relative_path).resolve()
        if not destination.is_relative_to(root):
            raise ValidationError(
                f"Patch artifact path must remain inside output directory: {relative_path}"
            )
        if destination.exists() and not overwrite:
            raise ValidationError(
                "Patch artifact already exists; use --overwrite explicitly: " f"{destination}"
            )
        destinations.append((artifact, destination))
    if dry_run:
        return MigrationPatchReport(
            plan=plan,
            output_dir=str(root),
            dry_run=True,
            artifacts=artifacts,
            planned_files=[str(destination) for _, destination in destinations],
            safety_findings=[
                MigrationSafetyFinding(
                    severity="info",
                    code="dry_run",
                    message="Dry-run completed; no artifacts or customer files were written.",
                )
            ],
        )

    written: list[str] = []
    for artifact, destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(artifact.content, encoding="utf-8")
        written.append(str(destination))
    return MigrationPatchReport(
        plan=plan,
        output_dir=str(root),
        dry_run=False,
        artifacts=artifacts,
        written_files=written,
        safety_findings=[
            MigrationSafetyFinding(
                severity="warning",
                code="artifacts_written",
                message=(
                    "Review artifacts were written only to the output directory. "
                    "No customer files were modified and no patch was applied."
                ),
            )
        ],
    )


def _review_comment_for_path(file_path: str) -> str:
    """Return a non-executing review comment suited to a documentation file."""
    if Path(file_path).suffix.lower() in {".md", ".rst"}:
        return "<!-- REVIEW: verify this PyProcore CLI reference manually. -->"
    return "# REVIEW: verify this PyProcore CLI reference manually."


def _validate_artifact_path(value: str) -> Path:
    """Validate one portable artifact path."""
    pure_path = PurePosixPath(value)
    if pure_path.is_absolute() or ".." in pure_path.parts or not pure_path.parts:
        raise ValidationError(f"Unsafe patch artifact relative path: {value}")
    if any(part in {"", "."} for part in pure_path.parts):
        raise ValidationError(f"Unsafe patch artifact relative path: {value}")
    return Path(*pure_path.parts)
