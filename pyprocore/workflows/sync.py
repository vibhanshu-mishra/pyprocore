"""Folder sync workflows for RFIs and submittals."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pyprocore.models import RFI, Submittal
from pyprocore.services.rfis import download_rfi_attachments, list_rfis
from pyprocore.services.submittals import download_submittal_attachments, list_submittals
from pyprocore.workflows.exports import write_rfis_csv, write_submittals_csv
from pyprocore.workflows.models import (
    ProjectSyncResult,
    SyncedItem,
    SyncResult,
    SyncState,
    SyncStateItem,
)
from pyprocore.workflows.state import build_sync_state_path, load_sync_state, save_sync_state
from pyprocore.workflows.utils import (
    attachment_count,
    get_value,
    item_number,
    item_title,
    json_default,
    model_to_dict,
    safe_filename,
    scalar_text,
)


def sync_rfis_to_folder(
    project_id: int,
    output_dir: Path | str,
    *,
    status: str | None = None,
    download_attachments: bool = True,
    overwrite: bool = False,
    create_tracker: bool = True,
    create_markdown: bool = True,
    dry_run: bool = False,
    incremental: bool = False,
    create_summary: bool = True,
    **filters: Any,
) -> SyncResult:
    """Sync project RFIs into a local folder structure.

    Args:
        project_id: Procore project ID.
        output_dir: Root output folder.
        status: Optional RFI status filter.
        download_attachments: Whether to download RFI attachments.
        overwrite: Whether attachment downloads may overwrite existing files.
        create_tracker: Whether to write a CSV tracker.
        create_markdown: Whether to write one Markdown summary per RFI.
        dry_run: Whether to plan the sync without writing files or downloading
            attachments.
        incremental: Whether to skip unchanged items using local sync state.
        create_summary: Whether to write a Markdown sync summary.
        **filters: Additional list filter parameters passed to the RFI service.

    Returns:
        A typed sync result with manifest and downloaded file paths.
    """
    rfis = list_rfis(project_id, status=status, **filters)
    root = Path(output_dir)
    items_root = root / "rfis"
    if not dry_run:
        items_root.mkdir(parents=True, exist_ok=True)

    synced_items: list[SyncedItem] = []
    skipped_items: list[SyncedItem] = []
    downloaded_files: list[Path] = []
    warnings = _sync_warnings(dry_run=dry_run, download_attachments=download_attachments)
    state_path = build_sync_state_path(root, "rfi") if incremental else None
    previous_state = _load_previous_state(state_path, project_id, "rfi", warnings)
    for rfi in rfis:
        folder = _item_folder(items_root, "RFI", rfi)
        item_json_path = folder / "item.json"
        summary_path = folder / "summary.md" if create_markdown else None
        synced_item = _synced_item(
            rfi,
            folder,
            item_type="rfi",
            item_json_path=item_json_path,
            summary_path=summary_path,
        )
        if _should_skip_item(rfi, previous_state):
            skipped_items.append(synced_item)
            continue
        if not dry_run:
            folder.mkdir(parents=True, exist_ok=True)
            _write_item_json(item_json_path, rfi)
            if summary_path is not None:
                _write_markdown(summary_path, _rfi_markdown(rfi))
        if download_attachments and not dry_run:
            downloaded_files.extend(
                download_rfi_attachments(
                    project_id,
                    rfi.id,
                    folder / "attachments",
                    overwrite=overwrite,
                )
            )
        synced_items.append(synced_item)

    tracker_path = root / "rfi_tracker.csv" if create_tracker else None
    if tracker_path is not None and not dry_run:
        write_rfis_csv(rfis, tracker_path)
    manifest_path = None
    summary_path = None
    if not dry_run:
        manifest_path = _write_manifest(
            root,
            item_type="rfi",
            project_id=project_id,
            tracker_path=tracker_path,
            downloaded_files=downloaded_files,
            skipped_files=[],
            errors=[],
            warnings=warnings,
            items=synced_items,
            skipped_items=skipped_items,
            incremental=incremental,
        )
        if incremental and state_path is not None:
            save_sync_state(_build_state(project_id, "rfi", rfis, items_root), state_path)
        if create_summary:
            summary_path = _write_sync_summary(
                root / "sync_summary.md",
                _sync_result_for_summary(
                    root,
                    "rfi",
                    project_id,
                    len(rfis),
                    tracker_path,
                    manifest_path,
                    downloaded_files,
                    warnings,
                    dry_run,
                    incremental,
                    state_path,
                    synced_items,
                    skipped_items,
                ),
            )
    return SyncResult(
        output_dir=root,
        item_type="rfi",
        project_id=project_id,
        item_count=len(rfis),
        tracker_path=tracker_path,
        manifest_path=manifest_path,
        downloaded_files=downloaded_files,
        skipped_files=[],
        errors=[],
        warnings=warnings,
        dry_run=dry_run,
        summary_path=summary_path,
        synced_count=len(synced_items),
        skipped_count=len(skipped_items),
        warning_count=len(warnings),
        error_count=0,
        state_path=state_path,
        incremental=incremental,
        items=synced_items,
        skipped_items=skipped_items,
    )


def sync_submittals_to_folder(
    project_id: int,
    output_dir: Path | str,
    *,
    status: str | None = None,
    download_attachments: bool = True,
    overwrite: bool = False,
    create_tracker: bool = True,
    create_markdown: bool = True,
    dry_run: bool = False,
    incremental: bool = False,
    create_summary: bool = True,
    **filters: Any,
) -> SyncResult:
    """Sync project submittals into a local folder structure.

    Args:
        project_id: Procore project ID.
        output_dir: Root output folder.
        status: Optional submittal status filter.
        download_attachments: Whether to download submittal attachments.
        overwrite: Whether attachment downloads may overwrite existing files.
        create_tracker: Whether to write a CSV tracker.
        create_markdown: Whether to write one Markdown summary per submittal.
        dry_run: Whether to plan the sync without writing files or downloading
            attachments.
        incremental: Whether to skip unchanged items using local sync state.
        create_summary: Whether to write a Markdown sync summary.
        **filters: Additional list filter parameters passed to the submittal service.

    Returns:
        A typed sync result with manifest and downloaded file paths.
    """
    submittals = list_submittals(project_id, status=status, **filters)
    root = Path(output_dir)
    items_root = root / "submittals"
    if not dry_run:
        items_root.mkdir(parents=True, exist_ok=True)

    synced_items: list[SyncedItem] = []
    skipped_items: list[SyncedItem] = []
    downloaded_files: list[Path] = []
    warnings = _sync_warnings(dry_run=dry_run, download_attachments=download_attachments)
    state_path = build_sync_state_path(root, "submittal") if incremental else None
    previous_state = _load_previous_state(state_path, project_id, "submittal", warnings)
    for submittal in submittals:
        folder = _item_folder(items_root, "SUB", submittal)
        item_json_path = folder / "item.json"
        summary_path = folder / "summary.md" if create_markdown else None
        synced_item = _synced_item(
            submittal,
            folder,
            item_type="submittal",
            item_json_path=item_json_path,
            summary_path=summary_path,
        )
        if _should_skip_item(submittal, previous_state):
            skipped_items.append(synced_item)
            continue
        if not dry_run:
            folder.mkdir(parents=True, exist_ok=True)
            _write_item_json(item_json_path, submittal)
            if summary_path is not None:
                _write_markdown(summary_path, _submittal_markdown(submittal))
        if download_attachments and not dry_run:
            downloaded_files.extend(
                download_submittal_attachments(
                    project_id,
                    submittal.id,
                    folder / "attachments",
                    overwrite=overwrite,
                )
            )
        synced_items.append(synced_item)

    tracker_path = root / "submittal_tracker.csv" if create_tracker else None
    if tracker_path is not None and not dry_run:
        write_submittals_csv(submittals, tracker_path)
    manifest_path = None
    summary_path = None
    if not dry_run:
        manifest_path = _write_manifest(
            root,
            item_type="submittal",
            project_id=project_id,
            tracker_path=tracker_path,
            downloaded_files=downloaded_files,
            skipped_files=[],
            errors=[],
            warnings=warnings,
            items=synced_items,
            skipped_items=skipped_items,
            incremental=incremental,
        )
        if incremental and state_path is not None:
            save_sync_state(
                _build_state(project_id, "submittal", submittals, items_root),
                state_path,
            )
        if create_summary:
            summary_path = _write_sync_summary(
                root / "sync_summary.md",
                _sync_result_for_summary(
                    root,
                    "submittal",
                    project_id,
                    len(submittals),
                    tracker_path,
                    manifest_path,
                    downloaded_files,
                    warnings,
                    dry_run,
                    incremental,
                    state_path,
                    synced_items,
                    skipped_items,
                ),
            )
    return SyncResult(
        output_dir=root,
        item_type="submittal",
        project_id=project_id,
        item_count=len(submittals),
        tracker_path=tracker_path,
        manifest_path=manifest_path,
        downloaded_files=downloaded_files,
        skipped_files=[],
        errors=[],
        warnings=warnings,
        dry_run=dry_run,
        summary_path=summary_path,
        synced_count=len(synced_items),
        skipped_count=len(skipped_items),
        warning_count=len(warnings),
        error_count=0,
        state_path=state_path,
        incremental=incremental,
        items=synced_items,
        skipped_items=skipped_items,
    )


def sync_project_to_folder(
    project_id: int,
    output_dir: Path | str,
    *,
    include_rfis: bool = True,
    include_submittals: bool = True,
    status: str | None = None,
    download_attachments: bool = True,
    overwrite: bool = False,
    create_tracker: bool = True,
    create_markdown: bool = True,
    dry_run: bool = False,
    incremental: bool = False,
    **filters: Any,
) -> ProjectSyncResult:
    """Sync RFIs and/or submittals for a project into one folder."""
    root = Path(output_dir)
    if not include_rfis and not include_submittals:
        raise ValueError("At least one of include_rfis or include_submittals must be True.")

    rfi_result = (
        sync_rfis_to_folder(
            project_id,
            root,
            status=status,
            download_attachments=download_attachments,
            overwrite=overwrite,
            create_tracker=create_tracker,
            create_markdown=create_markdown,
            dry_run=dry_run,
            incremental=incremental,
            create_summary=False,
            **filters,
        )
        if include_rfis
        else None
    )
    submittal_result = (
        sync_submittals_to_folder(
            project_id,
            root,
            status=status,
            download_attachments=download_attachments,
            overwrite=overwrite,
            create_tracker=create_tracker,
            create_markdown=create_markdown,
            dry_run=dry_run,
            incremental=incremental,
            create_summary=False,
            **filters,
        )
        if include_submittals
        else None
    )
    child_results = [result for result in (rfi_result, submittal_result) if result is not None]
    warnings = [warning for result in child_results for warning in result.warnings]
    errors = [error for result in child_results for error in result.errors]
    item_count = sum(result.item_count for result in child_results)
    synced_count = sum(result.synced_count or len(result.items) for result in child_results)
    skipped_count = sum(result.skipped_count for result in child_results)
    manifest_path = None
    summary_path = None
    if not dry_run:
        root.mkdir(parents=True, exist_ok=True)
        manifest_path = _write_project_manifest(
            root,
            project_id=project_id,
            rfi_result=rfi_result,
            submittal_result=submittal_result,
            warnings=warnings,
            errors=errors,
            dry_run=dry_run,
            incremental=incremental,
        )
        summary_path = _write_project_summary(
            root / "project_sync_summary.md",
            project_id=project_id,
            output_dir=root,
            item_count=item_count,
            synced_count=synced_count,
            skipped_count=skipped_count,
            warnings=warnings,
            errors=errors,
            dry_run=dry_run,
            incremental=incremental,
            manifest_path=manifest_path,
        )
    return ProjectSyncResult(
        output_dir=root,
        project_id=project_id,
        item_count=item_count,
        synced_count=synced_count,
        skipped_count=skipped_count,
        warning_count=len(warnings),
        error_count=len(errors),
        dry_run=dry_run,
        incremental=incremental,
        rfi_result=rfi_result,
        submittal_result=submittal_result,
        manifest_path=manifest_path,
        summary_path=summary_path,
        warnings=warnings,
        errors=errors,
    )


def _item_folder(root: Path, prefix: str, item: object) -> Path:
    """Return the local folder path for one synced item."""
    number = item_number(item) or scalar_text(get_value(item, "id"))
    title = item_title(item)
    name = safe_filename(f"{prefix}-{number} - {title}", fallback=f"{prefix}-{number}")
    return root / name


def _synced_item(
    item: object,
    folder: Path,
    *,
    item_type: str,
    item_json_path: Path,
    summary_path: Path | None,
) -> SyncedItem:
    """Build synced item metadata."""
    return SyncedItem(
        id=int(get_value(item, "id")),
        number=item_number(item),
        title=item_title(item),
        folder=folder,
        status=scalar_text(get_value(item, "status")) or None,
        summary_path=summary_path,
        item_json_path=item_json_path,
        attachment_count=attachment_count(item, item_type=item_type),
    )


def _write_item_json(path: Path, item: object) -> None:
    """Write a typed item payload to JSON."""
    path.write_text(
        json.dumps(model_to_dict(item), indent=2, default=json_default, sort_keys=True),
        encoding="utf-8",
    )


def _write_markdown(path: Path, content: str) -> None:
    """Write a Markdown summary file."""
    path.write_text(content, encoding="utf-8")


def _rfi_markdown(rfi: RFI) -> str:
    """Return a Markdown summary for one RFI."""
    lines = [
        f"# RFI {scalar_text(rfi.number)}: {item_title(rfi)}".strip(),
        "",
        f"- ID: {rfi.id}",
        f"- Number: {scalar_text(rfi.number)}",
        f"- Status: {scalar_text(rfi.status)}",
        f"- Due Date: {scalar_text(get_value(rfi, 'due_date'))}",
        f"- Ball In Court: {scalar_text(get_value(rfi, 'ball_in_court'))}",
        f"- Responsible Contractor: {scalar_text(get_value(rfi, 'responsible_contractor'))}",
        f"- Attachment Count: {attachment_count(rfi, item_type='rfi')}",
        "",
    ]
    questions = rfi.questions
    if questions:
        lines.extend(["## Questions", ""])
        for index, question in enumerate(questions, start=1):
            body = scalar_text(get_value(question, "plain_text_body", "body")) or "No question text"
            lines.extend([f"### Question {index}", "", body, ""])
    return "\n".join(lines).rstrip() + "\n"


def _submittal_markdown(submittal: Submittal) -> str:
    """Return a Markdown summary for one submittal."""
    lines = [
        f"# Submittal {scalar_text(submittal.number)}: {item_title(submittal)}".strip(),
        "",
        f"- ID: {submittal.id}",
        f"- Number: {scalar_text(submittal.number)}",
        f"- Status: {scalar_text(submittal.status)}",
        f"- Due Date: {scalar_text(get_value(submittal, 'due_date'))}",
        f"- Ball In Court: {scalar_text(get_value(submittal, 'ball_in_court'))}",
        f"- Responsible Contractor: {scalar_text(submittal.responsible_contractor)}",
        f"- Attachment Count: {attachment_count(submittal, item_type='submittal')}",
        "",
    ]
    description = scalar_text(get_value(submittal, "description", "body", "plain_text_body"))
    if description:
        lines.extend(["## Description", "", description, ""])
    return "\n".join(lines).rstrip() + "\n"


def _write_manifest(
    root: Path,
    *,
    item_type: str,
    project_id: int,
    tracker_path: Path | None,
    downloaded_files: Sequence[Path],
    skipped_files: Sequence[Path],
    errors: Sequence[str],
    warnings: Sequence[str],
    items: Sequence[SyncedItem],
    skipped_items: Sequence[SyncedItem],
    incremental: bool,
) -> Path:
    """Write a sync manifest and return its path."""
    manifest_path = root / "sync_manifest.json"
    payload: Mapping[str, Any] = {
        "item_type": item_type,
        "project_id": project_id,
        "item_count": len(items),
        "synced_count": len(items),
        "skipped_count": len(skipped_items),
        "incremental": incremental,
        "created_at": datetime.now(UTC).isoformat(),
        "tracker_path": str(tracker_path) if tracker_path else None,
        "downloaded_files": [str(path) for path in downloaded_files],
        "skipped_files": [str(path) for path in skipped_files],
        "errors": list(errors),
        "warnings": list(warnings),
        "items": [item.model_dump(mode="json") for item in items],
        "skipped_items": [item.model_dump(mode="json") for item in skipped_items],
    }
    manifest_path.write_text(
        json.dumps(payload, indent=2, default=json_default, sort_keys=True),
        encoding="utf-8",
    )
    return manifest_path


def _load_previous_state(
    state_path: Path | None,
    project_id: int,
    item_type: str,
    warnings: list[str],
) -> SyncState | None:
    """Load prior state, falling back with a warning when invalid."""
    if state_path is None or not state_path.exists():
        return None
    try:
        state = load_sync_state(state_path)
    except Exception as exc:
        warnings.append(f"Could not read sync state {state_path}: {exc}. Full sync will run.")
        return None
    if state.project_id != project_id or state.item_type != item_type:
        warnings.append(f"Sync state {state_path} does not match this sync. Full sync will run.")
        return None
    return state


def _should_skip_item(item: object, state: SyncState | None) -> bool:
    """Return whether an item is unchanged according to prior sync state."""
    if state is None:
        return False
    item_id = str(get_value(item, "id"))
    previous = state.items.get(item_id)
    if previous is None:
        return False
    return previous.updated_at == _updated_at(item)


def _build_state(project_id: int, item_type: str, items: Sequence[object], root: Path) -> SyncState:
    """Build current sync state for all listed items."""
    state_items: dict[str, SyncStateItem] = {}
    prefix = "RFI" if item_type == "rfi" else "SUB"
    for item in items:
        item_id = int(get_value(item, "id"))
        folder = _item_folder(root, prefix, item)
        state_items[str(item_id)] = SyncStateItem(
            id=item_id,
            number=item_number(item),
            updated_at=_updated_at(item),
            folder=str(folder),
        )
    return SyncState(
        project_id=project_id,
        item_type=item_type,
        last_sync_at=datetime.now(UTC).isoformat(),
        items=state_items,
    )


def _updated_at(item: object) -> str | None:
    """Return an item's updated timestamp as text."""
    value = get_value(item, "updated_at")
    return None if value is None else str(value)


def _sync_result_for_summary(
    root: Path,
    item_type: str,
    project_id: int,
    item_count: int,
    tracker_path: Path | None,
    manifest_path: Path | None,
    downloaded_files: Sequence[Path],
    warnings: Sequence[str],
    dry_run: bool,
    incremental: bool,
    state_path: Path | None,
    synced_items: Sequence[SyncedItem],
    skipped_items: Sequence[SyncedItem],
) -> SyncResult:
    """Build a temporary result for summary rendering."""
    return SyncResult(
        output_dir=root,
        item_type=item_type,
        project_id=project_id,
        item_count=item_count,
        tracker_path=tracker_path,
        manifest_path=manifest_path,
        downloaded_files=list(downloaded_files),
        warnings=list(warnings),
        dry_run=dry_run,
        synced_count=len(synced_items),
        skipped_count=len(skipped_items),
        warning_count=len(warnings),
        error_count=0,
        state_path=state_path,
        incremental=incremental,
        items=list(synced_items),
        skipped_items=list(skipped_items),
    )


def _write_sync_summary(path: Path, result: SyncResult) -> Path:
    """Write an individual sync summary report."""
    lines = [
        f"# {result.item_type.title()} Sync Summary",
        "",
        f"- Project ID: {result.project_id}",
        f"- Item Type: {result.item_type}",
        f"- Dry Run: {'yes' if result.dry_run else 'no'}",
        f"- Incremental: {'yes' if result.incremental else 'no'}",
        f"- Item Count: {result.item_count}",
        f"- Synced Count: {result.synced_count or 0}",
        f"- Skipped Count: {result.skipped_count}",
        f"- Warning Count: {result.warning_count}",
        f"- Error Count: {result.error_count}",
        f"- Tracker Path: {result.tracker_path or 'None'}",
        f"- Manifest Path: {result.manifest_path or 'None'}",
        f"- State Path: {result.state_path or 'None'}",
        f"- Output Folder: {result.output_dir}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_project_manifest(
    root: Path,
    *,
    project_id: int,
    rfi_result: SyncResult | None,
    submittal_result: SyncResult | None,
    warnings: Sequence[str],
    errors: Sequence[str],
    dry_run: bool,
    incremental: bool,
) -> Path:
    """Write a project-level sync manifest."""
    path = root / "project_sync_manifest.json"
    payload: Mapping[str, Any] = {
        "project_id": project_id,
        "created_at": datetime.now(UTC).isoformat(),
        "dry_run": dry_run,
        "incremental": incremental,
        "warnings": list(warnings),
        "errors": list(errors),
        "rfi_result": rfi_result.model_dump(mode="json") if rfi_result else None,
        "submittal_result": submittal_result.model_dump(mode="json") if submittal_result else None,
    }
    path.write_text(
        json.dumps(payload, indent=2, default=json_default, sort_keys=True), encoding="utf-8"
    )
    return path


def _write_project_summary(
    path: Path,
    *,
    project_id: int,
    output_dir: Path,
    item_count: int,
    synced_count: int,
    skipped_count: int,
    warnings: Sequence[str],
    errors: Sequence[str],
    dry_run: bool,
    incremental: bool,
    manifest_path: Path | None,
) -> Path:
    """Write a project-level sync summary report."""
    lines = [
        "# Project Sync Summary",
        "",
        f"- Project ID: {project_id}",
        f"- Dry Run: {'yes' if dry_run else 'no'}",
        f"- Incremental: {'yes' if incremental else 'no'}",
        f"- Item Count: {item_count}",
        f"- Synced Count: {synced_count}",
        f"- Skipped Count: {skipped_count}",
        f"- Warning Count: {len(warnings)}",
        f"- Error Count: {len(errors)}",
        f"- Manifest Path: {manifest_path or 'None'}",
        f"- Output Folder: {output_dir}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _sync_warnings(*, dry_run: bool, download_attachments: bool) -> list[str]:
    """Return non-fatal warnings for a sync operation."""
    warnings: list[str] = []
    if dry_run:
        warnings.append("Dry run: no files were written and no attachments were downloaded.")
    if not download_attachments:
        warnings.append("Attachment downloads were disabled.")
    return warnings
