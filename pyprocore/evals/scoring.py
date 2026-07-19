"""Deterministic scoring helpers for local PyProcore eval artifacts."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from pyprocore.evals.models import EvalFinding, EvalScore, EvalSeverity

SECRET_LIKE_KEYS = (
    "access_token",
    "refresh_token",
    "client_secret",
    "authorization",
    "bearer",
    "password",
)
UNSAFE_TEXT_FRAGMENTS = (
    "access_token",
    "refresh_token",
    "client_secret",
    "authorization:",
    "bearer ",
    " ".join(("pip", "install")),
    "curl ",
    "wget ",
)
UNSAFE_ACTION_WORDS = tuple(
    f"{verb}_procore"
    for verb in (
        "create",
        "update",
        "delete",
        "upload",
        "approve",
        "reject",
        "submit",
        "payment",
    )
)


def exact_match_score(actual: Any, expected: Any, *, case_id: str | None = None) -> EvalScore:
    """Score exact equality for deterministic artifacts.

    Args:
        actual: Actual value.
        expected: Expected value.
        case_id: Optional case identifier for findings.

    Returns:
        Deterministic score.
    """
    passed = actual == expected
    return _score(
        "exact_match",
        passed,
        (
            "Artifact matches the expected value."
            if passed
            else "Artifact did not match the expected value."
        ),
        case_id=case_id,
    )


def required_keys_score(
    artifact: Any,
    required_keys: Iterable[str],
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score whether required dotted keys exist in an artifact."""
    missing = [key for key in required_keys if not _has_dotted_key(artifact, key)]
    return _score(
        "required_keys",
        not missing,
        "All required keys are present." if not missing else "Required keys are missing.",
        case_id=case_id,
        details={"missing_keys": missing},
    )


def forbidden_keys_score(
    artifact: Any,
    forbidden_keys: Iterable[str],
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score whether forbidden dotted keys are absent from an artifact."""
    present = [key for key in forbidden_keys if _has_dotted_key(artifact, key)]
    return _score(
        "forbidden_keys",
        not present,
        "Forbidden keys are absent." if not present else "Forbidden keys are present.",
        case_id=case_id,
        details={"present_keys": present},
    )


def schema_shape_score(
    artifact: Any,
    required_keys: Iterable[str],
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score basic JSON-like schema shape through required dotted keys."""
    return required_keys_score(artifact, required_keys, case_id=case_id)


def contains_text_score(
    artifact: Any,
    required_text: Iterable[str],
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score whether artifact text contains all required snippets."""
    text = _artifact_text(artifact).casefold()
    missing = [item for item in required_text if item.casefold() not in text]
    return _score(
        "contains_text",
        not missing,
        (
            "Required text snippets are present."
            if not missing
            else "Required text snippets are missing."
        ),
        case_id=case_id,
        details={"missing_text": missing},
    )


def does_not_contain_text_score(
    artifact: Any,
    forbidden_text: Iterable[str],
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score whether artifact text avoids all forbidden snippets."""
    text = _artifact_text(artifact).casefold()
    present = [item for item in forbidden_text if item.casefold() in text]
    return _score(
        "does_not_contain_text",
        not present,
        (
            "Forbidden text snippets are absent."
            if not present
            else "Forbidden text snippets are present."
        ),
        case_id=case_id,
        details={"present_text": present},
    )


def safety_boundary_score(artifact: Any, *, case_id: str | None = None) -> EvalScore:
    """Score whether local eval artifacts avoid unsafe text and write-action hints."""
    text = _artifact_text(artifact).casefold()
    present = [
        fragment for fragment in (*UNSAFE_TEXT_FRAGMENTS, *UNSAFE_ACTION_WORDS) if fragment in text
    ]
    return _score(
        "safety_boundary",
        not present,
        (
            "Artifact stays inside local deterministic safety boundaries."
            if not present
            else "Artifact contains unsafe text."
        ),
        case_id=case_id,
        details={"unsafe_fragments": [_redact_text(item) for item in present]},
    )


def json_serializable_score(artifact: Any, *, case_id: str | None = None) -> EvalScore:
    """Score whether an artifact can be serialized to JSON."""
    try:
        json.dumps(artifact, sort_keys=True)
    except TypeError as exc:
        return _score(
            "json_serializable",
            False,
            "Artifact is not JSON serializable.",
            case_id=case_id,
            details={"error": str(exc)},
        )
    return _score(
        "json_serializable",
        True,
        "Artifact is JSON serializable.",
        case_id=case_id,
    )


def redaction_score(artifact: Any, *, case_id: str | None = None) -> EvalScore:
    """Score whether artifact text avoids raw secret-like values."""
    text = _artifact_text(artifact).casefold()
    present = [key for key in SECRET_LIKE_KEYS if key in text]
    return _score(
        "redaction",
        not present,
        "No secret-like text is present." if not present else "Secret-like text is present.",
        case_id=case_id,
        details={"secret_like_fragments": [_redact_text(item) for item in present]},
    )


def row_count_score(
    rows: Any,
    expected_count: int,
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score the exact row count for list-like export artifacts."""
    actual_count = len(rows) if isinstance(rows, list) else -1
    return _score(
        "row_count",
        actual_count == expected_count,
        "Row count matches." if actual_count == expected_count else "Row count mismatch.",
        case_id=case_id,
        details={"expected": expected_count, "actual": actual_count},
    )


def manifest_integrity_score(
    artifact: Any,
    required_keys: Iterable[str],
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score basic manifest integrity for local metadata artifacts."""
    if not isinstance(artifact, dict):
        return _score(
            "manifest_integrity",
            False,
            "Manifest artifact must be a JSON object.",
            case_id=case_id,
        )
    missing = [key for key in required_keys if not _has_dotted_key(artifact, key)]
    name_present = bool(artifact.get("name") or artifact.get("plugin_name"))
    passed = not missing and name_present
    return _score(
        "manifest_integrity",
        passed,
        "Manifest integrity checks passed." if passed else "Manifest integrity checks failed.",
        case_id=case_id,
        details={"missing_keys": missing, "name_present": name_present},
    )


def required_values_score(
    artifact: Any,
    required_values: dict[str, Any],
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score whether dotted keys equal required values."""
    mismatches = {
        key: {"expected": expected, "actual": _get_dotted_key(artifact, key)}
        for key, expected in required_values.items()
        if _get_dotted_key(artifact, key) != expected
    }
    return _score(
        "required_values",
        not mismatches,
        "Required values match." if not mismatches else "Required values do not match.",
        case_id=case_id,
        details={"mismatches": mismatches},
    )


def _score(
    check: str,
    passed: bool,
    message: str,
    *,
    case_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> EvalScore:
    """Create one deterministic score object."""
    return EvalScore(
        check=check,
        passed=passed,
        points=1 if passed else 0,
        max_points=1,
        findings=[
            EvalFinding(
                severity=EvalSeverity.PASS if passed else EvalSeverity.FAILURE,
                message=message,
                case_id=case_id,
                check=check,
                details=details or {},
            )
        ],
    )


def _artifact_text(artifact: Any) -> str:
    """Return deterministic artifact text for text-scanning checks."""
    if isinstance(artifact, str):
        return artifact
    return json.dumps(artifact, sort_keys=True, default=str)


def _has_dotted_key(artifact: Any, dotted_key: str) -> bool:
    """Return whether a dotted key exists in a nested mapping."""
    return _get_dotted_key(artifact, dotted_key) is not None


def _get_dotted_key(artifact: Any, dotted_key: str) -> Any | None:
    """Return a nested value by dotted key, or None when absent."""
    current = artifact
    for part in dotted_key.split("."):
        if isinstance(current, list) and part.isdigit():
            index = int(part)
            if index >= len(current):
                return None
            current = current[index]
            continue
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _redact_text(value: str) -> str:
    """Redact secret-like fragments from finding details."""
    lowered = value.casefold()
    if any(key in lowered for key in SECRET_LIKE_KEYS):
        return "[REDACTED]"
    return value
