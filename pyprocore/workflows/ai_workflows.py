"""Model-agnostic local AI workflow helpers for PyProcore.

These helpers prepare prompts, checklists, chunk manifests, and small local
packages from already-available text or dictionaries. They never call Procore,
external model APIs, MCP execution tools, or vector databases.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field

from pyprocore.core.exceptions import ValidationError
from pyprocore.models.base import ProcoreModel
from pyprocore.workflows.utils import json_default

AiWorkflowKind = Literal[
    "rfi_review",
    "submittal_review",
    "project_qa",
    "drawing_spec_comparison",
    "field_issue_summary",
    "change_risk_review",
    "engineering_assistant_context",
    "vector_export",
]

DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 120


class AiWorkflowInput(ProcoreModel):
    """Local input used to build a model-agnostic AI workflow package.

    Attributes:
        title: Human-readable package title.
        workflow: Workflow pattern such as ``rfi_review`` or ``project_qa``.
        summary: Short local summary or placeholder context.
        records: Local structured records already exported by the user.
        source_files: Optional local source file paths for user review.
        notes: Optional notes for the human reviewer or downstream system.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    title: str
    workflow: AiWorkflowKind
    summary: str
    records: list[dict[str, object]] = Field(default_factory=list)
    source_files: list[Path] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AiWorkflowPrompt(ProcoreModel):
    """Prompt text prepared for a user-selected model system.

    Attributes:
        title: Human-readable prompt title.
        workflow: Workflow pattern this prompt supports.
        system_context: Safety and role context.
        user_prompt: Task prompt for the user's chosen AI/model system.
        checklist: Human review checklist that should stay outside automation.
    """

    title: str
    workflow: AiWorkflowKind
    system_context: str
    user_prompt: str
    checklist: list[str] = Field(default_factory=list)


class AiWorkflowChecklist(ProcoreModel):
    """Safety checklist for model-agnostic AI workflow usage.

    Attributes:
        title: Checklist title.
        items: Review items for the human operator.
        boundaries: Safety boundaries that PyProcore preserves.
    """

    title: str
    items: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)


class AiWorkflowPackage(ProcoreModel):
    """Local AI workflow package metadata.

    Attributes:
        name: Package name.
        workflow: Workflow pattern this package supports.
        created_at: UTC creation timestamp.
        prompt: Prompt prepared for the user's model stack.
        checklist: Human review and safety checklist.
        files_written: Local files written by the package helper.
        manifest_path: Optional manifest path when written to disk.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    name: str
    workflow: AiWorkflowKind
    created_at: str
    prompt: AiWorkflowPrompt
    checklist: AiWorkflowChecklist
    files_written: list[Path] = Field(default_factory=list)
    manifest_path: Path | None = None


class VectorExportChunk(ProcoreModel):
    """One local text chunk prepared for optional vector indexing elsewhere."""

    id: str
    text: str
    start: int
    end: int
    metadata: dict[str, object] = Field(default_factory=dict)


class VectorIndexManifest(ProcoreModel):
    """Manifest for local chunk files that a user may index with their own stack."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    created_at: str
    source_name: str
    chunk_count: int
    chunk_size: int
    overlap: int
    chunks: list[VectorExportChunk] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def build_rfi_review_prompt_pack(
    rfi: Mapping[str, object] | None = None,
    context: str = "Placeholder project context.",
) -> AiWorkflowPrompt:
    """Build a local prompt pack for an RFI review assistant pattern.

    Args:
        rfi: Optional already-exported local RFI dictionary.
        context: Local context text to include in the prompt.

    Returns:
        A prompt object that can be serialized to JSON or Markdown.
    """
    number = _record_value(rfi, "number", "RFI-PLACEHOLDER")
    title = _record_value(rfi, "title", "Placeholder RFI title")
    return _build_prompt(
        title=f"RFI Review Assistant Package: {number}",
        workflow="rfi_review",
        objective=(
            f"Review {number}: {title}. Summarize the issue, identify missing "
            "information, list affected drawings/specs if present, and draft "
            "questions for human review."
        ),
        context=context,
        checklist=[
            "Confirm the RFI payload was exported from the intended project.",
            "Redact private or sensitive fields before sharing externally.",
            "Keep final RFI responses under human reviewer control.",
        ],
    )


def build_submittal_review_prompt_pack(
    submittal: Mapping[str, object] | None = None,
    context: str = "Placeholder project context.",
) -> AiWorkflowPrompt:
    """Build a local prompt pack for a submittal review assistant pattern."""
    number = _record_value(submittal, "number", "SUBMITTAL-PLACEHOLDER")
    title = _record_value(submittal, "title", "Placeholder submittal title")
    return _build_prompt(
        title=f"Submittal Review Assistant Package: {number}",
        workflow="submittal_review",
        objective=(
            f"Review {number}: {title}. Summarize scope, identify review risks, "
            "compare against provided specifications, and list human follow-up "
            "questions."
        ),
        context=context,
        checklist=[
            "Confirm specification references are from the same project.",
            "Do not treat AI output as approval, rejection, or direction.",
            "Route final decisions through the normal submittal review process.",
        ],
    )


def build_project_qa_prompt_pack(
    project_summary: str = "Placeholder project context package summary.",
) -> AiWorkflowPrompt:
    """Build a local prompt pack for project context Q&A."""
    return _build_prompt(
        title="Project Context Q&A Package",
        workflow="project_qa",
        objective=(
            "Answer questions using only the provided local project context. "
            "Cite source filenames or sections and say when information is missing."
        ),
        context=project_summary,
        checklist=[
            "Include only approved local exports in the context bundle.",
            "Ask the model to cite local source names.",
            "Use human review for any operational decision.",
        ],
    )


def build_drawing_spec_comparison_prompt_pack(
    drawing_summary: str = "Placeholder drawing notes.",
    specification_summary: str = "Placeholder specification notes.",
) -> AiWorkflowPrompt:
    """Build a local prompt pack for drawing/spec comparison."""
    return _build_prompt(
        title="Drawing And Specification Comparison Package",
        workflow="drawing_spec_comparison",
        objective=(
            "Compare the provided drawing notes and specification notes. Flag "
            "potential conflicts, missing references, and review questions."
        ),
        context=(
            f"Drawing notes:\n{drawing_summary}\n\n"
            f"Specification notes:\n{specification_summary}"
        ),
        checklist=[
            "Verify drawing revisions and specification revisions match.",
            "Treat conflicts as review leads, not confirmed defects.",
            "Keep engineering judgment with qualified reviewers.",
        ],
    )


def build_field_issue_summary_prompt_pack(
    issue_notes: str = "Placeholder field issue notes.",
) -> AiWorkflowPrompt:
    """Build a local prompt pack for field issue summarization."""
    return _build_prompt(
        title="Field Issue Summary Package",
        workflow="field_issue_summary",
        objective=(
            "Summarize field issue notes into timeline, impacted work areas, "
            "open questions, possible related records, and recommended next review steps."
        ),
        context=issue_notes,
        checklist=[
            "Confirm notes do not include private personal information.",
            "Check linked RFIs, observations, photos, and daily logs manually.",
            "Do not generate directives to field teams automatically.",
        ],
    )


def build_change_risk_review_prompt_pack(
    change_context: str = "Placeholder change event or financial context.",
) -> AiWorkflowPrompt:
    """Build a local prompt pack for change-risk review."""
    return _build_prompt(
        title="Change-Risk Review Package",
        workflow="change_risk_review",
        objective=(
            "Review change context for scope, schedule, cost, documentation, "
            "and approval-chain risks. Produce a human-review checklist."
        ),
        context=change_context,
        checklist=[
            "Confirm source records are read-only exports.",
            "Do not infer contractual entitlement from AI output alone.",
            "Route risk findings through the project controls process.",
        ],
    )


def build_engineering_assistant_context_bundle(
    context: str = "Placeholder engineering context.",
) -> AiWorkflowPrompt:
    """Build a local prompt pack for an engineering assistant context bundle."""
    return _build_prompt(
        title="Engineering Assistant Context Bundle",
        workflow="engineering_assistant_context",
        objective=(
            "Organize the provided engineering context into assumptions, known facts, "
            "missing inputs, relevant references, and questions for a licensed reviewer."
        ),
        context=context,
        checklist=[
            "Keep calculations and design decisions outside automated output.",
            "Confirm source drawings/specs are current before review.",
            "Use qualified human review before acting on any recommendation.",
        ],
    )


def build_ai_workflow_safety_checklist() -> AiWorkflowChecklist:
    """Return the standard Phase 12 safety checklist."""
    return AiWorkflowChecklist(
        title="PyProcore AI Workflow Safety Checklist",
        items=[
            "Use local exported data only.",
            "Review and redact private project data before sharing externally.",
            "Send only selected files to the user's chosen model stack.",
            "Keep a human reviewer in the loop for every conclusion.",
            "Do not use AI output as approval, rejection, field direction, or contract action.",
        ],
        boundaries=[
            "PyProcore does not call external AI/model APIs by default.",
            "PyProcore does not require AI framework or vector database dependencies.",
            "Procore tool execution remains disabled.",
            "MCP remains discovery-only.",
            "No Procore write actions are performed.",
        ],
    )


def build_vector_index_manifest(
    text: str,
    source_name: str = "placeholder-source.md",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
    metadata: Mapping[str, object] | None = None,
) -> VectorIndexManifest:
    """Build a local manifest for optional vector indexing in user-owned systems.

    Args:
        text: Local text to chunk.
        source_name: Display name of the source text.
        chunk_size: Maximum characters per chunk.
        overlap: Number of characters to overlap between chunks.
        metadata: Metadata copied to every chunk.

    Returns:
        A manifest with chunks and safety notes.
    """
    chunks = chunk_text_for_vector_export(
        text,
        source_name=source_name,
        chunk_size=chunk_size,
        overlap=overlap,
        metadata=metadata,
    )
    return VectorIndexManifest(
        created_at=datetime.now(UTC).isoformat(),
        source_name=source_name,
        chunk_count=len(chunks),
        chunk_size=chunk_size,
        overlap=overlap,
        chunks=chunks,
        notes=[
            "This manifest is local-only and model-agnostic.",
            "Index these chunks only in a user-selected vector system.",
            "Review and redact private data before sending it outside your environment.",
        ],
    )


def chunk_text_for_vector_export(
    text: str,
    source_name: str = "placeholder-source.md",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
    metadata: Mapping[str, object] | None = None,
) -> list[VectorExportChunk]:
    """Split local text into deterministic chunks for optional vector export.

    Args:
        text: Text to split.
        source_name: Source name included in each chunk ID.
        chunk_size: Maximum characters per chunk.
        overlap: Character overlap between adjacent chunks.
        metadata: Metadata copied to each chunk.

    Returns:
        Ordered chunk models.

    Raises:
        ValidationError: If chunk settings are invalid.
    """
    if chunk_size <= 0:
        raise ValidationError("chunk_size must be a positive integer.")
    if overlap < 0:
        raise ValidationError("overlap must be zero or a positive integer.")
    if overlap >= chunk_size:
        raise ValidationError("overlap must be smaller than chunk_size.")

    normalized = text.strip()
    if not normalized:
        return []

    chunks: list[VectorExportChunk] = []
    start = 0
    slug = _slugify(source_name)
    shared_metadata = dict(metadata or {})
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        if end < len(normalized):
            boundary = normalized.rfind("\n", start, end)
            if boundary <= start:
                boundary = normalized.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        chunk_text = normalized[start:end].strip()
        if chunk_text:
            chunk_number = len(chunks) + 1
            chunks.append(
                VectorExportChunk(
                    id=f"{slug}-{chunk_number:04d}",
                    text=chunk_text,
                    start=start,
                    end=end,
                    metadata={"source_name": source_name, **shared_metadata},
                )
            )
        if end >= len(normalized):
            break
        next_start = max(0, end - overlap)
        start = next_start if next_start > start else end
    return chunks


def write_ai_workflow_package(
    workflow_input: AiWorkflowInput,
    output_dir: Path | str,
    overwrite: bool = False,
) -> AiWorkflowPackage:
    """Write a small local prompt/checklist/manifest package.

    Args:
        workflow_input: Local workflow input.
        output_dir: Directory to write.
        overwrite: Whether existing package files may be overwritten.

    Returns:
        Package metadata with paths written.
    """
    root = Path(output_dir)
    if root.exists() and any(root.iterdir()) and not overwrite:
        raise ValidationError(f"Output directory already exists and is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)

    prompt = _prompt_for_input(workflow_input)
    checklist = build_ai_workflow_safety_checklist()
    files_written = [
        _write_text(root / "prompt.md", _prompt_to_markdown(prompt)),
        _write_json(root / "prompt.json", prompt.model_dump(mode="json")),
        _write_text(root / "safety_checklist.md", _checklist_to_markdown(checklist)),
        _write_json(root / "input.json", workflow_input.model_dump(mode="json")),
    ]

    package = AiWorkflowPackage(
        name=workflow_input.title,
        workflow=workflow_input.workflow,
        created_at=datetime.now(UTC).isoformat(),
        prompt=prompt,
        checklist=checklist,
        files_written=files_written,
    )
    manifest_path = _write_json(root / "manifest.json", package.model_dump(mode="json"))
    package.files_written.append(manifest_path)
    package.manifest_path = manifest_path
    return package


def _prompt_for_input(workflow_input: AiWorkflowInput) -> AiWorkflowPrompt:
    """Build a prompt from typed workflow input."""
    records_summary = _records_summary(workflow_input.records)
    context = "\n\n".join(
        part
        for part in [
            workflow_input.summary,
            records_summary,
            "\n".join(f"- {note}" for note in workflow_input.notes),
        ]
        if part
    )
    if workflow_input.workflow == "rfi_review":
        return build_rfi_review_prompt_pack(context=context)
    if workflow_input.workflow == "submittal_review":
        return build_submittal_review_prompt_pack(context=context)
    if workflow_input.workflow == "project_qa":
        return build_project_qa_prompt_pack(context)
    if workflow_input.workflow == "drawing_spec_comparison":
        return build_drawing_spec_comparison_prompt_pack(context, "Add local spec notes here.")
    if workflow_input.workflow == "field_issue_summary":
        return build_field_issue_summary_prompt_pack(context)
    if workflow_input.workflow == "change_risk_review":
        return build_change_risk_review_prompt_pack(context)
    if workflow_input.workflow == "engineering_assistant_context":
        return build_engineering_assistant_context_bundle(context)
    return _build_prompt(
        title="Vector Export Pattern",
        workflow="vector_export",
        objective="Prepare local text chunks for a user-selected vector index.",
        context=context,
        checklist=build_ai_workflow_safety_checklist().items,
    )


def _build_prompt(
    title: str,
    workflow: AiWorkflowKind,
    objective: str,
    context: str,
    checklist: Sequence[str],
) -> AiWorkflowPrompt:
    """Build a standardized prompt object."""
    system_context = (
        "You are reviewing a local PyProcore export. Use only the provided "
        "context. Do not claim authority to approve, reject, submit, update, "
        "or direct Procore work. If information is missing, say so."
    )
    user_prompt = (
        f"Objective:\n{objective}\n\n"
        f"Local context:\n{context}\n\n"
        "Expected output:\n"
        "- Short summary\n"
        "- Key facts and source references\n"
        "- Risks or conflicts to review\n"
        "- Missing information\n"
        "- Questions for a human reviewer\n"
    )
    return AiWorkflowPrompt(
        title=title,
        workflow=workflow,
        system_context=system_context,
        user_prompt=user_prompt,
        checklist=list(checklist),
    )


def _prompt_to_markdown(prompt: AiWorkflowPrompt) -> str:
    """Render a prompt object as Markdown."""
    checklist = "\n".join(f"- {item}" for item in prompt.checklist)
    return (
        f"# {prompt.title}\n\n"
        "## System Context\n\n"
        f"{prompt.system_context}\n\n"
        "## User Prompt\n\n"
        f"{prompt.user_prompt}\n"
        "## Human Review Checklist\n\n"
        f"{checklist}\n"
    )


def _checklist_to_markdown(checklist: AiWorkflowChecklist) -> str:
    """Render a checklist as Markdown."""
    items = "\n".join(f"- {item}" for item in checklist.items)
    boundaries = "\n".join(f"- {boundary}" for boundary in checklist.boundaries)
    return f"# {checklist.title}\n\n## Checklist\n\n{items}\n\n## Boundaries\n\n{boundaries}\n"


def _records_summary(records: Sequence[Mapping[str, object]]) -> str:
    """Summarize local records without assuming a schema."""
    if not records:
        return ""
    lines = ["Local records:"]
    for index, record in enumerate(records, start=1):
        title = _record_value(record, "title", _record_value(record, "name", "Untitled"))
        number = _record_value(record, "number", _record_value(record, "id", f"item-{index}"))
        lines.append(f"- {number}: {title}")
    return "\n".join(lines)


def _record_value(
    record: Mapping[str, object] | None,
    key: str,
    default: object,
) -> str:
    """Return one local record value as text."""
    if record is None:
        return str(default)
    value = record.get(key, default)
    if value is None:
        return str(default)
    return str(value)


def _slugify(value: str) -> str:
    """Return a stable ASCII-ish slug."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "source"


def _write_json(path: Path, payload: object) -> Path:
    """Write JSON payload and return the path."""
    path.write_text(json.dumps(payload, indent=2, default=json_default) + "\n", encoding="utf-8")
    return path


def _write_text(path: Path, content: str) -> Path:
    """Write text content and return the path."""
    path.write_text(content, encoding="utf-8")
    return path
