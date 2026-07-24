"""Safe local copy helpers for optional starter templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pyprocore.core.exceptions import ValidationError
from pyprocore.templates.models import (
    TemplateCopyFileResult,
    TemplateCopyFinding,
    TemplateCopyResult,
)
from pyprocore.templates.registry import get_starter_template

UNSAFE_OUTPUT_FRAGMENTS = (
    "://",
    "access_token",
    "refresh_token",
    "client_secret",
    "authorization",
    "bearer ",
    "password",
    "token=",
    "secret=",
)


def copy_starter_template(
    name: str,
    output_dir: Path | str,
    *,
    overwrite: bool = False,
    dry_run: bool = False,
) -> TemplateCopyResult:
    """Copy or preview a static starter template.

    Args:
        name: Template identifier.
        output_dir: Destination directory.
        overwrite: Whether existing files may be replaced.
        dry_run: When true, plan files without writing them.

    Returns:
        Copy result with planned, written, skipped, and validation findings.
    """
    template = get_starter_template(name)
    root = Path(output_dir)
    findings = _validate_output_dir(root)
    result = TemplateCopyResult(
        template_name=template.name,
        output_dir=root,
        dry_run=dry_run,
        overwrite=overwrite,
        findings=findings,
    )
    if any(finding.severity == "error" for finding in findings):
        return result

    resolved_root = root.resolve()
    for template_file in template.files:
        relative = _safe_relative_path(template_file.path)
        target = root / relative
        file_result = TemplateCopyFileResult(
            source_template=template_file.path,
            path=str(target),
            exists=target.exists(),
            status="planned" if dry_run else "pending",
        )
        result.files.append(file_result)
        result.planned_count += 1
        if not _is_relative_to(target.resolve(), resolved_root):
            file_result.status = "error"
            result.findings.append(
                TemplateCopyFinding(
                    severity="error",
                    message="Template target escaped the selected output directory.",
                    path=str(target),
                )
            )
            continue
        if dry_run:
            continue
        if target.exists() and not overwrite:
            file_result.status = "skipped"
            file_result.exists = True
            result.skipped_count += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(template_file.content, encoding="utf-8")
        if relative.name.endswith(".sh"):
            target.chmod(0o755)
        file_result.status = "written"
        file_result.exists = True
        result.written_count += 1
    return result


def template_copy_result_to_jsonable(result: TemplateCopyResult) -> dict[str, Any]:
    """Return copy result as a JSON-compatible dictionary."""
    return result.model_dump(mode="json")


def _validate_output_dir(path: Path) -> list[TemplateCopyFinding]:
    """Validate output path without requiring it to exist."""
    findings: list[TemplateCopyFinding] = []
    text = str(path)
    lowered = text.casefold()
    if path.is_absolute():
        candidate_parts = path.parts
    else:
        candidate_parts = path.parts
    if any(part == ".." for part in candidate_parts):
        findings.append(
            TemplateCopyFinding(
                severity="error",
                message="Template output paths must not contain path traversal.",
            )
        )
    if lowered.startswith(("http:", "https:")) or "://" in lowered:
        findings.append(
            TemplateCopyFinding(
                severity="error",
                message="Template output must be a local filesystem path, not a URL.",
            )
        )
    for fragment in UNSAFE_OUTPUT_FRAGMENTS:
        if fragment in lowered:
            findings.append(
                TemplateCopyFinding(
                    severity="error",
                    message="Template output path appears to contain sensitive text.",
                )
            )
            break
    return findings


def _safe_relative_path(value: str) -> Path:
    """Return a safe relative file path for a static template entry."""
    path = Path(value)
    if path.is_absolute() or any(part == ".." for part in path.parts):
        raise ValidationError("Template file paths must stay relative.")
    return path


def _is_relative_to(path: Path, parent: Path) -> bool:
    """Return whether path is inside parent."""
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
