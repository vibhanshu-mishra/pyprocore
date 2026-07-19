"""Built-in deterministic local plugin hooks for Phase 11B."""

from __future__ import annotations

import json
from typing import Any

from pyprocore.plugins.hook_registry import PluginHookRegistry
from pyprocore.plugins.hooks import PluginHookContext, PluginHookMetadata, PluginHookType


def builtin_hook_registry() -> PluginHookRegistry:
    """Return a registry populated with safe built-in local hooks."""
    registry = PluginHookRegistry()
    for metadata, hook in builtin_hook_registrations():
        registry.register_hook(metadata, hook, source="built-in")
    return registry


def builtin_hook_metadata() -> list[PluginHookMetadata]:
    """Return metadata for built-in safe local hooks."""
    return [metadata for metadata, _ in builtin_hook_registrations()]


def builtin_hook_registrations() -> list[tuple[PluginHookMetadata, Any]]:
    """Return built-in hook metadata and callables."""
    return [
        (
            PluginHookMetadata(
                hook_name="validate_required_fields",
                plugin_name="built_in_quality_hooks",
                hook_type=PluginHookType.VALIDATOR,
                description="Validate that each record has required fields.",
                input_kind="records",
                output_kind="validation_report",
                notes=["Uses context.options['required_fields']."],
            ),
            validate_required_fields,
        ),
        (
            PluginHookMetadata(
                hook_name="validate_no_empty_ids",
                plugin_name="built_in_quality_hooks",
                hook_type=PluginHookType.VALIDATOR,
                description="Validate that records do not contain empty id values.",
                input_kind="records",
                output_kind="validation_report",
            ),
            validate_no_empty_ids,
        ),
        (
            PluginHookMetadata(
                hook_name="format_records_as_summary",
                plugin_name="built_in_format_hooks",
                hook_type=PluginHookType.FORMATTER,
                description="Format records as a compact human-readable summary.",
                input_kind="records",
                output_kind="text",
            ),
            format_records_as_summary,
        ),
        (
            PluginHookMetadata(
                hook_name="transform_records_select_fields",
                plugin_name="built_in_transform_hooks",
                hook_type=PluginHookType.RECORD_TRANSFORMER,
                description="Return records with only selected fields.",
                input_kind="records",
                output_kind="records",
                notes=["Uses context.options['fields']."],
            ),
            transform_records_select_fields,
        ),
        (
            PluginHookMetadata(
                hook_name="export_records_to_jsonl_payload",
                plugin_name="built_in_export_hooks",
                hook_type=PluginHookType.EXPORTER,
                description="Render records as a JSONL string payload without writing files.",
                input_kind="records",
                output_kind="jsonl_text",
            ),
            export_records_to_jsonl_payload,
        ),
        (
            PluginHookMetadata(
                hook_name="build_basic_quality_report",
                plugin_name="built_in_report_hooks",
                hook_type=PluginHookType.REPORT,
                description="Build a deterministic local quality summary for records.",
                input_kind="records",
                output_kind="report",
            ),
            build_basic_quality_report,
        ),
    ]


def validate_required_fields(context: PluginHookContext, payload: Any) -> dict[str, Any]:
    """Validate that every record has each required field."""
    records = _records(payload)
    required_fields = [str(item) for item in context.options.get("required_fields", [])]
    missing: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        for field in required_fields:
            if record.get(field) in (None, ""):
                missing.append({"record": index, "field": field})
    return {
        "valid": not missing,
        "record_count": len(records),
        "required_fields": required_fields,
        "missing": missing,
    }


def validate_no_empty_ids(_context: PluginHookContext, payload: Any) -> dict[str, Any]:
    """Validate that record id values are present."""
    records = _records(payload)
    empty_records = [
        index for index, record in enumerate(records, start=1) if record.get("id") in (None, "")
    ]
    return {
        "valid": not empty_records,
        "record_count": len(records),
        "empty_id_records": empty_records,
    }


def format_records_as_summary(_context: PluginHookContext, payload: Any) -> str:
    """Format records as a compact deterministic summary."""
    records = _records(payload)
    lines = [f"Records: {len(records)}"]
    for index, record in enumerate(records[:5], start=1):
        label = (
            record.get("name") or record.get("title") or record.get("number") or record.get("id")
        )
        lines.append(f"- {index}: {label or 'unnamed'}")
    if len(records) > 5:
        lines.append(f"- ... {len(records) - 5} more")
    return "\n".join(lines)


def transform_records_select_fields(
    context: PluginHookContext, payload: Any
) -> list[dict[str, Any]]:
    """Return records containing only requested fields."""
    records = _records(payload)
    fields = [str(item) for item in context.options.get("fields", [])]
    if not fields:
        return records
    return [{field: record.get(field) for field in fields if field in record} for record in records]


def export_records_to_jsonl_payload(_context: PluginHookContext, payload: Any) -> str:
    """Return records as JSONL text without writing files."""
    return "\n".join(
        json.dumps(record, sort_keys=True, default=str) for record in _records(payload)
    )


def build_basic_quality_report(_context: PluginHookContext, payload: Any) -> dict[str, Any]:
    """Build a local deterministic quality report for records."""
    records = _records(payload)
    keys = sorted({key for record in records for key in record})
    empty_id_count = sum(1 for record in records if record.get("id") in (None, ""))
    return {
        "record_count": len(records),
        "field_count": len(keys),
        "fields": keys,
        "empty_id_count": empty_id_count,
    }


def _records(payload: Any) -> list[dict[str, Any]]:
    """Normalize payload into a list of dictionaries."""
    if isinstance(payload, dict):
        if isinstance(payload.get("records"), list):
            return [dict(item) for item in payload["records"] if isinstance(item, dict)]
        return [dict(payload)]
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    return []
