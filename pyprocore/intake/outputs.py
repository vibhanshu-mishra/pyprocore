"""Local output writer for mocked intake sync results."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from pyprocore.core.exceptions import ValidationError
from pyprocore.intake.attachments import (
    render_attachment_manifest_json,
    render_attachment_manifest_markdown,
)
from pyprocore.intake.models import (
    IntakeOutputManifest,
    IntakeSyncResourceResult,
    IntakeSyncRunResult,
)
from pyprocore.intake.reports import intake_run_result_to_markdown, intake_to_json


def write_intake_sync_outputs(
    result: IntakeSyncRunResult,
    output_dir: str | Path,
    *,
    dry_run: bool = True,
    overwrite: bool = False,
) -> IntakeOutputManifest:
    """Plan or write all intake outputs inside one local directory."""
    root = _safe_root(output_dir)
    relative_paths = result.plan.output_files
    destinations = [_inside(root, path) for path in relative_paths]
    if dry_run:
        return IntakeOutputManifest(
            output_dir=str(root),
            dry_run=True,
            planned_files=relative_paths,
        )
    existing = [path for path in destinations if path.exists()]
    if existing and not overwrite:
        raise ValidationError(
            "Refusing to overwrite existing intake outputs: "
            + ", ".join(str(path) for path in existing)
        )
    root.mkdir(parents=True, exist_ok=True)
    content = _output_content(result)
    written: list[str] = []
    for relative_path in relative_paths:
        destination = _inside(root, relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if relative_path == "output_manifest.json":
            continue
        value = content.get(relative_path, "")
        if isinstance(value, list):
            _write_csv(destination, value)
        else:
            destination.write_text(value, encoding="utf-8")
        written.append(relative_path)
    manifest = IntakeOutputManifest(
        output_dir=str(root),
        dry_run=False,
        planned_files=relative_paths,
        written_files=written + ["output_manifest.json"],
    )
    manifest_path = _inside(root, "output_manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(intake_to_json(manifest) + "\n", encoding="utf-8")
    result.output_manifest = manifest
    return manifest


def _output_content(result: IntakeSyncRunResult) -> dict[str, str | list[dict[str, Any]]]:
    content: dict[str, str | list[dict[str, Any]]] = {
        "intake_summary.json": intake_to_json(result.summary) + "\n",
        "intake_summary.md": intake_run_result_to_markdown(result),
        "attachments_manifest.json": (
            render_attachment_manifest_json(result.attachment_manifest) + "\n"
        ),
        "attachments_manifest.md": render_attachment_manifest_markdown(result.attachment_manifest),
        "state/intake_state.json": intake_to_json(result.state_after) + "\n",
    }
    for resource in ("rfis", "submittals"):
        results = [item for item in result.resource_results if item.resource == resource]
        records = _normalized_records(results)
        content[f"{resource}.jsonl"] = "".join(
            json.dumps(record, sort_keys=True, default=str) + "\n" for record in records
        )
        content[f"{resource}.csv"] = records
        for item in results:
            content[f"raw/{resource}_{item.project_id}.json"] = (
                json.dumps(item.raw_records, indent=2, sort_keys=True, default=str) + "\n"
            )
    return content


def _normalized_records(results: list[IntakeSyncResourceResult]) -> list[dict[str, Any]]:
    return [row.record.model_dump(mode="json") for result in results for row in result.rows]


def _write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    headers = sorted({key for record in records for key in record})
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not headers:
            handle.write("")
            return
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    key: json.dumps(value) if isinstance(value, (list, dict)) else value
                    for key, value in record.items()
                }
            )


def _safe_root(output_dir: str | Path) -> Path:
    candidate = Path(output_dir).expanduser()
    if ".." in candidate.parts:
        raise ValidationError("Path traversal is not allowed for intake output_dir.")
    return candidate.resolve()


def _inside(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    if not candidate.is_relative_to(root):
        raise ValidationError("Intake output path must remain inside output_dir.")
    return candidate
