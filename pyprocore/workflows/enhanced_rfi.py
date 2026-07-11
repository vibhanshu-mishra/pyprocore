"""Enhanced AI-ready RFI package workflow."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from pyprocore.core.exceptions import ValidationError
from pyprocore.models import RFI
from pyprocore.services.daily_logs import (
    get_daily_log_counts,
    list_daily_log_headers,
    list_daily_logs_for_date,
)
from pyprocore.services.documents import list_documents
from pyprocore.services.drawings import list_drawing_areas, list_drawings
from pyprocore.services.photos import list_photo_albums, list_photos
from pyprocore.services.rfis import download_rfi_attachments, get_rfi
from pyprocore.services.search import find_rfi
from pyprocore.services.specifications import list_specification_sections
from pyprocore.services.submittals import list_submittals
from pyprocore.workflows.models import (
    EnhancedRFIPackageManifest,
    EnhancedRFIPackageOptions,
    EnhancedRFIPackageResult,
    EnhancedRFIRelatedSectionResult,
)
from pyprocore.workflows.utils import (
    get_value,
    item_title,
    json_default,
    model_to_dict,
    scalar_text,
)

RELATED_SECTIONS = (
    "submittals",
    "documents",
    "drawings",
    "specifications",
    "photos",
    "daily_logs",
)
COMMON_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "what",
    "when",
    "where",
    "which",
    "are",
    "will",
    "shall",
    "into",
    "have",
    "has",
    "rfi",
}


def build_enhanced_rfi_package(
    project_id: int,
    rfi_id: int | None = None,
    rfi_number: str | None = None,
    company_id: int | None = None,
    output_dir: Path | str | None = None,
    include_related: bool = True,
    related_sections: Sequence[str] | str | None = None,
    exclude_related: Sequence[str] | str | None = None,
    search_terms: Sequence[str] | str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    log_date: str | None = None,
    max_related_items: int = 25,
    download_files: bool = False,
    overwrite: bool = False,
    continue_on_error: bool = True,
) -> EnhancedRFIPackageResult:
    """Build a rich, read-only, AI-ready RFI review package.

    Args:
        project_id: Procore project ID.
        rfi_id: Optional RFI ID.
        rfi_number: Optional RFI number used when ``rfi_id`` is not supplied.
        company_id: Optional company ID for related project tools.
        output_dir: Local output folder. Defaults to ``rfi-package``.
        include_related: Whether to gather related project context.
        related_sections: Optional related section names to include.
        exclude_related: Optional related section names to skip.
        search_terms: Optional reviewer-provided search terms.
        start_date: Optional lower date bound for supported related sections.
        end_date: Optional upper date bound for supported related sections.
        log_date: Optional Daily Logs date.
        max_related_items: Maximum related items per section.
        download_files: Whether to download RFI attachments.
        overwrite: Whether downloads can overwrite existing files.
        continue_on_error: Whether related section failures should be recorded.

    Returns:
        A typed result describing local package artifacts.
    """
    _validate_inputs(project_id, rfi_id, rfi_number, max_related_items)
    sections = _resolve_related_sections(related_sections, exclude_related, include_related)
    root = Path(output_dir or "rfi-package")
    root.mkdir(parents=True, exist_ok=True)
    if rfi_id is not None:
        rfi = get_rfi(project_id, rfi_id)
    else:
        assert rfi_number is not None
        rfi = find_rfi(project_id, number=rfi_number)
    terms = _extract_terms(rfi, search_terms)
    options = EnhancedRFIPackageOptions(
        project_id=project_id,
        rfi_id=rfi_id,
        rfi_number=rfi_number,
        company_id=company_id,
        output_dir=root,
        include_related=include_related,
        related_sections=(
            _normalize_list(related_sections) if related_sections is not None else None
        ),
        exclude_related=_normalize_list(exclude_related) if exclude_related is not None else None,
        search_terms=_normalize_list(search_terms),
        start_date=start_date,
        end_date=end_date,
        log_date=log_date,
        max_related_items=max_related_items,
        download_files=download_files,
        overwrite=overwrite,
        continue_on_error=continue_on_error,
    )
    rfi_json_path = _write_json(root / "rfi.json", model_to_dict(rfi))
    rfi_md_path = _write_markdown(root / "rfi.md", _rfi_markdown(rfi))
    downloaded_files = (
        download_rfi_attachments(
            project_id,
            rfi.id,
            root / "attachments",
            overwrite=overwrite,
        )
        if download_files
        else []
    )
    related_results: list[EnhancedRFIRelatedSectionResult] = []
    related_payloads: dict[str, list[dict[str, Any]]] = {}
    builders = _related_builders()
    for section in sections:
        try:
            result, payload = builders[section](root, options, terms)
            related_results.append(result)
            related_payloads[section] = payload
        except Exception as exc:
            if not continue_on_error:
                raise
            related_results.append(
                EnhancedRFIRelatedSectionResult(
                    name=section,
                    status="failed",
                    errors=[f"{type(exc).__name__}: {exc}"],
                )
            )
            related_payloads[section] = []

    ai_files = _write_ai_files(root, rfi, related_payloads, related_results, terms)
    manifest = _build_manifest(
        root,
        options,
        rfi,
        sections,
        [rfi_json_path, rfi_md_path, *ai_files],
        downloaded_files,
        related_results,
    )
    summary_path = _write_markdown(root / "summary.md", _package_summary(manifest))
    manifest.files_written.append(summary_path)
    manifest_path = _write_json(root / "manifest.json", manifest.model_dump(mode="json"))
    errors_path = _write_optional_list(root / "errors.json", manifest.errors)
    warnings_path = _write_optional_list(root / "warnings.json", manifest.warnings)
    return EnhancedRFIPackageResult(
        output_dir=root,
        project_id=project_id,
        company_id=company_id,
        rfi_id=rfi.id,
        rfi_number=_text_or_none(rfi.number),
        manifest_path=manifest_path,
        summary_path=summary_path,
        rfi_json_path=rfi_json_path,
        review_context_path=root / "ai" / "review_context.md",
        errors_path=errors_path,
        warnings_path=warnings_path,
        manifest=manifest,
    )


def _related_builders() -> dict[
    str,
    Callable[
        [Path, EnhancedRFIPackageOptions, Sequence[str]],
        tuple[EnhancedRFIRelatedSectionResult, list[dict[str, Any]]],
    ],
]:
    """Return related section builder functions."""
    return {
        "submittals": _build_submittals,
        "documents": _build_documents,
        "drawings": _build_drawings,
        "specifications": _build_specifications,
        "photos": _build_photos,
        "daily_logs": _build_daily_logs,
    }


def _build_submittals(
    root: Path,
    options: EnhancedRFIPackageOptions,
    terms: Sequence[str],
) -> tuple[EnhancedRFIRelatedSectionResult, list[dict[str, Any]]]:
    """Build related submittals context."""
    items = list_submittals(
        options.project_id,
        updated_after=options.start_date,
        updated_before=options.end_date,
    )
    return _write_related(root, "submittals", _top_matches(items, terms, options.max_related_items))


def _build_documents(
    root: Path,
    options: EnhancedRFIPackageOptions,
    terms: Sequence[str],
) -> tuple[EnhancedRFIRelatedSectionResult, list[dict[str, Any]]]:
    """Build related documents context."""
    items = list_documents(options.project_id, company_id=options.company_id)
    return _write_related(root, "documents", _top_matches(items, terms, options.max_related_items))


def _build_drawings(
    root: Path,
    options: EnhancedRFIPackageOptions,
    terms: Sequence[str],
) -> tuple[EnhancedRFIRelatedSectionResult, list[dict[str, Any]]]:
    """Build related drawings context."""
    drawings: list[object] = []
    for area in list_drawing_areas(options.project_id, company_id=options.company_id):
        area_id = get_value(area, "id")
        if isinstance(area_id, int):
            drawings.extend(
                list_drawings(
                    options.project_id,
                    company_id=options.company_id,
                    drawing_area_id=area_id,
                )
            )
    return _write_related(
        root, "drawings", _top_matches(drawings, terms, options.max_related_items)
    )


def _build_specifications(
    root: Path,
    options: EnhancedRFIPackageOptions,
    terms: Sequence[str],
) -> tuple[EnhancedRFIRelatedSectionResult, list[dict[str, Any]]]:
    """Build related specifications context."""
    items = list_specification_sections(options.project_id, company_id=options.company_id)
    return _write_related(
        root,
        "specifications",
        _top_matches(items, terms, options.max_related_items),
    )


def _build_photos(
    root: Path,
    options: EnhancedRFIPackageOptions,
    terms: Sequence[str],
) -> tuple[EnhancedRFIRelatedSectionResult, list[dict[str, Any]]]:
    """Build related photos context."""
    photos: list[object] = []
    for album in list_photo_albums(options.project_id, company_id=options.company_id):
        album_id = get_value(album, "id")
        if isinstance(album_id, int):
            photos.extend(
                list_photos(options.project_id, company_id=options.company_id, album_id=album_id)
            )
    return _write_related(root, "photos", _top_matches(photos, terms, options.max_related_items))


def _build_daily_logs(
    root: Path,
    options: EnhancedRFIPackageOptions,
    terms: Sequence[str],
) -> tuple[EnhancedRFIRelatedSectionResult, list[dict[str, Any]]]:
    """Build related Daily Logs context."""
    payloads: list[object] = [
        *get_daily_log_counts(
            options.project_id,
            company_id=options.company_id,
            log_date=options.log_date,
            start_date=options.start_date,
            end_date=options.end_date,
        ),
        *list_daily_log_headers(
            options.project_id,
            company_id=options.company_id,
            log_date=options.log_date,
            start_date=options.start_date,
            end_date=options.end_date,
        ),
    ]
    if options.log_date:
        summary = list_daily_logs_for_date(
            options.project_id,
            company_id=options.company_id,
            log_date=options.log_date,
        )
        for entries in summary.logs.values():
            payloads.extend(entries)
    matches = _top_matches(payloads, terms, options.max_related_items)
    return _write_related(root, "daily_logs", matches)


def _write_related(
    root: Path,
    name: str,
    items: Sequence[object],
) -> tuple[EnhancedRFIRelatedSectionResult, list[dict[str, Any]]]:
    """Write one related-context section."""
    section_root = root / "related"
    payload = _items_to_dicts(items)
    json_path = _write_json(section_root / f"{name}.json", payload)
    md_path = _write_markdown(section_root / f"{name}.md", _related_markdown(name, items))
    return (
        EnhancedRFIRelatedSectionResult(
            name=name,
            status="completed",
            item_count=len(items),
            files_written=[json_path, md_path],
        ),
        payload,
    )


def _top_matches(items: Sequence[object], terms: Sequence[str], limit: int) -> list[object]:
    """Return top keyword matches with deterministic ordering."""
    scored: list[tuple[int, int, object]] = []
    for index, item in enumerate(items):
        text = _searchable_text(item)
        score = sum(1 for term in terms if term and term in text)
        if score > 0:
            scored.append((score, -index, item))
    scored.sort(key=lambda value: (value[0], value[1]), reverse=True)
    return [item for _, _, item in scored[:limit]]


def _extract_terms(rfi: RFI, user_terms: Sequence[str] | str | None) -> list[str]:
    """Extract simple keyword terms from an RFI and user input."""
    raw_values = [
        _text_or_none(rfi.number),
        item_title(rfi),
        scalar_text(
            get_value(rfi, "location", "reference", "drawing_number", "specification_section")
        ),
    ]
    for question in rfi.questions:
        raw_values.append(scalar_text(get_value(question, "plain_text_body", "body")))
    raw_values.extend(_normalize_list(user_terms))
    terms: list[str] = []
    for value in raw_values:
        if not value:
            continue
        for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9_.-]+", value.casefold()):
            normalized = token.strip("._-")
            if len(normalized) < 3 or normalized in COMMON_WORDS:
                continue
            if normalized not in terms:
                terms.append(normalized)
    return terms


def _write_ai_files(
    root: Path,
    rfi: RFI,
    related: Mapping[str, Sequence[Mapping[str, Any]]],
    results: Sequence[EnhancedRFIRelatedSectionResult],
    terms: Sequence[str],
) -> list[Path]:
    """Write AI review context files."""
    ai_root = root / "ai"
    ai_root.mkdir(parents=True, exist_ok=True)
    context = {
        "rfi": model_to_dict(rfi),
        "search_terms": list(terms),
        "related_counts": {name: len(items) for name, items in related.items()},
        "warnings": [warning for result in results for warning in result.warnings],
        "errors": [f"{result.name}: {error}" for result in results for error in result.errors],
    }
    return [
        _write_markdown(
            ai_root / "review_context.md", _review_context_markdown(rfi, related, results, terms)
        ),
        _write_json(ai_root / "review_context.json", context),
        _write_markdown(ai_root / "questions_to_answer.md", _questions_markdown()),
        _write_markdown(ai_root / "risk_flags.md", _risk_flags_markdown(rfi, related)),
    ]


def _review_context_markdown(
    rfi: RFI,
    related: Mapping[str, Sequence[Mapping[str, Any]]],
    results: Sequence[EnhancedRFIRelatedSectionResult],
    terms: Sequence[str],
) -> str:
    """Create the main AI review context Markdown."""
    lines = [
        "# RFI Review Context",
        "",
        f"- RFI ID: {rfi.id}",
        f"- Number: {scalar_text(rfi.number)}",
        f"- Subject: {item_title(rfi)}",
        f"- Status: {scalar_text(rfi.status)}",
        f"- Due Date: {scalar_text(get_value(rfi, 'due_date'))}",
        f"- Assignee: {scalar_text(get_value(rfi, 'assignee'))}",
        f"- Responsible Contractor: {scalar_text(get_value(rfi, 'responsible_contractor'))}",
        f"- Search Terms: {', '.join(terms)}",
        "",
        "## Question / Body",
        "",
        _rfi_question_text(rfi) or "No question text was found.",
        "",
        "## Official Answer / Response",
        "",
        _official_answer_text(rfi) or "No official answer was found in the RFI payload.",
        "",
        "## Related Context",
        "",
        "| Section | Matched Items |",
        "| --- | ---: |",
    ]
    for name, items in related.items():
        lines.append(f"| {name} | {len(items)} |")
    failures = [result for result in results if result.status == "failed"]
    if failures:
        lines.extend(["", "## Related Section Errors", ""])
        for result in failures:
            lines.extend(f"- {result.name}: {error}" for error in result.errors)
    return "\n".join(lines).rstrip() + "\n"


def _questions_markdown() -> str:
    """Return reviewer prompts for the enhanced RFI package."""
    return "\n".join(
        [
            "# Questions To Answer",
            "",
            "- What is the core issue raised by this RFI?",
            "- Which drawings or specification sections may be relevant?",
            "- What information is missing from the current RFI?",
            "- What cost, schedule, or coordination risks should be reviewed?",
            "- What follow-up questions should be asked before closing the RFI?",
            "- Which related project records should a human reviewer inspect first?",
            "",
        ]
    )


def _risk_flags_markdown(rfi: RFI, related: Mapping[str, Sequence[Mapping[str, Any]]]) -> str:
    """Return simple rule-based possible review flags."""
    flags: list[str] = []
    due_date = _parse_date(scalar_text(get_value(rfi, "due_date")))
    if due_date is not None and due_date <= date.today():
        flags.append("Possible overdue RFI based on due date.")
    if not _official_answer_text(rfi):
        flags.append("No official answer was found in the RFI payload.")
    if _attachment_count(rfi) == 0:
        flags.append("No attachments were found on RFI questions.")
    if not get_value(rfi, "assignee", "responsible_contractor"):
        flags.append("No responsible party was found in common RFI fields.")
    if scalar_text(rfi.status).casefold() in {"open", "pending"}:
        flags.append("Status appears open or pending.")
    if len(related.get("daily_logs", [])) >= 10 or len(related.get("photos", [])) >= 10:
        flags.append("Many related Daily Log or photo records were found.")
    if len(related.get("documents", [])) >= 10 or len(related.get("specifications", [])) >= 10:
        flags.append("Many related document or specification records were found.")
    if not flags:
        flags.append("No simple rule-based review flags were detected.")
    return "# Possible Review Flags\n\n" + "\n".join(f"- {flag}" for flag in flags) + "\n"


def _build_manifest(
    root: Path,
    options: EnhancedRFIPackageOptions,
    rfi: RFI,
    attempted: Sequence[str],
    core_files: Sequence[Path],
    downloaded_files: Sequence[Path],
    related_results: Sequence[EnhancedRFIRelatedSectionResult],
) -> EnhancedRFIPackageManifest:
    """Build enhanced RFI manifest metadata."""
    files = list(core_files)
    for result in related_results:
        files.extend(result.files_written)
    files.extend(downloaded_files)
    errors = [f"{result.name}: {error}" for result in related_results for error in result.errors]
    warnings = [warning for result in related_results for warning in result.warnings]
    return EnhancedRFIPackageManifest(
        created_at=datetime.now(UTC).isoformat(),
        project_id=options.project_id,
        company_id=options.company_id,
        rfi_id=rfi.id,
        rfi_number=_text_or_none(rfi.number),
        output_dir=root,
        options=options,
        sections_attempted=list(attempted),
        sections_completed=[
            result.name for result in related_results if result.status == "completed"
        ],
        sections_failed=[result.name for result in related_results if result.status == "failed"],
        files_written=files,
        related_item_counts={result.name: result.item_count for result in related_results},
        downloads_enabled=options.download_files,
        downloaded_files=list(downloaded_files),
        errors=errors,
        warnings=warnings,
        related_sections=list(related_results),
    )


def _package_summary(manifest: EnhancedRFIPackageManifest) -> str:
    """Create root package summary Markdown."""
    lines = [
        "# Enhanced RFI Package",
        "",
        f"- Project ID: {manifest.project_id}",
        f"- RFI ID: {manifest.rfi_id}",
        f"- RFI Number: {manifest.rfi_number or ''}",
        f"- Downloads Enabled: {manifest.downloads_enabled}",
        "",
        "| Related Section | Status | Items |",
        "| --- | --- | ---: |",
    ]
    for section in manifest.related_sections:
        lines.append(f"| {section.name} | {section.status} | {section.item_count} |")
    return "\n".join(lines).rstrip() + "\n"


def _rfi_markdown(rfi: RFI) -> str:
    """Create primary RFI Markdown."""
    return "\n".join(
        [
            f"# RFI {scalar_text(rfi.number)}: {item_title(rfi)}".strip(),
            "",
            f"- ID: {rfi.id}",
            f"- Status: {scalar_text(rfi.status)}",
            f"- Due Date: {scalar_text(get_value(rfi, 'due_date'))}",
            "",
            "## Question / Body",
            "",
            _rfi_question_text(rfi) or "No question text was found.",
            "",
            "## Official Answer / Response",
            "",
            _official_answer_text(rfi) or "No official answer was found in the RFI payload.",
            "",
        ]
    )


def _related_markdown(name: str, items: Sequence[object]) -> str:
    """Create compact related section Markdown."""
    lines = [
        f"# Related {name.replace('_', ' ').title()}",
        "",
        f"Count: {len(items)}",
        "",
        "| ID | Number | Title | Status |",
        "| --- | --- | --- | --- |",
    ]
    for item in items[:50]:
        lines.append(
            "| {id} | {number} | {title} | {status} |".format(
                id=scalar_text(get_value(item, "id")),
                number=scalar_text(get_value(item, "number", "project_number")),
                title=item_title(item),
                status=scalar_text(get_value(item, "status")),
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def _resolve_related_sections(
    related_sections: Sequence[str] | str | None,
    exclude_related: Sequence[str] | str | None,
    include_related: bool,
) -> list[str]:
    """Resolve related section names."""
    if not include_related:
        return []
    included = (
        _normalize_list(related_sections)
        if related_sections is not None
        else list(RELATED_SECTIONS)
    )
    excluded = set(_normalize_list(exclude_related))
    unknown = (set(included) | excluded) - set(RELATED_SECTIONS)
    if unknown:
        raise ValidationError(
            "Unknown related section(s): "
            f"{', '.join(sorted(unknown))}. Supported sections: {', '.join(RELATED_SECTIONS)}."
        )
    return [section for section in included if section not in excluded]


def _normalize_list(value: Sequence[str] | str | None) -> list[str]:
    """Normalize comma-separated values or string sequences."""
    if value is None:
        return []
    raw = value.split(",") if isinstance(value, str) else list(value)
    return [item.strip().casefold().replace("-", "_") for item in raw if item.strip()]


def _validate_inputs(
    project_id: int,
    rfi_id: int | None,
    rfi_number: str | None,
    max_related_items: int,
) -> None:
    """Validate enhanced RFI package inputs."""
    if project_id <= 0:
        raise ValidationError("project_id must be a positive integer.")
    if rfi_id is None and not rfi_number:
        raise ValidationError("Provide rfi_id or rfi_number.")
    if rfi_id is not None and rfi_id <= 0:
        raise ValidationError("rfi_id must be a positive integer.")
    if max_related_items <= 0:
        raise ValidationError("max_related_items must be a positive integer.")


def _items_to_dicts(items: Iterable[object]) -> list[dict[str, Any]]:
    """Convert items to dictionaries."""
    return [model_to_dict(item) for item in items]


def _searchable_text(item: object) -> str:
    """Return lowercase searchable text for a related item."""
    return json.dumps(model_to_dict(item), default=json_default, sort_keys=True).casefold()


def _rfi_question_text(rfi: RFI) -> str:
    """Return concatenated RFI question text."""
    values = [
        scalar_text(get_value(question, "plain_text_body", "body")) for question in rfi.questions
    ]
    return "\n\n".join(value for value in values if value)


def _official_answer_text(rfi: RFI) -> str:
    """Return common official answer/response fields."""
    return scalar_text(get_value(rfi, "official_response", "answer", "response", "response_text"))


def _attachment_count(rfi: RFI) -> int:
    """Count question attachments."""
    count = 0
    for question in rfi.questions:
        attachments = get_value(question, "attachments") or []
        if isinstance(attachments, Sequence) and not isinstance(attachments, (str, bytes)):
            count += len(attachments)
    return count


def _parse_date(value: str) -> date | None:
    """Parse a date from common ISO-like values."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def _write_json(path: Path, payload: object) -> Path:
    """Write JSON and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, default=json_default, sort_keys=True),
        encoding="utf-8",
    )
    return path


def _write_markdown(path: Path, content: str) -> Path:
    """Write Markdown and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_optional_list(path: Path, values: Sequence[str]) -> Path | None:
    """Write an optional JSON list."""
    if not values:
        return None
    return _write_json(path, list(values))


def _text_or_none(value: object) -> str | None:
    """Return string text or None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None
