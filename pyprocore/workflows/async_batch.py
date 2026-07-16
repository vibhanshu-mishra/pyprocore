"""Async multi-project batch helpers for read-only Procore workflows."""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import ConfigDict, Field

from pyprocore.async_client import AsyncProcore
from pyprocore.core.exceptions import ValidationError
from pyprocore.models.base import ProcoreModel
from pyprocore.services.files import sanitize_filename
from pyprocore.workflows.async_exports import (
    DEFAULT_ASYNC_CONCURRENCY,
    async_export_records_csv,
    async_export_records_jsonl,
)
from pyprocore.workflows.utils import model_to_dict

AsyncBatchOutputFormat = Literal["csv", "jsonl"]
AsyncBatchStatus = Literal["completed", "failed", "skipped", "dry_run"]
AsyncBatchSeverity = Literal["error", "warning", "info"]

SUPPORTED_ASYNC_BATCH_RESOURCES: tuple[str, ...] = (
    "rfis",
    "submittals",
    "documents",
    "drawings",
    "specification_sections",
)

SECRET_PATTERN = re.compile(
    r"(access[_-]?token|refresh[_-]?token|client[_-]?secret|authorization|password|api[_-]?key)"
    r"([\"'\s:=]+)([^\"'\s,}]+)",
    flags=re.IGNORECASE,
)
URL_WITH_QUERY_PATTERN = re.compile(r"https?://[^\s\"']+\?[^\s\"']+")


class AsyncBatchFinding(ProcoreModel):
    """One validation, planning, or runtime finding for an async batch."""

    severity: AsyncBatchSeverity
    code: str
    message: str


class AsyncBatchPlan(ProcoreModel):
    """Local plan for read-only async multi-project exports.

    Attributes:
        plan_name: Human-readable plan name.
        company_id: Procore company ID.
        project_ids: Project IDs to include.
        resources: Supported project-scoped resources to collect or export.
        output_dir: Local output directory for file exports.
        output_format: Export format for local files.
        max_concurrency: Maximum project/resource tasks to run at once.
        continue_on_error: Whether independent tasks continue after failures.
        dry_run: Whether planning should avoid Procore calls and file writes.
        include_timestamp: Whether planned output paths include a timestamp folder.
        per_project_subfolders: Whether outputs are grouped by project.
        resource_options: Optional per-resource read options.
        skip_completed: Whether completed pairs from a previous manifest are skipped.
        previous_manifest_path: Optional local manifest used for simple resume planning.
        notes: Optional operator notes.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, arbitrary_types_allowed=True)

    plan_name: str = "async-multi-project-export"
    company_id: int
    project_ids: list[int] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)
    output_dir: Path = Path("./exports/async-batch")
    output_format: AsyncBatchOutputFormat = "jsonl"
    max_concurrency: int = DEFAULT_ASYNC_CONCURRENCY
    continue_on_error: bool = True
    dry_run: bool = True
    include_timestamp: bool = False
    per_project_subfolders: bool = True
    resource_options: dict[str, dict[str, Any]] = Field(default_factory=dict)
    skip_completed: bool = True
    previous_manifest_path: Path | None = None
    notes: str | None = None


class AsyncProjectResult(ProcoreModel):
    """Result summary for one project in an async batch."""

    project_id: int
    status: AsyncBatchStatus
    resources: list[str] = Field(default_factory=list)
    record_count: int = 0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AsyncBatchResourceResult(ProcoreModel):
    """Result for one project/resource pair in an async batch."""

    project_id: int
    resource: str
    status: AsyncBatchStatus
    output_path: Path | None = None
    output_format: AsyncBatchOutputFormat | None = None
    record_count: int = 0
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)
    records: list[dict[str, Any]] = Field(default_factory=list, exclude=True)


class AsyncBatchManifest(ProcoreModel):
    """Serializable manifest for async batch planning or execution."""

    plan_name: str
    generated_at: str
    dry_run: bool
    company_id: int
    project_ids: list[int] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)
    output_dir: Path
    output_format: AsyncBatchOutputFormat
    max_concurrency: int
    continue_on_error: bool
    include_timestamp: bool
    per_project_subfolders: bool
    results: list[AsyncBatchResourceResult] = Field(default_factory=list)
    projects: list[AsyncProjectResult] = Field(default_factory=list)
    findings: list[AsyncBatchFinding] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)

    @property
    def completed_count(self) -> int:
        """Return completed resource-pair count."""
        return sum(1 for result in self.results if result.status == "completed")

    @property
    def failed_count(self) -> int:
        """Return failed resource-pair count."""
        return sum(1 for result in self.results if result.status == "failed")

    @property
    def skipped_count(self) -> int:
        """Return skipped resource-pair count."""
        return sum(1 for result in self.results if result.status == "skipped")


class AsyncBatchResult(ProcoreModel):
    """Top-level result for an async batch run."""

    plan: AsyncBatchPlan
    manifest: AsyncBatchManifest


def load_async_batch_plan(path: Path | str) -> AsyncBatchPlan:
    """Load an async batch plan from JSON without calling Procore.

    Args:
        path: Local JSON plan path.

    Returns:
        Parsed async batch plan.

    Raises:
        ValidationError: If the file cannot be loaded or parsed.
    """
    plan_path = Path(path)
    if plan_path.suffix.casefold() != ".json":
        raise ValidationError("Async batch plan files must use .json.")
    try:
        payload = json.loads(plan_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"Async batch plan file not found: {plan_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Async batch plan JSON is invalid: {exc.msg}") from exc
    except OSError as exc:
        raise ValidationError(f"Could not read async batch plan {plan_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValidationError("Async batch plan must be a JSON object.")
    try:
        return AsyncBatchPlan.model_validate(payload)
    except ValueError as exc:
        raise ValidationError(f"Async batch plan is invalid: {exc}") from exc


def build_async_batch_plan(
    *,
    company_id: int,
    project_ids: Sequence[int],
    resources: Sequence[str],
    output_dir: Path | str = Path("./exports/async-batch"),
    output_format: AsyncBatchOutputFormat = "jsonl",
    plan_name: str = "async-multi-project-export",
    max_concurrency: int = DEFAULT_ASYNC_CONCURRENCY,
    continue_on_error: bool = True,
    dry_run: bool = True,
    include_timestamp: bool = False,
    per_project_subfolders: bool = True,
    resource_options: Mapping[str, Mapping[str, Any]] | None = None,
) -> AsyncBatchPlan:
    """Build a typed async batch plan from simple values."""
    return AsyncBatchPlan(
        plan_name=plan_name,
        company_id=company_id,
        project_ids=list(project_ids),
        resources=list(resources),
        output_dir=Path(output_dir),
        output_format=output_format,
        max_concurrency=max_concurrency,
        continue_on_error=continue_on_error,
        dry_run=dry_run,
        include_timestamp=include_timestamp,
        per_project_subfolders=per_project_subfolders,
        resource_options={
            resource: dict(options) for resource, options in (resource_options or {}).items()
        },
    )


def validate_async_batch_plan(plan: AsyncBatchPlan | Path | str) -> list[AsyncBatchFinding]:
    """Validate an async batch plan without calling Procore."""
    batch_plan = _coerce_plan(plan)
    findings: list[AsyncBatchFinding] = []
    if batch_plan.company_id <= 0:
        findings.append(_finding("error", "invalid_company_id", "company_id must be positive."))
    if not batch_plan.project_ids:
        findings.append(
            _finding("error", "missing_project_ids", "At least one project_id is required.")
        )
    for project_id in batch_plan.project_ids:
        if project_id <= 0:
            findings.append(
                _finding("error", "invalid_project_id", "project_ids must be positive integers.")
            )
            break
    if not batch_plan.resources:
        findings.append(
            _finding("error", "missing_resources", "At least one resource is required.")
        )
    for resource in batch_plan.resources:
        if resource not in SUPPORTED_ASYNC_BATCH_RESOURCES:
            findings.append(
                _finding(
                    "error",
                    "unknown_resource",
                    f"Unsupported async batch resource '{resource}'. Supported resources: "
                    f"{', '.join(SUPPORTED_ASYNC_BATCH_RESOURCES)}.",
                )
            )
    if batch_plan.output_format not in ("csv", "jsonl"):
        findings.append(
            _finding("error", "unknown_output_format", "output_format must be csv or jsonl.")
        )
    _validate_output_dir(batch_plan, findings)
    if batch_plan.max_concurrency <= 0:
        findings.append(
            _finding("error", "invalid_concurrency", "max_concurrency must be greater than zero.")
        )
    elif batch_plan.max_concurrency > 12:
        findings.append(
            _finding(
                "warning",
                "high_concurrency",
                "max_concurrency is high. Start conservatively to avoid API pressure.",
            )
        )
    if len(batch_plan.project_ids) * max(1, len(batch_plan.resources)) > 25:
        findings.append(
            _finding(
                "warning",
                "broad_async_batch",
                "This plan covers many project/resource pairs. Review access, "
                "runtime, and storage.",
            )
        )
    if not batch_plan.dry_run:
        findings.append(
            _finding(
                "info",
                "live_async_export_plan",
                "Library execution may call Procore when dry_run is false; "
                "CLI dry-run stays local.",
            )
        )
    return findings


def build_async_batch_dry_run_manifest(plan: AsyncBatchPlan | Path | str) -> AsyncBatchManifest:
    """Build a dry-run manifest without calling Procore or writing export files."""
    batch_plan = _coerce_plan(plan)
    findings = validate_async_batch_plan(batch_plan)
    results = [
        AsyncBatchResourceResult(
            project_id=project_id,
            resource=resource,
            status="dry_run",
            output_path=_resource_output_path(batch_plan, project_id, resource),
            output_format=batch_plan.output_format,
        )
        for project_id in batch_plan.project_ids
        for resource in batch_plan.resources
    ]
    return _build_manifest(batch_plan, results=results, findings=findings, dry_run=True)


def explain_async_batch_plan(plan: AsyncBatchPlan | Path | str) -> str:
    """Return a human-readable dry-run explanation for an async batch plan."""
    manifest = build_async_batch_dry_run_manifest(plan)
    valid = not any(finding.severity == "error" for finding in manifest.findings)
    lines = [
        "Async batch dry run.",
        f"Plan: {manifest.plan_name}",
        f"Valid: {valid}",
        f"Company: {manifest.company_id}",
        f"Projects: {', '.join(str(item) for item in manifest.project_ids) or 'none'}",
        f"Resources: {', '.join(manifest.resources) or 'none'}",
        f"Output format: {manifest.output_format}",
        f"Output folder: {manifest.output_dir}",
        f"Max concurrency: {manifest.max_concurrency}",
        f"Planned project/resource files: {len(manifest.results)}",
        "Mode: local dry-run only; no Procore API calls were made.",
        "",
        "Safety notes:",
    ]
    lines.extend(f"- {note}" for note in manifest.safety_notes)
    if manifest.findings:
        lines.append("")
        lines.append("Findings:")
        lines.extend(
            f"- {finding.severity.upper()}: {finding.message}" for finding in manifest.findings
        )
    return "\n".join(lines)


def sample_async_batch_plan() -> AsyncBatchPlan:
    """Return a safe placeholder async batch plan."""
    return AsyncBatchPlan(
        plan_name="sample-async-multi-project-export",
        company_id=12345,
        project_ids=[67890, 11111],
        resources=["rfis", "submittals", "documents"],
        output_dir=Path("./exports/async-batch/sample"),
        output_format="jsonl",
        max_concurrency=3,
        continue_on_error=True,
        dry_run=True,
        include_timestamp=False,
        per_project_subfolders=True,
        notes="Placeholder-only sample. Replace IDs only after reviewing permissions.",
    )


def sample_async_batch_plan_json() -> str:
    """Return a safe placeholder async batch plan as pretty JSON."""
    return json.dumps(sample_async_batch_plan().model_dump(mode="json"), indent=2) + "\n"


def write_async_batch_manifest(manifest: AsyncBatchManifest, output_path: Path | str) -> Path:
    """Write an async batch manifest to a local JSON file."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(async_batch_manifest_to_json(manifest, pretty=True), encoding="utf-8")
    return destination


def async_batch_manifest_to_json(manifest: AsyncBatchManifest, *, pretty: bool = True) -> str:
    """Serialize an async batch manifest without excluded in-memory records."""
    indent = 2 if pretty else None
    return json.dumps(manifest.model_dump(mode="json"), indent=indent, default=str) + "\n"


async def async_collect_project_resources(
    client: AsyncProcore,
    company_id: int,
    project_id: int,
    resources: Sequence[str],
    *,
    resource_options: Mapping[str, Mapping[str, Any]] | None = None,
    continue_on_error: bool = True,
) -> list[AsyncBatchResourceResult]:
    """Collect supported resources for one project without writing files."""
    results: list[AsyncBatchResourceResult] = []
    for resource in resources:
        try:
            records = await _fetch_resource(
                client,
                company_id,
                project_id,
                resource,
                dict((resource_options or {}).get(resource, {})),
            )
            results.append(
                AsyncBatchResourceResult(
                    project_id=project_id,
                    resource=resource,
                    status="completed",
                    record_count=len(records),
                    records=[model_to_dict(record) for record in records],
                )
            )
        except Exception as exc:
            results.append(
                AsyncBatchResourceResult(
                    project_id=project_id,
                    resource=resource,
                    status="failed",
                    error=_redact_error(exc),
                )
            )
            if not continue_on_error:
                raise
    return results


async def async_collect_multi_project_resources(
    client: AsyncProcore,
    company_id: int,
    project_ids: Sequence[int],
    resources: Sequence[str],
    *,
    max_concurrency: int = DEFAULT_ASYNC_CONCURRENCY,
    continue_on_error: bool = True,
    resource_options: Mapping[str, Mapping[str, Any]] | None = None,
) -> AsyncBatchManifest:
    """Collect supported resources across projects without writing files."""
    plan = build_async_batch_plan(
        company_id=company_id,
        project_ids=project_ids,
        resources=resources,
        max_concurrency=max_concurrency,
        continue_on_error=continue_on_error,
        dry_run=False,
        resource_options=resource_options,
    )
    return await async_run_project_batch(client, plan, collect_only=True)


async def async_run_project_batch(
    client: AsyncProcore,
    plan: AsyncBatchPlan | Path | str,
    *,
    collect_only: bool = False,
    resume_manifest: AsyncBatchManifest | Path | str | None = None,
) -> AsyncBatchManifest:
    """Run a read-only async batch collection or export.

    Dry-run plans return a local manifest without Procore calls. Non-dry-run
    plans call the provided async client and optionally write local CSV/JSONL
    files. No Procore write, upload, approval, or mutation endpoints are used.
    """
    batch_plan = _coerce_plan(plan)
    findings = validate_async_batch_plan(batch_plan)
    if any(finding.severity == "error" for finding in findings):
        raise ValidationError("Async batch plan has validation errors.")
    if batch_plan.dry_run:
        return build_async_batch_dry_run_manifest(batch_plan)

    completed_pairs = _completed_pairs(resume_manifest or batch_plan.previous_manifest_path)
    semaphore = asyncio.Semaphore(max(1, batch_plan.max_concurrency))
    results: list[AsyncBatchResourceResult] = []

    async def run_pair(project_id: int, resource: str) -> None:
        async with semaphore:
            if batch_plan.skip_completed and (project_id, resource) in completed_pairs:
                results.append(
                    AsyncBatchResourceResult(
                        project_id=project_id,
                        resource=resource,
                        status="skipped",
                        output_path=(
                            None
                            if collect_only
                            else _resource_output_path(batch_plan, project_id, resource)
                        ),
                        output_format=batch_plan.output_format,
                    )
                )
                return
            try:
                records = await _fetch_resource(
                    client,
                    batch_plan.company_id,
                    project_id,
                    resource,
                    batch_plan.resource_options.get(resource, {}),
                )
                output_path = None
                if not collect_only:
                    output_path = _resource_output_path(batch_plan, project_id, resource)
                    await _write_records(records, output_path, resource, batch_plan.output_format)
                results.append(
                    AsyncBatchResourceResult(
                        project_id=project_id,
                        resource=resource,
                        status="completed",
                        output_path=output_path,
                        output_format=batch_plan.output_format if not collect_only else None,
                        record_count=len(records),
                        records=[model_to_dict(record) for record in records],
                    )
                )
            except Exception as exc:
                results.append(
                    AsyncBatchResourceResult(
                        project_id=project_id,
                        resource=resource,
                        status="failed",
                        output_path=(
                            None
                            if collect_only
                            else _resource_output_path(batch_plan, project_id, resource)
                        ),
                        output_format=batch_plan.output_format if not collect_only else None,
                        error=_redact_error(exc),
                    )
                )
                if not batch_plan.continue_on_error:
                    raise

    await asyncio.gather(
        *(
            run_pair(project_id, resource)
            for project_id in batch_plan.project_ids
            for resource in batch_plan.resources
        )
    )
    return _build_manifest(
        batch_plan,
        results=sorted(results, key=lambda item: (item.project_id, item.resource)),
        findings=findings,
        dry_run=False,
    )


async def async_export_multi_project_resources(
    client: AsyncProcore,
    plan: AsyncBatchPlan | Path | str,
    *,
    resume_manifest: AsyncBatchManifest | Path | str | None = None,
) -> AsyncBatchManifest:
    """Export supported resources for multiple projects to local CSV/JSONL files."""
    return await async_run_project_batch(client, plan, resume_manifest=resume_manifest)


async def async_export_multi_project_rfis(
    client: AsyncProcore,
    company_id: int,
    project_ids: Sequence[int],
    output_dir: Path | str,
    **options: Any,
) -> AsyncBatchManifest:
    """Export RFIs for multiple projects."""
    return await _export_one_resource(client, company_id, project_ids, output_dir, "rfis", options)


async def async_export_multi_project_submittals(
    client: AsyncProcore,
    company_id: int,
    project_ids: Sequence[int],
    output_dir: Path | str,
    **options: Any,
) -> AsyncBatchManifest:
    """Export submittals for multiple projects."""
    return await _export_one_resource(
        client, company_id, project_ids, output_dir, "submittals", options
    )


async def async_export_multi_project_documents(
    client: AsyncProcore,
    company_id: int,
    project_ids: Sequence[int],
    output_dir: Path | str,
    **options: Any,
) -> AsyncBatchManifest:
    """Export documents for multiple projects."""
    return await _export_one_resource(
        client, company_id, project_ids, output_dir, "documents", options
    )


async def async_export_multi_project_drawings(
    client: AsyncProcore,
    company_id: int,
    project_ids: Sequence[int],
    output_dir: Path | str,
    **options: Any,
) -> AsyncBatchManifest:
    """Export drawings for multiple projects."""
    return await _export_one_resource(
        client, company_id, project_ids, output_dir, "drawings", options
    )


async def async_export_multi_project_specification_sections(
    client: AsyncProcore,
    company_id: int,
    project_ids: Sequence[int],
    output_dir: Path | str,
    **options: Any,
) -> AsyncBatchManifest:
    """Export specification sections for multiple projects."""
    return await _export_one_resource(
        client,
        company_id,
        project_ids,
        output_dir,
        "specification_sections",
        options,
    )


async def async_export_multi_project_core_resources(
    client: AsyncProcore,
    company_id: int,
    project_ids: Sequence[int],
    output_dir: Path | str,
    **options: Any,
) -> AsyncBatchManifest:
    """Export common project resources for multiple projects."""
    resources = ["rfis", "submittals", "documents", "drawings", "specification_sections"]
    plan = build_async_batch_plan(
        company_id=company_id,
        project_ids=project_ids,
        resources=resources,
        output_dir=output_dir,
        dry_run=bool(options.pop("dry_run", False)),
        **options,
    )
    return await async_export_multi_project_resources(client, plan)


async def async_collect_multi_project_rfis(
    client: AsyncProcore,
    company_id: int,
    project_ids: Sequence[int],
    **options: Any,
) -> AsyncBatchManifest:
    """Collect RFIs for multiple projects without writing files."""
    return await _collect_one_resource(client, company_id, project_ids, "rfis", options)


async def async_collect_multi_project_submittals(
    client: AsyncProcore,
    company_id: int,
    project_ids: Sequence[int],
    **options: Any,
) -> AsyncBatchManifest:
    """Collect submittals for multiple projects without writing files."""
    return await _collect_one_resource(client, company_id, project_ids, "submittals", options)


async def async_collect_multi_project_documents(
    client: AsyncProcore,
    company_id: int,
    project_ids: Sequence[int],
    **options: Any,
) -> AsyncBatchManifest:
    """Collect documents for multiple projects without writing files."""
    return await _collect_one_resource(client, company_id, project_ids, "documents", options)


async def async_collect_multi_project_drawings(
    client: AsyncProcore,
    company_id: int,
    project_ids: Sequence[int],
    **options: Any,
) -> AsyncBatchManifest:
    """Collect drawings for multiple projects without writing files."""
    return await _collect_one_resource(client, company_id, project_ids, "drawings", options)


async def async_collect_multi_project_specifications(
    client: AsyncProcore,
    company_id: int,
    project_ids: Sequence[int],
    **options: Any,
) -> AsyncBatchManifest:
    """Collect specification sections for multiple projects without writing files."""
    return await _collect_one_resource(
        client,
        company_id,
        project_ids,
        "specification_sections",
        options,
    )


async def _export_one_resource(
    client: AsyncProcore,
    company_id: int,
    project_ids: Sequence[int],
    output_dir: Path | str,
    resource: str,
    options: dict[str, Any],
) -> AsyncBatchManifest:
    """Build and run a one-resource export plan."""
    plan = build_async_batch_plan(
        company_id=company_id,
        project_ids=project_ids,
        resources=[resource],
        output_dir=output_dir,
        dry_run=bool(options.pop("dry_run", False)),
        **options,
    )
    return await async_export_multi_project_resources(client, plan)


async def _collect_one_resource(
    client: AsyncProcore,
    company_id: int,
    project_ids: Sequence[int],
    resource: str,
    options: dict[str, Any],
) -> AsyncBatchManifest:
    """Build and run a one-resource collection plan."""
    return await async_collect_multi_project_resources(
        client,
        company_id,
        project_ids,
        [resource],
        **options,
    )


async def _fetch_resource(
    client: AsyncProcore,
    company_id: int,
    project_id: int,
    resource: str,
    options: Mapping[str, Any],
) -> Sequence[object]:
    """Fetch one supported project resource."""
    if resource == "rfis":
        return await client.list_rfis(company_id, project_id, **dict(options))
    if resource == "submittals":
        return await client.list_submittals(company_id, project_id, **dict(options))
    if resource == "documents":
        return await client.list_documents(company_id, project_id, **dict(options))
    if resource == "drawings":
        return await client.list_drawings(company_id, project_id, **dict(options))
    if resource == "specification_sections":
        return await client.list_specification_sections(company_id, project_id, **dict(options))
    raise ValidationError(f"Unsupported async batch resource: {resource}")


async def _write_records(
    records: Sequence[object],
    output_path: Path,
    resource: str,
    output_format: AsyncBatchOutputFormat,
) -> None:
    """Write records using Phase 10B export helpers."""
    if output_format == "csv":
        await async_export_records_csv(records, output_path, resource_name=resource)
    else:
        await async_export_records_jsonl(records, output_path, resource_name=resource)


def _build_manifest(
    plan: AsyncBatchPlan,
    *,
    results: Sequence[AsyncBatchResourceResult],
    findings: Sequence[AsyncBatchFinding],
    dry_run: bool,
) -> AsyncBatchManifest:
    """Build a batch manifest from pair-level results."""
    project_results: list[AsyncProjectResult] = []
    for project_id in plan.project_ids:
        project_pairs = [result for result in results if result.project_id == project_id]
        errors = [result.error for result in project_pairs if result.error]
        statuses = {result.status for result in project_pairs}
        if "failed" in statuses:
            status: AsyncBatchStatus = "failed"
        elif statuses == {"skipped"}:
            status = "skipped"
        elif dry_run:
            status = "dry_run"
        else:
            status = "completed"
        project_results.append(
            AsyncProjectResult(
                project_id=project_id,
                status=status,
                resources=[result.resource for result in project_pairs],
                record_count=sum(result.record_count for result in project_pairs),
                errors=[error for error in errors if error],
            )
        )

    warnings = [finding.message for finding in findings if finding.severity == "warning"]
    errors = [finding.message for finding in findings if finding.severity == "error"]
    errors.extend(result.error for result in results if result.error)
    return AsyncBatchManifest(
        plan_name=plan.plan_name,
        generated_at=datetime.now(tz=UTC).isoformat(),
        dry_run=dry_run,
        company_id=plan.company_id,
        project_ids=plan.project_ids,
        resources=plan.resources,
        output_dir=plan.output_dir,
        output_format=plan.output_format,
        max_concurrency=plan.max_concurrency,
        continue_on_error=plan.continue_on_error,
        include_timestamp=plan.include_timestamp,
        per_project_subfolders=plan.per_project_subfolders,
        results=list(results),
        projects=project_results,
        findings=list(findings),
        warnings=warnings,
        errors=[error for error in errors if error],
        safety_notes=_safety_notes(),
    )


def _resource_output_path(plan: AsyncBatchPlan, project_id: int, resource: str) -> Path:
    """Return a safe local output path for one project/resource pair."""
    output_root = Path(plan.output_dir).expanduser().resolve()
    safe_resource = sanitize_filename(resource)
    filename = f"{safe_resource}.{plan.output_format}"
    parts = [output_root]
    if plan.per_project_subfolders:
        parts.append(output_root / f"project-{project_id}")
    if plan.include_timestamp:
        parts.append(parts[-1] / "{timestamp}")
    candidate = (parts[-1] / filename).resolve()
    if not candidate.is_relative_to(output_root):
        raise ValidationError("Async batch output path cannot escape output_dir.")
    return candidate


def _validate_output_dir(plan: AsyncBatchPlan, findings: list[AsyncBatchFinding]) -> None:
    """Validate output directory is local and safe."""
    output_text = str(plan.output_dir)
    if not output_text.strip():
        findings.append(_finding("error", "missing_output_dir", "output_dir is required."))
        return
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", output_text):
        findings.append(
            _finding("error", "remote_output_dir", "output_dir must be a local path, not a URL.")
        )
    if ".." in plan.output_dir.parts:
        findings.append(
            _finding(
                "warning",
                "parent_directory_output",
                "output_dir contains '..'. Prefer an explicit private export folder.",
            )
        )


def _completed_pairs(
    manifest: AsyncBatchManifest | Path | str | None,
) -> set[tuple[int, str]]:
    """Return completed project/resource pairs from a previous manifest."""
    if manifest is None:
        return set()
    active_manifest = manifest
    if not isinstance(active_manifest, AsyncBatchManifest):
        payload = json.loads(Path(active_manifest).read_text(encoding="utf-8"))
        active_manifest = AsyncBatchManifest.model_validate(payload)
    return {
        (result.project_id, result.resource)
        for result in active_manifest.results
        if result.status == "completed"
    }


def _coerce_plan(plan: AsyncBatchPlan | Path | str) -> AsyncBatchPlan:
    """Coerce a plan object or path to an async batch plan."""
    if isinstance(plan, AsyncBatchPlan):
        return plan
    return load_async_batch_plan(plan)


def _finding(severity: AsyncBatchSeverity, code: str, message: str) -> AsyncBatchFinding:
    """Build one batch finding."""
    return AsyncBatchFinding(severity=severity, code=code, message=message)


def _redact_error(error: Exception) -> str:
    """Return non-sensitive error text for manifests."""
    message = str(error)
    message = SECRET_PATTERN.sub(
        lambda match: f"{match.group(1)}{match.group(2)}[redacted]", message
    )
    return URL_WITH_QUERY_PATTERN.sub("[redacted-url]", message)


def _safety_notes() -> list[str]:
    """Return static async batch safety notes."""
    return [
        "Async batch dry-run and validation do not call Procore.",
        "Async batch exports are read-only and write local CSV/JSONL files only.",
        "No create, update, delete, upload, approval, or status-change actions are added.",
        "Manifests do not include raw access tokens, refresh tokens, client secrets, or headers.",
        "Agent tool execution remains disabled and MCP remains discovery-only.",
    ]


__all__ = [
    "SUPPORTED_ASYNC_BATCH_RESOURCES",
    "AsyncBatchFinding",
    "AsyncBatchManifest",
    "AsyncBatchPlan",
    "AsyncBatchResourceResult",
    "AsyncBatchResult",
    "AsyncProjectResult",
    "async_batch_manifest_to_json",
    "async_collect_multi_project_documents",
    "async_collect_multi_project_drawings",
    "async_collect_multi_project_resources",
    "async_collect_multi_project_rfis",
    "async_collect_multi_project_specifications",
    "async_collect_multi_project_submittals",
    "async_collect_project_resources",
    "async_export_multi_project_core_resources",
    "async_export_multi_project_documents",
    "async_export_multi_project_drawings",
    "async_export_multi_project_resources",
    "async_export_multi_project_rfis",
    "async_export_multi_project_specification_sections",
    "async_export_multi_project_submittals",
    "async_run_project_batch",
    "build_async_batch_dry_run_manifest",
    "build_async_batch_plan",
    "explain_async_batch_plan",
    "load_async_batch_plan",
    "sample_async_batch_plan",
    "sample_async_batch_plan_json",
    "validate_async_batch_plan",
    "write_async_batch_manifest",
]
