"""Bounded local traversal for PyProcore customer-codebase usage scans."""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ValidationError
from pyprocore.maintenance.models import (
    ApiMaintenanceFinding,
    CodebaseFileFinding,
    CodebaseScanOptions,
    CodebaseScanReport,
    PyprocoreCallUsage,
    PyprocoreCliUsage,
    PyprocoreImportUsage,
    PyprocoreUsage,
)
from pyprocore.maintenance.usage import detect_python_usages, detect_text_usages


def scan_pyprocore_usage(
    codebase_path: str | Path,
    options: CodebaseScanOptions | None = None,
) -> CodebaseScanReport:
    """Scan a local folder for PyProcore usage without importing or executing it.

    Args:
        codebase_path: Existing local file or directory to inspect.
        options: Optional bounded scan settings.

    Returns:
        Local usage report with redacted snippets.

    Raises:
        ValidationError: If the path is remote, missing, or invalid.
    """
    scan_options = options or CodebaseScanOptions()
    root = _validate_local_codebase_path(codebase_path)
    scanned: list[CodebaseFileFinding] = []
    skipped: list[CodebaseFileFinding] = []
    imports: list[PyprocoreImportUsage] = []
    calls: list[PyprocoreCallUsage] = []
    cli_usages: list[PyprocoreCliUsage] = []
    other_usages: list[PyprocoreUsage] = []

    for path, skip_reason in _iter_candidate_files(root, scan_options):
        relative_path = _display_path(path, root)
        try:
            size = path.stat().st_size
        except OSError as exc:
            skipped.append(
                CodebaseFileFinding(
                    path=relative_path,
                    status="skipped",
                    reason=f"could not inspect file: {type(exc).__name__}",
                )
            )
            continue
        if skip_reason:
            skipped.append(
                CodebaseFileFinding(
                    path=relative_path,
                    status="skipped",
                    reason=skip_reason,
                    size_bytes=size,
                )
            )
            continue
        if size > scan_options.max_file_size_bytes:
            skipped.append(
                CodebaseFileFinding(
                    path=relative_path,
                    status="skipped",
                    reason="file exceeds max_file_size_bytes",
                    size_bytes=size,
                )
            )
            continue
        try:
            raw = path.read_bytes()
        except OSError as exc:
            skipped.append(
                CodebaseFileFinding(
                    path=relative_path,
                    status="skipped",
                    reason=f"could not read file: {type(exc).__name__}",
                    size_bytes=size,
                )
            )
            continue
        if b"\x00" in raw:
            skipped.append(
                CodebaseFileFinding(
                    path=relative_path,
                    status="skipped",
                    reason="binary file detected",
                    size_bytes=size,
                )
            )
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            skipped.append(
                CodebaseFileFinding(
                    path=relative_path,
                    status="skipped",
                    reason="file is not UTF-8 text",
                    size_bytes=size,
                )
            )
            continue

        scanned.append(
            CodebaseFileFinding(
                path=relative_path,
                status="scanned",
                size_bytes=size,
            )
        )
        if path.suffix.lower() == ".py":
            file_imports, file_calls, file_other = detect_python_usages(text, relative_path)
            imports.extend(file_imports)
            calls.extend(file_calls)
            other_usages.extend(file_other)
        file_cli, file_references = detect_text_usages(text, relative_path)
        cli_usages.extend(file_cli)
        if path.suffix.lower() != ".py":
            other_usages.extend(file_references)

    usages: list[PyprocoreUsage] = [*imports, *calls, *cli_usages, *other_usages]
    counts: dict[str, int] = {}
    for usage in usages:
        counts[usage.capability_family] = counts.get(usage.capability_family, 0) + 1
    return CodebaseScanReport(
        scanned_path=str(root),
        options=scan_options,
        files_scanned=scanned,
        files_skipped=skipped,
        imports=imports,
        calls=calls,
        cli_usages=cli_usages,
        usages=usages,
        capability_counts=dict(sorted(counts.items())),
        findings=[
            ApiMaintenanceFinding(
                severity="info",
                code="local_scan_only",
                message=(
                    "Local report only: no files were modified or executed, no remote "
                    "repository was accessed, and no Procore or AI/model calls were made."
                ),
            )
        ],
    )


def _validate_local_codebase_path(path: str | Path) -> Path:
    """Validate a local codebase file or directory path."""
    raw_path = str(path)
    if "://" in raw_path:
        raise ValidationError("Codebase path must be local; remote repositories are not supported.")
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise ValidationError(f"Codebase path does not exist: {resolved}")
    if not resolved.is_file() and not resolved.is_dir():
        raise ValidationError(f"Codebase path must be a regular file or directory: {resolved}")
    return resolved


def _iter_candidate_files(
    root: Path,
    options: CodebaseScanOptions,
) -> list[tuple[Path, str | None]]:
    """Return deterministic local candidates and directory-skip findings."""
    extensions = {extension.lower() for extension in options.extensions}
    ignored = set(options.ignored_directories)
    ignored_filenames = set(options.ignored_filenames)
    if root.is_file():
        reason = None if root.suffix.lower() in extensions else "unsupported file extension"
        return [(root, reason)]

    candidates: list[tuple[Path, str | None]] = []
    for current_root, directory_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current_root)
        kept_directories: list[str] = []
        for directory_name in sorted(directory_names):
            directory_path = current_path / directory_name
            if directory_name in ignored:
                candidates.append((directory_path, f"ignored directory: {directory_name}"))
            elif directory_name.startswith(".") and not options.include_hidden_files:
                candidates.append((directory_path, "hidden directory"))
            elif directory_path.is_symlink():
                candidates.append((directory_path, "symbolic-link directory"))
            else:
                kept_directories.append(directory_name)
        directory_names[:] = kept_directories
        for file_name in sorted(file_names):
            path = current_path / file_name
            if file_name in ignored_filenames:
                candidates.append((path, f"ignored filename: {file_name}"))
            elif file_name.startswith(".") and not options.include_hidden_files:
                candidates.append((path, "hidden file"))
            elif path.is_symlink():
                candidates.append((path, "symbolic-link file"))
            elif path.suffix.lower() not in extensions:
                continue
            else:
                candidates.append((path, None))
    return sorted(candidates, key=lambda row: str(row[0]))


def _display_path(path: Path, root: Path) -> str:
    """Return a stable report path relative to a scanned directory."""
    if root.is_file():
        return root.name
    return path.relative_to(root).as_posix()
