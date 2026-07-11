"""AI-ready project context package workflow."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from pyprocore.core.exceptions import ValidationError
from pyprocore.services.daily_logs import (
    get_daily_log_counts,
    list_daily_log_headers,
    list_daily_logs_for_date,
)
from pyprocore.services.documents import download_document, list_document_folders, list_documents
from pyprocore.services.drawings import download_drawing, list_drawing_areas, list_drawings
from pyprocore.services.photos import download_photo, list_photo_albums, list_photos
from pyprocore.services.projects import get_project
from pyprocore.services.rfis import download_rfi_attachments, list_rfis
from pyprocore.services.specifications import (
    download_specification_section_revision,
    list_specification_section_revisions,
    list_specification_sections,
    list_specification_sets,
)
from pyprocore.services.submittals import download_submittal_attachments, list_submittals
from pyprocore.workflows.models import (
    ProjectContextManifest,
    ProjectContextOptions,
    ProjectContextResult,
    ProjectContextSectionResult,
)
from pyprocore.workflows.utils import (
    get_value,
    item_title,
    json_default,
    model_to_dict,
    scalar_text,
)

DEFAULT_SECTIONS = (
    "project",
    "rfis",
    "submittals",
    "documents",
    "drawings",
    "specifications",
    "photos",
    "daily_logs",
)
ALL_SECTIONS = frozenset(DEFAULT_SECTIONS)
COMMON_DAILY_LOG_TYPES = ("manpower", "notes", "delay", "delivery")


def _sdk_version() -> str:
    """Return the installed SDK version for package manifests."""
    try:
        return version("pyprocore")
    except PackageNotFoundError:
        return "0+local"


def build_project_context_package(
    project_id: int,
    company_id: int | None = None,
    output_dir: Path | str | None = None,
    include: Sequence[str] | str | None = None,
    exclude: Sequence[str] | str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    log_date: str | None = None,
    max_items: int | None = None,
    download_files: bool = False,
    overwrite: bool = False,
    continue_on_error: bool = True,
) -> ProjectContextResult:
    """Build a read-only AI-friendly project context package.

    Args:
        project_id: Procore project ID.
        company_id: Optional Procore company ID for company-scoped endpoints.
        output_dir: Local output folder. Defaults to ``project-context``.
        include: Optional section names to include.
        exclude: Optional section names to skip.
        start_date: Optional lower date bound passed to date-aware sections.
        end_date: Optional upper date bound passed to date-aware sections.
        log_date: Optional Daily Logs date.
        max_items: Optional per-collection item limit.
        download_files: Whether to call safe download helpers.
        overwrite: Whether downloads can overwrite existing files.
        continue_on_error: Whether section failures should be recorded and skipped.

    Returns:
        A typed result with manifest and summary paths.
    """
    _validate_project_context_inputs(project_id, max_items)
    root = Path(output_dir or "project-context")
    root.mkdir(parents=True, exist_ok=True)
    sections = _resolve_sections(include, exclude)
    options = ProjectContextOptions(
        project_id=project_id,
        company_id=company_id,
        output_dir=root,
        include=_normalize_sequence(include) if include is not None else None,
        exclude=_normalize_sequence(exclude) if exclude is not None else None,
        start_date=start_date,
        end_date=end_date,
        log_date=log_date,
        max_items=max_items,
        download_files=download_files,
        overwrite=overwrite,
        continue_on_error=continue_on_error,
    )
    started = time.perf_counter()
    section_results: list[ProjectContextSectionResult] = []

    builders: dict[str, Callable[[Path, ProjectContextOptions], ProjectContextSectionResult]] = {
        "project": _build_project_section,
        "rfis": _build_rfis_section,
        "submittals": _build_submittals_section,
        "documents": _build_documents_section,
        "drawings": _build_drawings_section,
        "specifications": _build_specifications_section,
        "photos": _build_photos_section,
        "daily_logs": _build_daily_logs_section,
    }
    for section in sections:
        try:
            section_results.append(builders[section](root, options))
        except Exception as exc:
            if not continue_on_error:
                raise
            section_results.append(
                ProjectContextSectionResult(
                    name=section,
                    status="failed",
                    errors=[f"{type(exc).__name__}: {exc}"],
                )
            )

    manifest = _build_manifest(root, options, sections, section_results)
    manifest.duration_seconds = round(time.perf_counter() - started, 3)
    summary_path = _write_summary(root / "summary.md", manifest)
    manifest.file_paths_written.append(summary_path)
    manifest_path = _write_json(root / "manifest.json", manifest.model_dump(mode="json"))
    errors_path = _write_optional_list(root / "errors.json", manifest.errors)
    warnings_path = _write_optional_list(root / "warnings.json", manifest.warnings)
    return ProjectContextResult(
        output_dir=root,
        project_id=project_id,
        company_id=company_id,
        manifest_path=manifest_path,
        summary_path=summary_path,
        errors_path=errors_path,
        warnings_path=warnings_path,
        manifest=manifest,
    )


def _build_project_section(
    root: Path, options: ProjectContextOptions
) -> ProjectContextSectionResult:
    """Build the project metadata section."""
    project = get_project(options.project_id)
    project_path = _write_json(root / "project.json", model_to_dict(project))
    return ProjectContextSectionResult(
        name="project",
        status="completed",
        item_count=1,
        files_written=[project_path],
    )


def _build_rfis_section(root: Path, options: ProjectContextOptions) -> ProjectContextSectionResult:
    """Build the RFIs section."""
    section_root = root / "rfis"
    section_root.mkdir(parents=True, exist_ok=True)
    rfis = _limit(
        list_rfis(
            options.project_id,
            updated_after=options.start_date,
            updated_before=options.end_date,
        ),
        options.max_items,
    )
    files = [
        _write_json(section_root / "rfis.json", _items_to_dicts(rfis)),
        _write_jsonl(section_root / "rfis.jsonl", rfis),
        _write_markdown(section_root / "rfis.md", _items_markdown("RFIs", rfis, "subject")),
    ]
    downloads = _download_rfi_files(rfis, section_root, options) if options.download_files else []
    return _completed("rfis", rfis, files, downloads)


def _build_submittals_section(
    root: Path,
    options: ProjectContextOptions,
) -> ProjectContextSectionResult:
    """Build the submittals section."""
    section_root = root / "submittals"
    section_root.mkdir(parents=True, exist_ok=True)
    submittals = _limit(
        list_submittals(
            options.project_id,
            updated_after=options.start_date,
            updated_before=options.end_date,
        ),
        options.max_items,
    )
    files = [
        _write_json(section_root / "submittals.json", _items_to_dicts(submittals)),
        _write_jsonl(section_root / "submittals.jsonl", submittals),
        _write_markdown(
            section_root / "submittals.md",
            _items_markdown("Submittals", submittals, "title"),
        ),
    ]
    downloads = (
        _download_submittal_files(submittals, section_root, options)
        if options.download_files
        else []
    )
    return _completed("submittals", submittals, files, downloads)


def _build_documents_section(
    root: Path,
    options: ProjectContextOptions,
) -> ProjectContextSectionResult:
    """Build the documents section without downloading files by default."""
    section_root = root / "documents"
    section_root.mkdir(parents=True, exist_ok=True)
    folders = _limit(
        list_document_folders(options.project_id, company_id=options.company_id),
        options.max_items,
    )
    documents = _limit(
        list_documents(options.project_id, company_id=options.company_id),
        options.max_items,
    )
    files = [
        _write_json(section_root / "document_folders.json", _items_to_dicts(folders)),
        _write_json(section_root / "documents.json", _items_to_dicts(documents)),
        _write_markdown(section_root / "documents.md", _items_markdown("Documents", documents)),
    ]
    downloads = (
        _download_document_files(documents, section_root, options) if options.download_files else []
    )
    return _completed("documents", [*folders, *documents], files, downloads)


def _build_drawings_section(
    root: Path, options: ProjectContextOptions
) -> ProjectContextSectionResult:
    """Build the drawings section without downloading files by default."""
    section_root = root / "drawings"
    section_root.mkdir(parents=True, exist_ok=True)
    areas = _limit(
        list_drawing_areas(options.project_id, company_id=options.company_id),
        options.max_items,
    )
    drawings: list[object] = []
    warnings: list[str] = []
    for area in areas:
        area_id = get_value(area, "id")
        if not isinstance(area_id, int):
            warnings.append("Skipped a drawing area without an id.")
            continue
        try:
            drawings.extend(
                _limit(
                    list_drawings(
                        options.project_id,
                        company_id=options.company_id,
                        drawing_area_id=area_id,
                    ),
                    options.max_items,
                )
            )
        except Exception as exc:
            warnings.append(f"Could not list drawings for area {area_id}: {exc}")
    drawings = _limit(drawings, options.max_items)
    files = [
        _write_json(section_root / "drawing_areas.json", _items_to_dicts(areas)),
        _write_json(section_root / "drawings.json", _items_to_dicts(drawings)),
        _write_markdown(section_root / "drawings.md", _items_markdown("Drawings", drawings)),
    ]
    downloads = (
        _download_drawing_files(drawings, section_root, options) if options.download_files else []
    )
    result = _completed("drawings", [*areas, *drawings], files, downloads)
    result.warnings.extend(warnings)
    return result


def _build_specifications_section(
    root: Path,
    options: ProjectContextOptions,
) -> ProjectContextSectionResult:
    """Build the specifications section without downloading PDFs by default."""
    section_root = root / "specifications"
    section_root.mkdir(parents=True, exist_ok=True)
    sets = _limit(
        list_specification_sets(options.project_id, company_id=options.company_id),
        options.max_items,
    )
    sections = _limit(
        list_specification_sections(options.project_id, company_id=options.company_id),
        options.max_items,
    )
    revisions = _limit(
        list_specification_section_revisions(options.project_id, company_id=options.company_id),
        options.max_items,
    )
    files = [
        _write_json(section_root / "specification_sets.json", _items_to_dicts(sets)),
        _write_json(section_root / "specification_sections.json", _items_to_dicts(sections)),
        _write_json(section_root / "specification_revisions.json", _items_to_dicts(revisions)),
        _write_markdown(
            section_root / "specifications.md",
            _items_markdown("Specifications", sections, "title"),
        ),
    ]
    downloads = (
        _download_specification_files(revisions, section_root, options)
        if options.download_files
        else []
    )
    return _completed("specifications", [*sets, *sections, *revisions], files, downloads)


def _build_photos_section(
    root: Path, options: ProjectContextOptions
) -> ProjectContextSectionResult:
    """Build the photos section without downloading photos by default."""
    section_root = root / "photos"
    section_root.mkdir(parents=True, exist_ok=True)
    albums = _limit(
        list_photo_albums(options.project_id, company_id=options.company_id),
        options.max_items,
    )
    photos: list[object] = []
    warnings: list[str] = []
    for album in albums:
        album_id = get_value(album, "id")
        if not isinstance(album_id, int):
            warnings.append("Skipped a photo album without an id.")
            continue
        try:
            photos.extend(
                _limit(
                    list_photos(
                        options.project_id,
                        company_id=options.company_id,
                        album_id=album_id,
                    ),
                    options.max_items,
                )
            )
        except Exception as exc:
            warnings.append(f"Could not list photos for album {album_id}: {exc}")
    photos = _limit(photos, options.max_items)
    files = [
        _write_json(section_root / "photo_albums.json", _items_to_dicts(albums)),
        _write_json(section_root / "photos.json", _items_to_dicts(photos)),
        _write_markdown(section_root / "photos.md", _items_markdown("Photos", photos)),
    ]
    downloads = (
        _download_photo_files(photos, section_root, options) if options.download_files else []
    )
    result = _completed("photos", [*albums, *photos], files, downloads)
    result.warnings.extend(warnings)
    return result


def _build_daily_logs_section(
    root: Path,
    options: ProjectContextOptions,
) -> ProjectContextSectionResult:
    """Build the Daily Logs section."""
    section_root = root / "daily-logs"
    section_root.mkdir(parents=True, exist_ok=True)
    counts = _limit(
        get_daily_log_counts(
            options.project_id,
            company_id=options.company_id,
            log_date=options.log_date,
            start_date=options.start_date,
            end_date=options.end_date,
        ),
        options.max_items,
    )
    headers = _limit(
        list_daily_log_headers(
            options.project_id,
            company_id=options.company_id,
            log_date=options.log_date,
            start_date=options.start_date,
            end_date=options.end_date,
        ),
        options.max_items,
    )
    summary = (
        list_daily_logs_for_date(
            options.project_id,
            company_id=options.company_id,
            log_date=options.log_date,
            log_types=COMMON_DAILY_LOG_TYPES,
        )
        if options.log_date
        else None
    )
    logs_payload = (
        summary.model_dump(mode="json") if summary is not None else {"logs": {}, "errors": {}}
    )
    errors = (
        [f"{key}: {value}" for key, value in summary.errors.items()] if summary is not None else []
    )
    files = [
        _write_json(section_root / "counts.json", _items_to_dicts(counts)),
        _write_json(section_root / "headers.json", _items_to_dicts(headers)),
        _write_json(section_root / "logs.json", logs_payload),
        _write_markdown(
            section_root / "daily_logs.md",
            _daily_logs_markdown(counts, headers, summary),
        ),
    ]
    log_count = sum(len(items) for items in summary.logs.values()) if summary is not None else 0
    return ProjectContextSectionResult(
        name="daily_logs",
        status="completed",
        item_count=len(counts) + len(headers) + log_count,
        files_written=files,
        errors=errors,
    )


def _completed(
    name: str,
    items: Sequence[object],
    files: Sequence[Path],
    downloads: Sequence[Path] | None = None,
) -> ProjectContextSectionResult:
    """Return a completed section result."""
    return ProjectContextSectionResult(
        name=name,
        status="completed",
        item_count=len(items),
        files_written=list(files),
        downloaded_files=list(downloads or []),
    )


def _download_rfi_files(
    rfis: Sequence[object],
    section_root: Path,
    options: ProjectContextOptions,
) -> list[Path]:
    """Download RFI attachments when requested."""
    paths: list[Path] = []
    for item in rfis:
        item_id = get_value(item, "id")
        if isinstance(item_id, int):
            paths.extend(
                download_rfi_attachments(
                    options.project_id,
                    item_id,
                    section_root / "attachments" / str(item_id),
                    overwrite=options.overwrite,
                )
            )
    return paths


def _download_submittal_files(
    submittals: Sequence[object],
    section_root: Path,
    options: ProjectContextOptions,
) -> list[Path]:
    """Download submittal attachments when requested."""
    paths: list[Path] = []
    for item in submittals:
        item_id = get_value(item, "id")
        if isinstance(item_id, int):
            paths.extend(
                download_submittal_attachments(
                    options.project_id,
                    item_id,
                    section_root / "attachments" / str(item_id),
                    overwrite=options.overwrite,
                )
            )
    return paths


def _download_document_files(
    documents: Sequence[object],
    section_root: Path,
    options: ProjectContextOptions,
) -> list[Path]:
    """Download documents when requested."""
    paths: list[Path] = []
    for item in documents:
        item_id = get_value(item, "id")
        if isinstance(item_id, int):
            paths.append(
                download_document(
                    options.project_id,
                    item_id,
                    section_root / "files",
                    company_id=options.company_id,
                    overwrite=options.overwrite,
                )
            )
    return paths


def _download_drawing_files(
    drawings: Sequence[object],
    section_root: Path,
    options: ProjectContextOptions,
) -> list[Path]:
    """Download drawings when requested."""
    paths: list[Path] = []
    for item in drawings:
        item_id = get_value(item, "id")
        area_id = get_value(item, "drawing_area_id", "drawing_area")
        if isinstance(area_id, dict):
            area_id = area_id.get("id")
        if isinstance(item_id, int):
            paths.append(
                download_drawing(
                    options.project_id,
                    item_id,
                    section_root / "files",
                    overwrite=options.overwrite,
                    company_id=options.company_id,
                    drawing_area_id=area_id if isinstance(area_id, int) else None,
                )
            )
    return paths


def _download_specification_files(
    revisions: Sequence[object],
    section_root: Path,
    options: ProjectContextOptions,
) -> list[Path]:
    """Download specification revision PDFs when requested."""
    paths: list[Path] = []
    for item in revisions:
        item_id = get_value(item, "id")
        if isinstance(item_id, int):
            paths.append(
                download_specification_section_revision(
                    options.project_id,
                    item_id,
                    section_root / "files",
                    company_id=options.company_id,
                    overwrite=options.overwrite,
                )
            )
    return paths


def _download_photo_files(
    photos: Sequence[object],
    section_root: Path,
    options: ProjectContextOptions,
) -> list[Path]:
    """Download photos when requested."""
    paths: list[Path] = []
    for item in photos:
        item_id = get_value(item, "id")
        if isinstance(item_id, int):
            paths.append(
                download_photo(
                    options.project_id,
                    item_id,
                    section_root / "files",
                    company_id=options.company_id,
                    overwrite=options.overwrite,
                )
            )
    return paths


def _build_manifest(
    root: Path,
    options: ProjectContextOptions,
    attempted: Sequence[str],
    sections: Sequence[ProjectContextSectionResult],
) -> ProjectContextManifest:
    """Build manifest data for the package."""
    warnings = [warning for section in sections for warning in section.warnings]
    errors = [f"{section.name}: {error}" for section in sections for error in section.errors]
    files = [path for section in sections for path in section.files_written]
    files.extend(path for section in sections for path in section.downloaded_files)
    return ProjectContextManifest(
        created_at=datetime.now(UTC).isoformat(),
        package_version=_sdk_version(),
        project_id=options.project_id,
        company_id=options.company_id,
        output_dir=root,
        options=options,
        sections_attempted=list(attempted),
        sections_completed=[section.name for section in sections if section.status == "completed"],
        sections_failed=[section.name for section in sections if section.status == "failed"],
        sections_skipped=[section.name for section in sections if section.status == "skipped"],
        file_paths_written=files,
        item_counts={section.name: section.item_count for section in sections},
        warnings=warnings,
        errors=errors,
        live_downloads_enabled=options.download_files,
        sections=list(sections),
    )


def _resolve_sections(
    include: Sequence[str] | str | None,
    exclude: Sequence[str] | str | None,
) -> list[str]:
    """Resolve requested package sections."""
    included = _normalize_sequence(include) if include is not None else list(DEFAULT_SECTIONS)
    excluded = set(_normalize_sequence(exclude)) if exclude is not None else set()
    unknown = (set(included) | excluded) - ALL_SECTIONS
    if unknown:
        supported = ", ".join(sorted(ALL_SECTIONS))
        raise ValidationError(
            "Unknown project context section(s): "
            f"{', '.join(sorted(unknown))}. Supported sections: {supported}."
        )
    return [section for section in included if section not in excluded]


def _normalize_sequence(value: Sequence[str] | str | None) -> list[str]:
    """Normalize comma-separated or sequence section input."""
    if value is None:
        return []
    if isinstance(value, str):
        raw = value.split(",")
    else:
        raw = list(value)
    return [item.strip().casefold().replace("-", "_") for item in raw if item.strip()]


def _validate_project_context_inputs(project_id: int, max_items: int | None) -> None:
    """Validate project context inputs."""
    if project_id <= 0:
        raise ValidationError("project_id must be a positive integer.")
    if max_items is not None and max_items <= 0:
        raise ValidationError("max_items must be a positive integer when provided.")


def _items_to_dicts(items: Iterable[object]) -> list[dict[str, Any]]:
    """Convert items to JSON-compatible dictionaries."""
    return [model_to_dict(item) for item in items]


def _limit(items: Sequence[object], max_items: int | None) -> list[object]:
    """Apply an optional maximum item limit."""
    values = list(items)
    return values[:max_items] if max_items is not None else values


def _write_json(path: Path, payload: object) -> Path:
    """Write JSON data and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, default=json_default, sort_keys=True),
        encoding="utf-8",
    )
    return path


def _write_jsonl(path: Path, items: Sequence[object]) -> Path:
    """Write JSONL data and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(model_to_dict(item), default=json_default, sort_keys=True) for item in items
    ]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path


def _write_markdown(path: Path, content: str) -> Path:
    """Write Markdown and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_optional_list(path: Path, values: Sequence[str]) -> Path | None:
    """Write an optional JSON list when values exist."""
    if not values:
        return None
    return _write_json(path, list(values))


def _write_summary(path: Path, manifest: ProjectContextManifest) -> Path:
    """Write the root package Markdown summary."""
    lines = [
        "# Project Context Package",
        "",
        f"- Project ID: {manifest.project_id}",
        f"- Company ID: {manifest.company_id or ''}",
        f"- Created At: {manifest.created_at}",
        f"- Downloads Enabled: {manifest.live_downloads_enabled}",
        f"- Manifest: {manifest.output_dir / 'manifest.json'}",
        "",
        "## Sections",
        "",
        "| Section | Status | Items |",
        "| --- | --- | ---: |",
    ]
    for section in manifest.sections:
        lines.append(f"| {section.name} | {section.status} | {section.item_count} |")
    if manifest.errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in manifest.errors)
    if manifest.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in manifest.warnings)
    return _write_markdown(path, "\n".join(lines).rstrip() + "\n")


def _items_markdown(title: str, items: Sequence[object], title_field: str = "name") -> str:
    """Create a compact Markdown list for common resource collections."""
    lines = [
        f"# {title}",
        "",
        f"Count: {len(items)}",
        "",
        "| ID | Number | Title | Status | Updated |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in items[:50]:
        lines.append(
            "| {id} | {number} | {title} | {status} | {updated} |".format(
                id=scalar_text(get_value(item, "id")),
                number=scalar_text(get_value(item, "number", "project_number")),
                title=scalar_text(get_value(item, title_field)) or item_title(item),
                status=scalar_text(get_value(item, "status")),
                updated=scalar_text(get_value(item, "updated_at")),
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def _daily_logs_markdown(
    counts: Sequence[object],
    headers: Sequence[object],
    summary: object | None,
) -> str:
    """Create a compact Daily Logs Markdown summary."""
    logs = get_value(summary, "logs") or {}
    errors = get_value(summary, "errors") or {}
    lines = [
        "# Daily Logs",
        "",
        f"- Count Items: {len(counts)}",
        f"- Headers: {len(headers)}",
        "",
        "| Log Type | Items |",
        "| --- | ---: |",
    ]
    if isinstance(logs, dict):
        for log_type, items in logs.items():
            count = len(items) if isinstance(items, Sequence) else 0
            lines.append(f"| {log_type} | {count} |")
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {key}: {value}" for key, value in dict(errors).items())
    return "\n".join(lines).rstrip() + "\n"
