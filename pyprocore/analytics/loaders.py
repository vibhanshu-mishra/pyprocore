"""Safe local data loaders for analytics recipes."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from pyprocore.core.exceptions import ValidationError

SECRET_FIELD_FRAGMENTS = (
    "token",
    "secret",
    "authorization",
    "password",
    "client_secret",
    "refresh",
    "access_token",
)
REDACTED = "[REDACTED]"


def load_json_records(path: Path | str) -> list[dict[str, Any]]:
    """Load local JSON records from a file.

    Args:
        path: Local JSON file containing a list, a dict, or a dict with a
            top-level ``records`` list.

    Returns:
        Redacted records.

    Raises:
        ValidationError: If the file cannot be read or parsed.
    """
    file_path = Path(path)
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(
            f"Could not load JSON analytics records from {file_path}: {exc}"
        ) from exc
    return load_records(payload)


def load_jsonl_records(path: Path | str) -> list[dict[str, Any]]:
    """Load local JSONL records from a file."""
    file_path = Path(path)
    records: list[dict[str, Any]] = []
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            parsed = json.loads(stripped)
            if not isinstance(parsed, dict):
                raise ValidationError(
                    f"JSONL line {line_number} in {file_path} is not an object record."
                )
            records.append(redact_sensitive_data(parsed))
    except (OSError, json.JSONDecodeError, PydanticValidationError) as exc:
        raise ValidationError(
            f"Could not load JSONL analytics records from {file_path}: {exc}"
        ) from exc
    return records


def load_csv_records(path: Path | str) -> list[dict[str, Any]]:
    """Load local CSV records using the Python standard library."""
    file_path = Path(path)
    try:
        with file_path.open(newline="", encoding="utf-8") as handle:
            return [redact_sensitive_data(dict(row)) for row in csv.DictReader(handle)]
    except OSError as exc:
        raise ValidationError(
            f"Could not load CSV analytics records from {file_path}: {exc}"
        ) from exc


def load_records(payload: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize in-memory local records into a redacted list of dictionaries."""
    if isinstance(payload, list):
        return [redact_sensitive_data(dict(item)) for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        records = payload.get("records")
        if isinstance(records, list):
            return [redact_sensitive_data(dict(item)) for item in records if isinstance(item, dict)]
        return [redact_sensitive_data(payload)]
    raise ValidationError("Analytics records must be a dictionary, list of dictionaries, or file.")


def load_records_from_path(path: Path | str) -> list[dict[str, Any]]:
    """Load local records from JSON, JSONL, or CSV by file extension."""
    file_path = Path(path)
    suffix = file_path.suffix.casefold()
    if suffix == ".json":
        return load_json_records(file_path)
    if suffix == ".jsonl":
        return load_jsonl_records(file_path)
    if suffix == ".csv":
        return load_csv_records(file_path)
    raise ValidationError(
        f"Unsupported analytics file type for {file_path}. Use JSON, JSONL, or CSV."
    )


def redact_sensitive_data(value: Any) -> Any:
    """Redact common secret-like keys from local analytics inputs."""
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if _is_secret_key(str(key)):
                redacted[str(key)] = REDACTED
            else:
                redacted[str(key)] = redact_sensitive_data(item)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive_data(item) for item in value]
    if isinstance(value, str):
        return _redact_secret_text(value)
    return value


def _is_secret_key(key: str) -> bool:
    folded = key.casefold()
    return any(fragment in folded for fragment in SECRET_FIELD_FRAGMENTS)


def _redact_secret_text(text: str) -> str:
    redacted = text
    for marker in ("Bearer ", "Token ", "client_secret=", "refresh_token=", "access_token="):
        if marker in redacted:
            prefix, _, remainder = redacted.partition(marker)
            redacted = prefix + marker + REDACTED
            if " " in remainder:
                redacted += " " + remainder.split(" ", 1)[1]
    return redacted
