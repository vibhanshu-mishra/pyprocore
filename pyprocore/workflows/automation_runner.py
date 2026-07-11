"""Safe local automation runner for PyProcore workflow plans."""

from __future__ import annotations

import inspect
import json
import re
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError as PydanticValidationError

from pyprocore.core.exceptions import ProcoreError, ValidationError
from pyprocore.workflows.ai_exports import build_ai_prompt_pack, build_ai_review_export
from pyprocore.workflows.enhanced_rfi import build_enhanced_rfi_package
from pyprocore.workflows.enhanced_submittal import build_enhanced_submittal_package
from pyprocore.workflows.exports import export_rfis_to_csv, export_submittals_to_csv
from pyprocore.workflows.models import (
    WorkflowPlan,
    WorkflowRunManifest,
    WorkflowRunOptions,
    WorkflowRunResult,
    WorkflowStep,
    WorkflowStepResult,
)
from pyprocore.workflows.project_context import build_project_context_package
from pyprocore.workflows.sync import (
    sync_documents_to_folder,
    sync_rfis_to_folder,
    sync_submittals_to_folder,
)
from pyprocore.workflows.utils import json_default, safe_filename

WorkflowFunction = Callable[..., object]

PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)\}")
FULL_PLACEHOLDER_PATTERN = re.compile(r"^\{([^{}]+)\}$")
SENSITIVE_KEY_PARTS = ("token", "secret", "authorization", "password", "client_secret")

WORKFLOW_DISPATCH: dict[str, WorkflowFunction] = {
    "project_context": build_project_context_package,
    "enhanced_rfi_package": build_enhanced_rfi_package,
    "enhanced_submittal_package": build_enhanced_submittal_package,
    "ai_review_export": build_ai_review_export,
    "ai_prompt_pack": build_ai_prompt_pack,
    "sync_rfis": sync_rfis_to_folder,
    "sync_submittals": sync_submittals_to_folder,
    "sync_documents": sync_documents_to_folder,
    "export_rfis": export_rfis_to_csv,
    "export_submittals": export_submittals_to_csv,
}


def list_available_workflows() -> list[str]:
    """Return the workflow names supported by the local automation runner."""
    return sorted(WORKFLOW_DISPATCH)


def load_workflow_plan(path: Path | str) -> WorkflowPlan:
    """Load a workflow plan from a JSON file.

    Args:
        path: Path to a JSON workflow plan. YAML paths receive a friendly
            optional-support error unless YAML support is added in a future
            release.

    Returns:
        A validated workflow plan model.

    Raises:
        ValidationError: If the file cannot be read or validated.
    """
    plan_path = Path(path)
    suffix = plan_path.suffix.casefold()
    if suffix in {".yaml", ".yml"}:
        raise ValidationError(
            "YAML workflow plans are not enabled in this installation. "
            "Use a .json workflow plan for now, or install optional YAML support "
            "when the project adds it."
        )
    if suffix != ".json":
        raise ValidationError("Workflow plan files must use .json, .yaml, or .yml.")
    try:
        payload = json.loads(plan_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"Workflow plan file not found: {plan_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Workflow plan JSON is invalid: {exc.msg}") from exc
    except OSError as exc:
        raise ValidationError(f"Could not read workflow plan file {plan_path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ValidationError("Workflow plan must be a JSON object.")
    return validate_workflow_plan(payload)


def validate_workflow_plan(plan: WorkflowPlan | Mapping[str, object]) -> WorkflowPlan:
    """Validate a workflow plan without executing it.

    Args:
        plan: A ``WorkflowPlan`` model or mapping loaded from JSON.

    Returns:
        A validated ``WorkflowPlan``.

    Raises:
        ValidationError: If the plan structure or references are invalid.
    """
    workflow_plan = _coerce_plan(plan)
    enabled_steps = [step for step in workflow_plan.steps if step.enabled]
    if not enabled_steps:
        raise ValidationError("Workflow plan must contain at least one enabled step.")

    seen: set[str] = set()
    for step in workflow_plan.steps:
        if step.id in seen:
            raise ValidationError(f"Workflow step IDs must be unique: {step.id}")
        seen.add(step.id)
        if step.workflow not in WORKFLOW_DISPATCH:
            raise ValidationError(
                f"Unsupported workflow '{step.workflow}' in step '{step.id}'. "
                f"Available workflows: {', '.join(list_available_workflows())}"
            )
        if not isinstance(step.options, dict):
            raise ValidationError(f"Options for step '{step.id}' must be an object.")

    earlier: set[str] = set()
    for step in workflow_plan.steps:
        for dependency in step.depends_on:
            if dependency not in seen:
                raise ValidationError(f"Step '{step.id}' depends on unknown step '{dependency}'.")
            if dependency not in earlier:
                raise ValidationError(
                    f"Step '{step.id}' depends on '{dependency}', but dependencies "
                    "must reference earlier steps."
                )
        earlier.add(step.id)
    return workflow_plan


def run_workflow_plan(
    path_or_plan: Path | str | WorkflowPlan | Mapping[str, object],
    output_dir: Path | str | None = None,
    dry_run: bool = False,
    continue_on_error: bool = True,
) -> WorkflowRunResult:
    """Run or dry-run a local workflow automation plan.

    Args:
        path_or_plan: Workflow plan path or in-memory plan object.
        output_dir: Optional run manifest output folder.
        dry_run: Whether to validate and resolve steps without executing them.
        continue_on_error: Whether independent later steps should continue after
            a failed step.

    Returns:
        A structured run result with manifest and summary paths.
    """
    plan = (
        load_workflow_plan(path_or_plan)
        if isinstance(path_or_plan, (str, Path))
        else validate_workflow_plan(path_or_plan)
    )
    run_started_at = _utc_now()
    run_started_perf = time.perf_counter()
    run_id = _build_run_id(run_started_at)
    root = _resolve_run_output_dir(plan, output_dir, run_started_at)
    root.mkdir(parents=True, exist_ok=True)
    run_options = WorkflowRunOptions(
        output_dir=root,
        dry_run=dry_run,
        continue_on_error=continue_on_error,
    )
    context: dict[str, object] = {
        **plan.defaults,
        "plan": {"name": plan.name},
        "run": {"id": run_id, "started_at": run_started_at},
        "steps": {},
    }
    step_results: list[WorkflowStepResult] = []
    resolved_steps: list[dict[str, object]] = []
    failed_or_skipped: set[str] = set()
    run_errors: list[str] = []
    run_warnings: list[str] = []
    stop_after_failure = False

    for step in plan.steps:
        if not step.enabled:
            result = _skipped_step_result(step, "Step is disabled.")
            step_results.append(result)
            resolved_steps.append(_resolved_step_payload(step, result.options))
            _record_step_context(context, step.id, result)
            continue

        blocked_dependencies = [
            dependency for dependency in step.depends_on if dependency in failed_or_skipped
        ]
        if stop_after_failure:
            result = _skipped_step_result(step, "Skipped after fail-fast failure.")
        elif blocked_dependencies:
            result = _skipped_step_result(
                step,
                "Skipped because dependency failed or was skipped: "
                + ", ".join(blocked_dependencies),
            )
        else:
            result = _run_step(
                step,
                plan,
                context,
                dry_run=dry_run,
            )

        step_results.append(result)
        resolved_steps.append(_resolved_step_payload(step, result.options))
        _record_step_context(context, step.id, result)

        if result.warnings:
            run_warnings.extend(f"{step.id}: {warning}" for warning in result.warnings)
        if result.status == "failed" or (
            result.status == "skipped" and result.skip_reason != "Dry run"
        ):
            failed_or_skipped.add(step.id)
        if result.status == "failed":
            run_errors.extend(f"{step.id}: {error}" for error in result.errors)
            step_continue = (
                step.continue_on_error if step.continue_on_error is not None else continue_on_error
            )
            if not step_continue:
                stop_after_failure = True

    finished_at = _utc_now()
    status = _run_status(step_results)
    manifest = WorkflowRunManifest(
        run_id=run_id,
        plan_name=plan.name,
        description=plan.description,
        status=status,
        started_at=run_started_at,
        finished_at=finished_at,
        duration_seconds=round(time.perf_counter() - run_started_perf, 6),
        dry_run=dry_run,
        continue_on_error=run_options.continue_on_error,
        output_dir=root,
        steps=step_results,
        warnings=run_warnings,
        errors=run_errors,
    )
    manifest_path = _write_json(root / "run_manifest.json", manifest.model_dump(mode="json"))
    summary_path = _write_markdown(root / "run_summary.md", _run_summary_markdown(manifest))
    resolved_plan_path = _write_json(
        root / "plan_resolved.json",
        _resolved_plan_payload(plan, resolved_steps),
    )
    errors_path = _write_optional_list(root / "errors.json", run_errors)
    warnings_path = _write_optional_list(root / "warnings.json", run_warnings)

    return WorkflowRunResult(
        run_id=run_id,
        plan=plan,
        output_dir=root,
        status=status,
        dry_run=dry_run,
        manifest_path=manifest_path,
        summary_path=summary_path,
        resolved_plan_path=resolved_plan_path,
        errors_path=errors_path,
        warnings_path=warnings_path,
        manifest=manifest,
    )


def _coerce_plan(plan: WorkflowPlan | Mapping[str, object]) -> WorkflowPlan:
    """Return a typed workflow plan or raise a friendly validation error."""
    if isinstance(plan, WorkflowPlan):
        return plan
    try:
        return WorkflowPlan.model_validate(plan)
    except PydanticValidationError as exc:
        raise ValidationError(f"Workflow plan is invalid: {exc}") from exc


def _run_step(
    step: WorkflowStep,
    plan: WorkflowPlan,
    context: Mapping[str, object],
    *,
    dry_run: bool,
) -> WorkflowStepResult:
    """Resolve and execute one workflow step."""
    started_at = _utc_now()
    started_perf = time.perf_counter()
    try:
        resolved_options = _resolve_value(step.options, context)
        if not isinstance(resolved_options, dict):
            raise ValidationError(f"Options for step '{step.id}' must resolve to an object.")
        call_options = _build_call_options(step, plan, resolved_options)
        display_options = _redact_value(call_options)
        if not isinstance(display_options, dict):
            display_options = {}
        if dry_run:
            output_dir = _planned_output_dir(call_options)
            return WorkflowStepResult(
                id=step.id,
                workflow=step.workflow,
                status="skipped",
                options=display_options,
                started_at=started_at,
                finished_at=_utc_now(),
                duration_seconds=round(time.perf_counter() - started_perf, 6),
                output_dir=output_dir,
                warnings=["Dry run: workflow was not executed."],
                skip_reason="Dry run",
            )
        raw_result = WORKFLOW_DISPATCH[step.workflow](**call_options)
        return _completed_step_result(
            step,
            display_options,
            raw_result,
            started_at,
            started_perf,
        )
    except Exception as exc:
        finished_at = _utc_now()
        message = _friendly_exception_message(exc)
        return WorkflowStepResult(
            id=step.id,
            workflow=step.workflow,
            status="failed",
            options=_redact_mapping(step.options),
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=round(time.perf_counter() - started_perf, 6),
            errors=[message],
        )


def _build_call_options(
    step: WorkflowStep,
    plan: WorkflowPlan,
    resolved_options: Mapping[str, object],
) -> dict[str, object]:
    """Build workflow function kwargs from accepted defaults and explicit options."""
    workflow_function = WORKFLOW_DISPATCH[step.workflow]
    signature = inspect.signature(workflow_function)
    parameters = signature.parameters
    accepted_names = {
        name
        for name, parameter in parameters.items()
        if parameter.kind
        in {
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }
    }
    accepts_var_kwargs = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()
    )
    call_options: dict[str, object] = {}
    for key, value in plan.defaults.items():
        if key in accepted_names and key not in resolved_options:
            call_options[key] = value
    unknown = sorted(key for key in resolved_options if key not in accepted_names)
    if unknown and not accepts_var_kwargs:
        raise ValidationError(
            f"Step '{step.id}' has unsupported option(s) for workflow "
            f"'{step.workflow}': {', '.join(unknown)}"
        )
    call_options.update(resolved_options)
    return call_options


def _resolve_value(value: object, context: Mapping[str, object]) -> object:
    """Resolve placeholders recursively without evaluating code."""
    if isinstance(value, str):
        full_match = FULL_PLACEHOLDER_PATTERN.match(value)
        if full_match:
            return _lookup_placeholder(full_match.group(1), context)

        def replace(match: re.Match[str]) -> str:
            replacement = _lookup_placeholder(match.group(1), context)
            return str(replacement)

        return PLACEHOLDER_PATTERN.sub(replace, value)
    if isinstance(value, list):
        return [_resolve_value(item, context) for item in value]
    if isinstance(value, tuple):
        return [_resolve_value(item, context) for item in value]
    if isinstance(value, dict):
        return {key: _resolve_value(item, context) for key, item in value.items()}
    return value


def _lookup_placeholder(name: str, context: Mapping[str, object]) -> object:
    """Resolve one dotted placeholder from the current run context."""
    current: object = context
    for part in name.split("."):
        if isinstance(current, Mapping) and part in current:
            current = current[part]
            continue
        raise ValidationError(f"Could not resolve workflow placeholder '{{{name}}}'.")
    return current


def _completed_step_result(
    step: WorkflowStep,
    options: dict[str, object],
    raw_result: object,
    started_at: str,
    started_perf: float,
) -> WorkflowStepResult:
    """Build a completed step result from a workflow return value."""
    output_dir = _extract_output_dir(raw_result, options)
    files_written = _extract_files_written(raw_result)
    warnings = _extract_string_list(raw_result, "warnings")
    errors = _extract_string_list(raw_result, "errors")
    return WorkflowStepResult(
        id=step.id,
        workflow=step.workflow,
        status="completed",
        options=options,
        started_at=started_at,
        finished_at=_utc_now(),
        duration_seconds=round(time.perf_counter() - started_perf, 6),
        output_dir=output_dir,
        files_written=files_written,
        warnings=warnings,
        errors=errors,
    )


def _skipped_step_result(step: WorkflowStep, reason: str) -> WorkflowStepResult:
    """Build a skipped step result."""
    return WorkflowStepResult(
        id=step.id,
        workflow=step.workflow,
        status="skipped",
        options=_redact_mapping(step.options),
        skip_reason=reason,
        warnings=[reason],
    )


def _record_step_context(
    context: dict[str, object],
    step_id: str,
    result: WorkflowStepResult,
) -> None:
    """Expose safe step result values to later placeholders."""
    steps = context.setdefault("steps", {})
    if isinstance(steps, dict):
        steps[step_id] = {
            "status": result.status,
            "output_dir": result.output_dir,
            "files_written": result.files_written,
        }


def _planned_output_dir(options: Mapping[str, object]) -> Path | None:
    """Return the most likely output directory from resolved options."""
    output_value = options.get("output_dir")
    if output_value is None:
        output_value = options.get("output_path")
    if output_value is None:
        return None
    path = Path(str(output_value))
    if path.suffix:
        return path.parent
    return path


def _extract_output_dir(raw_result: object, options: Mapping[str, object]) -> Path | None:
    """Extract an output directory from a workflow result."""
    output_dir = getattr(raw_result, "output_dir", None)
    if output_dir is not None:
        return Path(output_dir)
    if isinstance(raw_result, Path):
        return raw_result.parent
    return _planned_output_dir(options)


def _extract_files_written(raw_result: object) -> list[Path]:
    """Extract written files from a workflow result when available."""
    if isinstance(raw_result, Path):
        return [raw_result]
    files: list[Path] = []
    for attribute in (
        "manifest_path",
        "summary_path",
        "tracker_path",
        "ai_review_path",
        "ai_review_json_path",
        "prompt_path",
        "system_context_path",
        "source_index_json_path",
        "source_index_md_path",
        "errors_path",
        "warnings_path",
    ):
        value = getattr(raw_result, attribute, None)
        if value is not None:
            files.append(Path(value))
    for attribute in ("downloaded_files", "checklist_paths", "chunk_paths"):
        value = getattr(raw_result, attribute, None)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            files.extend(Path(item) for item in value)
    manifest = getattr(raw_result, "manifest", None)
    for attribute in ("file_paths_written", "files_written"):
        value = getattr(manifest, attribute, None)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            files.extend(Path(item) for item in value)
    return list(dict.fromkeys(files))


def _extract_string_list(raw_result: object, attribute: str) -> list[str]:
    """Extract warning or error strings from a workflow result."""
    value = getattr(raw_result, attribute, None)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [str(item) for item in value]
    manifest = getattr(raw_result, "manifest", None)
    manifest_value = getattr(manifest, attribute, None)
    if isinstance(manifest_value, Sequence) and not isinstance(
        manifest_value,
        (str, bytes, bytearray),
    ):
        return [str(item) for item in manifest_value]
    return []


def _run_status(step_results: Sequence[WorkflowStepResult]) -> str:
    """Return an overall run status from step results."""
    if any(step.status == "failed" for step in step_results):
        return "failed"
    if all(step.status == "skipped" for step in step_results):
        return "skipped"
    return "completed"


def _resolve_run_output_dir(
    plan: WorkflowPlan,
    output_dir: Path | str | None,
    started_at: str,
) -> Path:
    """Resolve the run manifest output folder."""
    if output_dir is not None:
        return Path(output_dir)
    output_root = plan.defaults.get("output_root")
    if output_root is not None:
        return Path(str(output_root))
    timestamp = safe_filename(started_at.replace(":", "-"), fallback="run")
    return Path("pyprocore-runs") / f"{safe_filename(plan.name)}-{timestamp}"


def _build_run_id(started_at: str) -> str:
    """Build a compact run ID."""
    timestamp = started_at.replace(":", "").replace("-", "").replace("+", "z")
    return f"run-{timestamp}-{uuid4().hex[:8]}"


def _resolved_plan_payload(
    plan: WorkflowPlan,
    resolved_steps: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Build a redacted resolved plan payload for disk."""
    return {
        "name": plan.name,
        "description": plan.description,
        "defaults": _redact_value(plan.defaults),
        "continue_on_error": plan.continue_on_error,
        "steps": list(resolved_steps),
    }


def _resolved_step_payload(step: WorkflowStep, options: Mapping[str, object]) -> dict[str, object]:
    """Build one redacted resolved step payload."""
    return {
        "id": step.id,
        "workflow": step.workflow,
        "depends_on": step.depends_on,
        "enabled": step.enabled,
        "continue_on_error": step.continue_on_error,
        "options": _redact_value(dict(options)),
    }


def _run_summary_markdown(manifest: WorkflowRunManifest) -> str:
    """Render a beginner-friendly Markdown run summary."""
    lines = [
        f"# Workflow Run: {manifest.plan_name}",
        "",
        f"- Run ID: `{manifest.run_id}`",
        f"- Status: `{manifest.status}`",
        f"- Dry Run: `{manifest.dry_run}`",
        f"- Started: `{manifest.started_at}`",
        f"- Finished: `{manifest.finished_at}`",
        f"- Output: `{manifest.output_dir}`",
        "",
        "## Steps",
        "",
        "| Step | Workflow | Status | Output | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for step in manifest.steps:
        notes = step.skip_reason or "; ".join(step.errors or step.warnings)
        lines.append(
            "| {id} | {workflow} | {status} | {output} | {notes} |".format(
                id=step.id,
                workflow=step.workflow,
                status=step.status,
                output=step.output_dir or "",
                notes=notes,
            )
        )
    if manifest.errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in manifest.errors)
    if manifest.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in manifest.warnings)
    return "\n".join(lines).rstrip() + "\n"


def _redact_mapping(values: Mapping[str, object]) -> dict[str, object]:
    """Return a redacted dictionary."""
    redacted = _redact_value(dict(values))
    return redacted if isinstance(redacted, dict) else {}


def _redact_value(value: object) -> object:
    """Redact secrets from values written to manifests."""
    if isinstance(value, Mapping):
        output: dict[str, object] = {}
        for key, item in value.items():
            key_text = str(key)
            if any(part in key_text.casefold() for part in SENSITIVE_KEY_PARTS):
                output[key_text] = "***REDACTED***"
            else:
                output[key_text] = _redact_value(item)
        return output
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, tuple):
        return [_redact_value(item) for item in value]
    return value


def _friendly_exception_message(exc: Exception) -> str:
    """Return a clear exception message without stack traces or secrets."""
    if isinstance(exc, ProcoreError):
        return str(exc)
    return f"{type(exc).__name__}: {exc}"


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


def _utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(UTC).isoformat()
