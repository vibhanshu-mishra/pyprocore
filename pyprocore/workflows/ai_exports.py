"""Local AI review export helpers for PyProcore workflow packages."""

from __future__ import annotations

import fnmatch
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from pyprocore.core.exceptions import ValidationError
from pyprocore.workflows.models import (
    AIExportChunk,
    AIExportManifest,
    AIExportOptions,
    AIExportResult,
    AIExportSource,
)
from pyprocore.workflows.utils import json_default

DEFAULT_SOURCE_EXTENSIONS = (".md", ".json", ".jsonl", ".txt")
DEFAULT_EXCLUDE_PATTERNS = (
    "ai-export/*",
    "ai-prompt-pack/*",
    "attachments/*",
    "downloads/*",
    "*.pdf",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.zip",
    "*.doc",
    "*.docx",
    "*.xls",
    "*.xlsx",
)


def build_ai_review_export(
    package_dir: Path | str,
    output_dir: Path | str | None = None,
    export_name: str | None = None,
    format: str = "markdown",
    include_json: bool = True,
    include_prompt: bool = True,
    include_checklists: bool = True,
    max_chunk_chars: int = 12000,
    source_extensions: Sequence[str] | str | None = None,
    exclude_patterns: Sequence[str] | str | None = None,
    overwrite: bool = False,
) -> AIExportResult:
    """Build a local AI-friendly review export from an existing package folder.

    Args:
        package_dir: Existing local workflow package folder.
        output_dir: Optional output folder. Defaults to ``package_dir / "ai-export"``.
        export_name: Optional export name recorded in the manifest.
        format: Export format. Currently ``"markdown"`` is supported.
        include_json: Whether to write ``ai_review.json``.
        include_prompt: Whether to write ``prompt.md`` and ``system_context.md``.
        include_checklists: Whether to write checklist Markdown files.
        max_chunk_chars: Maximum characters per chunk.
        source_extensions: Optional included source extensions.
        exclude_patterns: Optional glob-style exclude patterns.
        overwrite: Whether an existing output folder may be replaced logically.

    Returns:
        A typed result with paths and manifest metadata.
    """
    package_root = Path(package_dir)
    if not package_root.exists() or not package_root.is_dir():
        raise ValidationError(f"package_dir must be an existing directory: {package_root}")
    if max_chunk_chars <= 0:
        raise ValidationError("max_chunk_chars must be a positive integer.")
    if format != "markdown":
        raise ValidationError("Only markdown AI review exports are currently supported.")

    root = Path(output_dir) if output_dir is not None else package_root / "ai-export"
    if root.exists() and any(root.iterdir()) and not overwrite:
        raise ValidationError(f"Output directory already exists and is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)

    extensions = _normalize_extensions(source_extensions)
    excludes = [*DEFAULT_EXCLUDE_PATTERNS, *_normalize_list(exclude_patterns)]
    package_type = _detect_package_type(package_root)
    sources = _discover_sources(package_root, extensions, excludes)
    included_sources = [source for source in sources if source.included]
    source_texts = _read_source_texts(package_root, included_sources)
    chunks = _write_chunks(root, source_texts, max_chunk_chars)
    _attach_chunk_paths(included_sources, chunks)

    options = AIExportOptions(
        package_dir=package_root,
        output_dir=root,
        export_name=export_name,
        format=format,
        include_json=include_json,
        include_prompt=include_prompt,
        include_checklists=include_checklists,
        max_chunk_chars=max_chunk_chars,
        source_extensions=list(extensions),
        exclude_patterns=_normalize_list(exclude_patterns) or None,
        overwrite=overwrite,
    )

    files_written: list[Path] = []
    ai_review_path = _write_markdown(
        root / "ai_review.md",
        _ai_review_markdown(package_type, package_root, included_sources, chunks),
    )
    files_written.append(ai_review_path)

    ai_review_json_path: Path | None = None
    if include_json:
        ai_review_json_path = _write_json(
            root / "ai_review.json",
            {
                "package_type": package_type,
                "package_dir": str(package_root),
                "sources": [source.model_dump(mode="json") for source in included_sources],
                "chunks": [chunk.model_dump(mode="json") for chunk in chunks],
                "guidance": _review_guidance(package_type),
            },
        )
        files_written.append(ai_review_json_path)

    prompt_path: Path | None = None
    system_context_path: Path | None = None
    if include_prompt:
        prompt_path = _write_markdown(root / "prompt.md", _prompt_markdown(package_type))
        system_context_path = _write_markdown(
            root / "system_context.md",
            _system_context_markdown(package_type),
        )
        files_written.extend([prompt_path, system_context_path])

    checklist_paths: list[Path] = []
    if include_checklists:
        checklist_paths = _write_checklists(root, package_type)
        files_written.extend(checklist_paths)

    source_index_json_path = _write_json(
        root / "source_index.json",
        [source.model_dump(mode="json") for source in sources],
    )
    source_index_md_path = _write_markdown(
        root / "source_index.md",
        _source_index_markdown(sources),
    )
    files_written.extend([source_index_json_path, source_index_md_path])
    files_written.extend(chunk.path for chunk in chunks)

    warnings = _build_warnings(sources)
    errors: list[str] = []
    warnings_path = _write_optional_list(root / "warnings.json", warnings)
    errors_path = _write_optional_list(root / "errors.json", errors)
    if warnings_path:
        files_written.append(warnings_path)
    if errors_path:
        files_written.append(errors_path)

    manifest = AIExportManifest(
        created_at=datetime.now(UTC).isoformat(),
        package_dir=package_root,
        output_dir=root,
        package_type=package_type,
        options=options,
        sources=sources,
        chunks=chunks,
        files_written=files_written,
        warnings=warnings,
        errors=errors,
    )
    manifest_path = _write_json(root / "manifest.json", manifest.model_dump(mode="json"))
    manifest.files_written.append(manifest_path)

    return AIExportResult(
        output_dir=root,
        package_dir=package_root,
        package_type=package_type,
        manifest_path=manifest_path,
        ai_review_path=ai_review_path,
        ai_review_json_path=ai_review_json_path,
        prompt_path=prompt_path,
        system_context_path=system_context_path,
        source_index_json_path=source_index_json_path,
        source_index_md_path=source_index_md_path,
        chunk_paths=[chunk.path for chunk in chunks],
        checklist_paths=checklist_paths,
        warnings_path=warnings_path,
        errors_path=errors_path,
        manifest=manifest,
    )


def build_ai_prompt_pack(
    package_dir: Path | str,
    output_dir: Path | str | None = None,
    review_type: str = "general",
    max_chunk_chars: int = 12000,
    overwrite: bool = False,
) -> AIExportResult:
    """Build a prompt-focused local AI export from an existing package folder."""
    root = Path(output_dir) if output_dir is not None else Path(package_dir) / "ai-prompt-pack"
    return build_ai_review_export(
        package_dir,
        output_dir=root,
        export_name=f"{review_type}-prompt-pack",
        include_json=False,
        include_prompt=True,
        include_checklists=True,
        max_chunk_chars=max_chunk_chars,
        overwrite=overwrite,
    )


def _detect_package_type(package_dir: Path) -> str:
    """Detect a known package type from local files."""
    if (package_dir / "rfi.json").exists():
        return "enhanced_rfi"
    if (package_dir / "submittal.json").exists():
        return "enhanced_submittal"
    if (package_dir / "project_context_manifest.json").exists() or (
        package_dir / "project.json"
    ).exists():
        return "project_context"
    manifest = _read_json_if_possible(package_dir / "manifest.json")
    if isinstance(manifest, dict):
        keys = set(manifest)
        if "rfi_id" in keys:
            return "enhanced_rfi"
        if "submittal_id" in keys:
            return "enhanced_submittal"
        if "sections_attempted" in keys and "project_id" in keys:
            return "project_context"
    return "generic"


def _discover_sources(
    package_dir: Path,
    extensions: Sequence[str],
    exclude_patterns: Sequence[str],
) -> list[AIExportSource]:
    """Discover supported source files and record excluded files."""
    sources: list[AIExportSource] = []
    for path in sorted(item for item in package_dir.rglob("*") if item.is_file()):
        relative_path = path.relative_to(package_dir).as_posix()
        suffix = path.suffix.casefold()
        size = path.stat().st_size
        excluded_pattern = _matching_pattern(relative_path, exclude_patterns)
        if excluded_pattern:
            sources.append(
                AIExportSource(
                    relative_path=relative_path,
                    file_type=suffix or "unknown",
                    size=size,
                    included=False,
                    reason=f"Excluded by pattern: {excluded_pattern}",
                    role=_detect_source_role(relative_path),
                )
            )
            continue
        if suffix not in extensions:
            sources.append(
                AIExportSource(
                    relative_path=relative_path,
                    file_type=suffix or "unknown",
                    size=size,
                    included=False,
                    reason="Unsupported extension or binary/downloaded file",
                    role=_detect_source_role(relative_path),
                )
            )
            continue
        sources.append(
            AIExportSource(
                relative_path=relative_path,
                file_type=suffix,
                size=size,
                included=True,
                role=_detect_source_role(relative_path),
            )
        )
    return sources


def _read_source_texts(
    package_dir: Path,
    sources: Sequence[AIExportSource],
) -> list[tuple[AIExportSource, str]]:
    """Read included sources as text."""
    texts: list[tuple[AIExportSource, str]] = []
    for source in sources:
        path = package_dir / source.relative_path
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            source.included = False
            source.reason = "Could not read as UTF-8 text"
            continue
        texts.append((source, text))
    return texts


def _write_chunks(
    output_dir: Path,
    source_texts: Sequence[tuple[AIExportSource, str]],
    max_chunk_chars: int,
) -> list[AIExportChunk]:
    """Write deterministic Markdown chunks under ``max_chunk_chars``."""
    chunks: list[AIExportChunk] = []
    current_parts: list[str] = []
    current_sources: list[Path] = []
    current_size = 0

    def flush() -> None:
        nonlocal current_parts, current_sources, current_size
        if not current_parts:
            return
        path = output_dir / "chunks" / f"chunk_{len(chunks) + 1:03d}.md"
        content = "\n\n".join(current_parts).rstrip() + "\n"
        _write_markdown(path, content)
        chunks.append(
            AIExportChunk(
                path=path,
                source_paths=list(dict.fromkeys(current_sources)),
                char_count=len(content),
            )
        )
        current_parts = []
        current_sources = []
        current_size = 0

    for source, text in source_texts:
        blocks = _split_source_text(source.relative_path, text, max_chunk_chars)
        for block in blocks:
            if current_parts and current_size + len(block) > max_chunk_chars:
                flush()
            current_parts.append(block)
            current_sources.append(Path(source.relative_path))
            current_size += len(block)
            if current_size >= max_chunk_chars:
                flush()
    flush()
    return chunks


def _split_source_text(relative_path: str, text: str, max_chunk_chars: int) -> list[str]:
    """Split one source file into headed text blocks."""
    header = f"## Source: {relative_path}\n\n"
    if len(header) + len(text) <= max_chunk_chars:
        return [header + text]

    available = max(1000, max_chunk_chars - len(header) - 80)
    blocks: list[str] = []
    start = 0
    part = 1
    while start < len(text):
        end = min(len(text), start + available)
        if end < len(text):
            newline = text.rfind("\n", start, end)
            if newline > start:
                end = newline
        chunk_text = text[start:end].strip()
        if chunk_text:
            blocks.append(f"{header}_Part {part}_\n\n{chunk_text}")
            part += 1
        start = max(end, start + 1)
    return blocks


def _attach_chunk_paths(sources: Sequence[AIExportSource], chunks: Sequence[AIExportChunk]) -> None:
    """Attach generated chunk paths to each included source."""
    for source in sources:
        source_path = Path(source.relative_path)
        source.chunk_files = [
            chunk.path for chunk in chunks if source_path in set(chunk.source_paths)
        ]


def _ai_review_markdown(
    package_type: str,
    package_dir: Path,
    sources: Sequence[AIExportSource],
    chunks: Sequence[AIExportChunk],
) -> str:
    """Create the main AI review Markdown file."""
    lines = [
        "# AI Review Export",
        "",
        f"- Package Type: {package_type}",
        f"- Source Package: {package_dir}",
        f"- Source Files Included: {len(sources)}",
        f"- Chunks Generated: {len(chunks)}",
        "",
        "## Review Guidance",
        "",
        _review_guidance(package_type),
        "",
        "## Source Files Included",
        "",
    ]
    lines.extend(f"- `{source.relative_path}` ({source.role or 'source'})" for source in sources)
    lines.extend(["", "## Key Review Sections", ""])
    lines.extend(_package_type_sections(package_type))
    lines.extend(["", "## Local File References", ""])
    lines.append("- See `source_index.md` for all included and excluded source files.")
    if chunks:
        lines.append("- See `chunks/` for deterministic chunk files.")
    return "\n".join(lines).rstrip() + "\n"


def _prompt_markdown(package_type: str) -> str:
    """Create a reusable user prompt for AI tools."""
    return "\n".join(
        [
            "# Prompt",
            "",
            "Review the provided Procore export files using only the local source files.",
            "",
            "Requirements:",
            "",
            "- Do not invent facts.",
            "- Cite local file names or section headings when making claims.",
            "- Separate confirmed facts from assumptions.",
            "- Flag missing information clearly.",
            "- Provide review assistance only, not final construction or legal judgment.",
            "- Ask for missing source files if the export is incomplete.",
            "",
            f"Detected package type: `{package_type}`",
            "",
        ]
    )


def _system_context_markdown(package_type: str) -> str:
    """Create safe system context for AI-assisted review."""
    return "\n".join(
        [
            "# System Context",
            "",
            "You are reviewing exported Procore project data.",
            "Use the local files as the source of truth.",
            "If information is missing, ask for the missing files or fields.",
            "Do not claim authority to approve, reject, or direct construction work.",
            "Do not provide legal advice.",
            "",
            f"Package type: `{package_type}`",
            "",
        ]
    )


def _write_checklists(output_dir: Path, package_type: str) -> list[Path]:
    """Write package-aware review checklists."""
    checklists = {
        "missing_information.md": _missing_information_checklist(package_type),
        "coordination_risks.md": _coordination_risks_checklist(package_type),
        "follow_up_questions.md": _follow_up_questions_checklist(package_type),
    }
    return [
        _write_markdown(output_dir / "checklists" / filename, content)
        for filename, content in checklists.items()
    ]


def _source_index_markdown(sources: Sequence[AIExportSource]) -> str:
    """Create source index Markdown."""
    lines = [
        "# Source Index",
        "",
        "| Path | Type | Size | Included | Role | Reason | Chunks |",
        "| --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for source in sources:
        chunk_names = ", ".join(path.name for path in source.chunk_files)
        lines.append(
            "| {path} | {type} | {size} | {included} | {role} | {reason} | {chunks} |".format(
                path=source.relative_path,
                type=source.file_type,
                size=source.size,
                included=source.included,
                role=source.role or "",
                reason=source.reason or "",
                chunks=chunk_names,
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def _review_guidance(package_type: str) -> str:
    """Return package-aware review guidance."""
    guidance = {
        "enhanced_rfi": (
            "Review the RFI overview, question/answer context, related references, "
            "possible missing information, possible risk flags, and reviewer questions."
        ),
        "enhanced_submittal": (
            "Review the submittal overview, approval status, spec and drawing "
            "references, related RFIs, possible missing information, risk flags, "
            "and suggested reviewer questions."
        ),
        "project_context": (
            "Review the available project sections, high-level counts, suggested "
            "review areas, and limitations or permission warnings."
        ),
    }
    return guidance.get(
        package_type,
        "Review the included local package files and flag missing context or assumptions.",
    )


def _package_type_sections(package_type: str) -> list[str]:
    """Return package-aware section bullets."""
    if package_type == "enhanced_rfi":
        return [
            "- RFI overview",
            "- Question and answer context",
            "- Related references",
            "- Possible missing information",
            "- Possible risk flags",
            "- Suggested reviewer questions",
        ]
    if package_type == "enhanced_submittal":
        return [
            "- Submittal overview",
            "- Approval or review status",
            "- Specification and drawing references",
            "- Related RFIs and context",
            "- Possible missing information",
            "- Possible risk flags",
            "- Suggested reviewer questions",
        ]
    if package_type == "project_context":
        return [
            "- Project overview",
            "- Available sections",
            "- High-level counts",
            "- Suggested review areas",
            "- Limitations or permission warnings",
        ]
    return ["- Available local source files", "- Missing information", "- Follow-up questions"]


def _missing_information_checklist(package_type: str) -> str:
    """Return a missing-information checklist."""
    items = [
        "Primary record title, number, and status are visible.",
        "Relevant attachments or source documents are included when needed.",
        "Responsible parties or reviewers are identifiable.",
        "Dates and current status are clear.",
    ]
    if package_type == "enhanced_rfi":
        items.append("RFI question and official answer fields are present.")
    if package_type == "enhanced_submittal":
        items.append("Submittal response, spec section, and approval fields are present.")
    return _checklist("Missing Information", items)


def _coordination_risks_checklist(package_type: str) -> str:
    """Return a coordination-risk checklist."""
    items = [
        "Related drawings, specifications, RFIs, and documents have been checked.",
        "Daily Logs or photos near the review date have been considered.",
        "Open or pending records are separated from closed records.",
    ]
    if package_type == "enhanced_rfi":
        items.append("Related submittals do not conflict with the RFI response.")
    if package_type == "enhanced_submittal":
        items.append("Related RFIs do not change the submittal review criteria.")
    return _checklist("Coordination Risks", items)


def _follow_up_questions_checklist(package_type: str) -> str:
    """Return follow-up question prompts."""
    items = [
        "What facts are confirmed by the local files?",
        "What assumptions require human confirmation?",
        "What source files should be requested next?",
    ]
    if package_type == "enhanced_rfi":
        items.append("What answer or reference is needed to close the RFI?")
    if package_type == "enhanced_submittal":
        items.append("What review decision or missing material should a reviewer address?")
    return _checklist("Follow-Up Questions", items)


def _checklist(title: str, items: Sequence[str]) -> str:
    """Render a Markdown checklist."""
    return "# " + title + "\n\n" + "\n".join(f"- [ ] {item}" for item in items) + "\n"


def _detect_source_role(relative_path: str) -> str:
    """Detect a source role from a relative path."""
    path = relative_path.casefold()
    if path == "rfi.json":
        return "primary_rfi"
    if path == "submittal.json":
        return "primary_submittal"
    if path.endswith("review_context.md"):
        return "review_context"
    if "related/spec" in path:
        return "related_specs"
    if "related/drawing" in path:
        return "related_drawings"
    if "related/daily" in path:
        return "daily_logs"
    if path.endswith("manifest.json"):
        return "manifest"
    return "source"


def _build_warnings(sources: Sequence[AIExportSource]) -> list[str]:
    """Build non-fatal export warnings."""
    warnings: list[str] = []
    if not any(source.included for source in sources):
        warnings.append("No supported source files were included.")
    excluded_count = sum(1 for source in sources if not source.included)
    if excluded_count:
        warnings.append(f"{excluded_count} source file(s) were excluded.")
    return warnings


def _normalize_extensions(value: Sequence[str] | str | None) -> tuple[str, ...]:
    """Normalize source extensions."""
    items = _normalize_list(value) if value is not None else list(DEFAULT_SOURCE_EXTENSIONS)
    return tuple(item if item.startswith(".") else f".{item}" for item in items)


def _normalize_list(value: Sequence[str] | str | None) -> list[str]:
    """Normalize comma-separated values or string sequences."""
    if value is None:
        return []
    raw = value.split(",") if isinstance(value, str) else list(value)
    return [item.strip().casefold() for item in raw if item.strip()]


def _matching_pattern(relative_path: str, patterns: Sequence[str]) -> str | None:
    """Return the matching glob pattern, if any."""
    for pattern in patterns:
        if fnmatch.fnmatch(relative_path, pattern):
            return pattern
    return None


def _read_json_if_possible(path: Path) -> object | None:
    """Read JSON when possible."""
    if not path.exists():
        return None
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
        return payload
    except (OSError, json.JSONDecodeError):
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
