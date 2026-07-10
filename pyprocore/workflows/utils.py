"""Shared helpers for workflow export and sync operations."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel

UNSAFE_PATH_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
WHITESPACE = re.compile(r"\s+")


def safe_filename(value: object, *, fallback: str = "item", max_length: int = 120) -> str:
    """Return a filesystem-safe name for workflow folders and files.

    Args:
        value: Value to convert into a safe filename segment.
        fallback: Name used when the value is blank after sanitization.
        max_length: Maximum returned length.

    Returns:
        A sanitized filename or folder name.
    """
    candidate = str(value or "").strip()
    candidate = UNSAFE_PATH_CHARS.sub("_", candidate)
    candidate = WHITESPACE.sub(" ", candidate)
    candidate = candidate.strip(" .")
    if not candidate:
        candidate = fallback
    return candidate[:max_length].rstrip(" .") or fallback


def model_to_dict(item: object) -> dict[str, Any]:
    """Convert a typed SDK model or mapping into a JSON-compatible dictionary."""
    if isinstance(item, BaseModel):
        return item.model_dump(mode="json")
    if isinstance(item, Mapping):
        return dict(item)
    return {"value": item}


def get_value(item: object, *names: str) -> Any:
    """Return the first non-empty attribute or mapping value from an item."""
    for name in names:
        if isinstance(item, Mapping) and name in item:
            value = item[name]
        else:
            value = getattr(item, name, None)
        if value is not None:
            return value
    return None


def scalar_text(value: object) -> str:
    """Return a friendly scalar representation for CSV and Markdown output."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, Mapping):
        for key in ("name", "title", "status", "login", "email_address", "id"):
            nested = value.get(key)
            if nested is not None:
                return scalar_text(nested)
        return json.dumps(value, default=str, sort_keys=True)
    for attr in ("name", "title", "status", "login", "email_address", "id"):
        nested = getattr(value, attr, None)
        if nested is not None:
            return scalar_text(nested)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return "; ".join(scalar_text(item) for item in value)
    return str(value)


def item_number(item: object) -> str | None:
    """Return an item number as text when available."""
    value = get_value(item, "number")
    return None if value is None else str(value)


def item_title(item: object, *, fallback: str = "") -> str:
    """Return the best available title for a workflow item."""
    return (
        scalar_text(get_value(item, "subject", "title", "name", "filename", "file_name"))
        or fallback
    )


def attachment_count(item: object, *, item_type: str) -> int:
    """Return the number of visible attachments on a typed item."""
    if item_type == "rfi":
        questions = get_value(item, "questions") or []
        if not isinstance(questions, Sequence) or isinstance(questions, (str, bytes)):
            return 0
        total = 0
        for question in questions:
            attachments = get_value(question, "attachments") or []
            if isinstance(attachments, Sequence) and not isinstance(attachments, (str, bytes)):
                total += len(attachments)
        return total

    attachments = get_value(item, "attachments") or []
    if isinstance(attachments, Sequence) and not isinstance(attachments, (str, bytes)):
        return len(attachments)
    return 0


def json_default(value: object) -> str:
    """Serialize common non-JSON workflow values."""
    if isinstance(value, Path):
        return str(value)
    return str(value)
