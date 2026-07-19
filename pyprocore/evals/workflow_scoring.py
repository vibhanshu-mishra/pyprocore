"""Workflow-specific deterministic scoring helpers for local eval artifacts."""

from __future__ import annotations

import json
import posixpath
from collections.abc import Iterable
from typing import Any

from pyprocore.evals.models import EvalFinding, EvalScore, EvalSeverity
from pyprocore.evals.scoring import SECRET_LIKE_KEYS

MUTATION_PHRASES = (
    "create procore",
    "update procore",
    "delete procore",
    "upload procore",
    "approve submittal",
    "reject submittal",
    "submit submittal",
    "issue payment",
)
PLACEHOLDER_HINTS = (
    "placeholder",
    "sample",
    "example",
    "local",
    "dry_run",
    "dry-run",
)
UNSAFE_REMOTE_HINTS = (
    "http://",
    "https://",
    "@",
    "real-company",
    "real-project",
)


def expected_field_set_score(
    artifact: Any,
    expected_fields: Iterable[str],
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score whether export rows or package objects include expected fields."""
    fields = list(expected_fields)
    rows = _artifact_rows(artifact)
    if rows is None:
        missing = [field for field in fields if not _has_key(artifact, field)]
    else:
        missing = sorted(
            {field for row in rows if isinstance(row, dict) for field in fields if field not in row}
        )
    return _score(
        "expected_field_set",
        not missing,
        (
            "Expected workflow fields are present."
            if not missing
            else "Expected workflow fields are missing."
        ),
        case_id=case_id,
        details={"missing_fields": missing},
    )


def required_phrase_score(
    artifact: Any,
    required_phrases: Iterable[str],
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score whether artifact text includes required workflow guidance."""
    text = _artifact_text(artifact).casefold()
    missing = [phrase for phrase in required_phrases if phrase.casefold() not in text]
    return _score(
        "required_phrase",
        not missing,
        (
            "Required workflow phrases are present."
            if not missing
            else "Required workflow phrases are missing."
        ),
        case_id=case_id,
        details={"missing_phrases": missing},
    )


def forbidden_phrase_score(
    artifact: Any,
    forbidden_phrases: Iterable[str],
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score whether artifact text avoids forbidden workflow phrases."""
    text = _artifact_text(artifact).casefold()
    present = [phrase for phrase in forbidden_phrases if phrase.casefold() in text]
    return _score(
        "forbidden_phrase",
        not present,
        (
            "Forbidden workflow phrases are absent."
            if not present
            else "Forbidden workflow phrases are present."
        ),
        case_id=case_id,
        details={"present_phrases": [_redact_text(phrase) for phrase in present]},
    )


def path_within_output_dir_score(
    output_dir: str,
    output_paths: Iterable[str],
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score whether declared output paths stay under the declared output directory."""
    base = _normalize_path(output_dir)
    invalid = [
        path
        for path in output_paths
        if _is_absolute(path) or not _normalize_path(path).startswith(f"{base}/")
    ]
    return _score(
        "path_within_output_dir",
        not invalid,
        (
            "Output paths stay under the output directory."
            if not invalid
            else "Output paths escape the output directory."
        ),
        case_id=case_id,
        details={"invalid_paths": invalid},
    )


def manifest_status_score(
    artifact: Any,
    expected_status: str,
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score whether a manifest status matches the expected status."""
    actual = artifact.get("status") if isinstance(artifact, dict) else None
    return _score(
        "manifest_status",
        actual == expected_status,
        "Manifest status matches." if actual == expected_status else "Manifest status mismatch.",
        case_id=case_id,
        details={"expected": expected_status, "actual": actual},
    )


def no_mutation_instruction_score(artifact: Any, *, case_id: str | None = None) -> EvalScore:
    """Score whether workflow fixtures avoid Procore mutation instructions."""
    text = _artifact_text(artifact).casefold()
    present = [phrase for phrase in MUTATION_PHRASES if phrase in text]
    return _score(
        "no_mutation_instruction",
        not present,
        (
            "Artifact contains no Procore mutation instructions."
            if not present
            else "Artifact contains Procore mutation instructions."
        ),
        case_id=case_id,
        details={"mutation_phrases": present},
    )


def no_secret_like_value_score(artifact: Any, *, case_id: str | None = None) -> EvalScore:
    """Score whether workflow fixtures avoid secret-like key names and values."""
    text = _artifact_text(artifact).casefold()
    present = [key for key in SECRET_LIKE_KEYS if key in text]
    return _score(
        "no_secret_like_value",
        not present,
        "No secret-like values are present." if not present else "Secret-like values are present.",
        case_id=case_id,
        details={"secret_like_fragments": [_redact_text(item) for item in present]},
    )


def placeholder_only_score(artifact: Any, *, case_id: str | None = None) -> EvalScore:
    """Score whether sample artifacts look like local placeholder data."""
    text = _artifact_text(artifact).casefold()
    has_placeholder_hint = any(hint in text for hint in PLACEHOLDER_HINTS)
    unsafe_remote_hint = [hint for hint in UNSAFE_REMOTE_HINTS if hint in text]
    passed = has_placeholder_hint and not unsafe_remote_hint
    return _score(
        "placeholder_only",
        passed,
        (
            "Artifact uses placeholder-only local data."
            if passed
            else "Artifact may contain non-placeholder data."
        ),
        case_id=case_id,
        details={
            "has_placeholder_hint": has_placeholder_hint,
            "unsafe_remote_hints": unsafe_remote_hint,
        },
    )


def allowed_capability_score(
    artifact: Any,
    allowed_capabilities: Iterable[str],
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score whether plugin capabilities are in an allowed set."""
    allowed = set(allowed_capabilities)
    capabilities = artifact.get("capabilities", []) if isinstance(artifact, dict) else []
    invalid = [item for item in capabilities if item not in allowed]
    return _score(
        "allowed_capability",
        not invalid,
        (
            "Plugin capabilities are in the allowed set."
            if not invalid
            else "Plugin capabilities are outside the allowed set."
        ),
        case_id=case_id,
        details={"invalid_capabilities": invalid},
    )


def allowed_hook_type_score(
    artifact: Any,
    allowed_hook_types: Iterable[str],
    *,
    case_id: str | None = None,
) -> EvalScore:
    """Score whether hook metadata uses allowed hook types."""
    allowed = set(allowed_hook_types)
    hooks = artifact.get("hooks", []) if isinstance(artifact, dict) else []
    invalid = [
        hook.get("type")
        for hook in hooks
        if isinstance(hook, dict) and hook.get("type") not in allowed
    ]
    return _score(
        "allowed_hook_type",
        not invalid,
        "Hook types are allowed." if not invalid else "Hook types are not allowed.",
        case_id=case_id,
        details={"invalid_hook_types": invalid},
    )


def _artifact_rows(artifact: Any) -> list[Any] | None:
    """Return row-like data from a workflow artifact when present."""
    if isinstance(artifact, list):
        return artifact
    if isinstance(artifact, dict):
        rows = artifact.get("rows")
        if isinstance(rows, list):
            return rows
    return None


def _has_key(artifact: Any, key: str) -> bool:
    """Return whether a mapping contains one direct key."""
    return isinstance(artifact, dict) and key in artifact


def _artifact_text(artifact: Any) -> str:
    """Return deterministic JSON text for workflow artifact scanning."""
    if isinstance(artifact, str):
        return artifact
    return json.dumps(artifact, sort_keys=True, default=str)


def _normalize_path(path: str) -> str:
    """Normalize a local fixture path for text-only safety checks."""
    normalized = posixpath.normpath(path.replace("\\", "/"))
    if normalized.startswith("./"):
        return normalized[2:]
    return normalized


def _is_absolute(path: str) -> bool:
    """Return whether a fixture path is absolute on common platforms."""
    return path.startswith(("/", "\\")) or (len(path) > 2 and path[1] == ":")


def _score(
    check: str,
    passed: bool,
    message: str,
    *,
    case_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> EvalScore:
    """Create one deterministic workflow score."""
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


def _redact_text(value: str) -> str:
    """Redact secret-like text from workflow finding details."""
    lowered = value.casefold()
    if any(key in lowered for key in SECRET_LIKE_KEYS):
        return "[REDACTED]"
    return value
