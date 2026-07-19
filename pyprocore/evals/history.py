"""Local history snapshot helpers for deterministic PyProcore eval reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from pyprocore.core.exceptions import ValidationError
from pyprocore.evals.baselines import validate_local_eval_json_path
from pyprocore.evals.models import EvalHistorySnapshot, EvalHistorySummary, EvalReport
from pyprocore.evals.runner import sample_eval_report


def build_eval_history_snapshot(
    report: EvalReport,
    *,
    label: str | None = None,
) -> EvalHistorySnapshot:
    """Build one local deterministic eval history snapshot."""
    return EvalHistorySnapshot(
        generated_at=report.generated_at,
        pyprocore_version=report.pyprocore_version,
        status=report.status,
        passed=report.passed,
        total_suites=report.total_suites,
        total_cases=report.total_cases,
        passed_cases=report.passed_cases,
        failed_cases=report.failed_cases,
        warnings=report.warnings,
        score=report.score,
        max_score=report.max_score,
        label=label,
    )


def append_eval_history_snapshot(
    output_path: Path | str,
    snapshot: EvalHistorySnapshot,
) -> Path:
    """Append one eval history snapshot to a local JSON history file."""
    path = validate_local_eval_json_path(output_path, must_exist=False)
    snapshots = load_eval_history_file(path) if path.exists() else []
    snapshots.append(snapshot)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(eval_history_to_json(snapshots, pretty=True) + "\n", encoding="utf-8")
    return path


def load_eval_history_file(path: Path | str) -> list[EvalHistorySnapshot]:
    """Load local deterministic eval history snapshots from JSON."""
    history_path = validate_local_eval_json_path(path, must_exist=True)
    try:
        data = json.loads(history_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON eval history: {history_path}") from exc
    raw_snapshots = data.get("snapshots") if isinstance(data, dict) else data
    if not isinstance(raw_snapshots, list):
        raise ValidationError("Eval history JSON must be a list or an object with snapshots.")
    snapshots: list[EvalHistorySnapshot] = []
    for item in raw_snapshots:
        if not isinstance(item, dict):
            raise ValidationError("Each eval history snapshot must be an object.")
        snapshots.append(_load_history_snapshot_from_dict(item))
    return snapshots


def summarize_eval_history(snapshots: list[EvalHistorySnapshot]) -> EvalHistorySummary:
    """Summarize local deterministic eval history snapshots."""
    if not snapshots:
        return EvalHistorySummary(snapshot_count=0)
    scores = [snapshot.score for snapshot in snapshots]
    trend = "flat"
    if len(scores) > 1 and scores[-1] > scores[0]:
        trend = "up"
    elif len(scores) > 1 and scores[-1] < scores[0]:
        trend = "down"
    return EvalHistorySummary(
        snapshot_count=len(snapshots),
        latest=snapshots[-1],
        best_score=max(scores),
        worst_score=min(scores),
        score_trend=trend,
        snapshots=snapshots,
    )


def build_eval_history_markdown(summary: EvalHistorySummary) -> str:
    """Render eval history summary as Markdown."""
    lines = [
        "# PyProcore Eval History",
        "",
        f"Snapshots: {summary.snapshot_count}",
        f"Score trend: `{summary.score_trend}`",
    ]
    if summary.latest is not None:
        lines.extend(
            [
                f"Latest status: `{summary.latest.status.value}`",
                f"Latest score: {summary.latest.score}/{summary.latest.max_score}",
                "",
                "| Label | Status | Suites | Cases | Score | Warnings |",
                "| --- | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for snapshot in summary.snapshots:
            lines.append(
                f"| `{snapshot.label or ''}` | `{snapshot.status.value}` | "
                f"{snapshot.total_suites} | {snapshot.passed_cases}/{snapshot.total_cases} | "
                f"{snapshot.score}/{snapshot.max_score} | {snapshot.warnings} |"
            )
    lines.extend(
        [
            "",
            "Mode: local deterministic history only; no Procore, model, plugin, MCP, "
            "or tool execution occurred.",
            "",
        ]
    )
    return "\n".join(lines)


def eval_history_to_json(
    snapshots: list[EvalHistorySnapshot],
    *,
    pretty: bool = True,
) -> str:
    """Serialize local eval history snapshots to deterministic JSON text."""
    payload = {
        "schema_version": "1",
        "snapshots": [item.model_dump(mode="json") for item in snapshots],
    }
    return json.dumps(payload, indent=2 if pretty else None, sort_keys=True)


def sample_eval_history_snapshot() -> EvalHistorySnapshot:
    """Return a safe sample eval history snapshot."""
    return build_eval_history_snapshot(sample_eval_report(), label="sample-local-eval")


def sample_eval_history_summary() -> EvalHistorySummary:
    """Return a safe sample eval history summary."""
    return summarize_eval_history([sample_eval_history_snapshot()])


def _load_history_snapshot_from_dict(data: dict[str, Any]) -> EvalHistorySnapshot:
    """Validate one eval history snapshot dictionary."""
    try:
        return EvalHistorySnapshot.model_validate(data)
    except PydanticValidationError as exc:
        raise ValidationError(f"Invalid eval history snapshot: {exc}") from exc
