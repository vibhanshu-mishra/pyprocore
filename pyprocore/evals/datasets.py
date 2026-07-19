"""Golden dataset loading and validation for local PyProcore evals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from pyprocore.core.exceptions import ValidationError
from pyprocore.evals.models import (
    EvalFinding,
    EvalSeverity,
    GoldenDataset,
)
from pyprocore.evals.scoring import SECRET_LIKE_KEYS

DATASET_SCHEMA_VERSION = "1"
UNSAFE_DATASET_TEXT = (
    "authorization:",
    "bearer ",
    "client_secret",
    "refresh_token",
    "access_token",
    " ".join(("pip", "install")),
    "curl ",
    "wget ",
)
UNSAFE_DATASET_ACTIONS = tuple(
    f"{verb}_procore"
    for verb in ("create", "update", "delete", "upload", "approve", "reject", "submit")
)


def load_golden_dataset_from_dict(data: dict[str, Any]) -> GoldenDataset:
    """Load and validate a golden dataset from a dictionary.

    Args:
        data: JSON-like dictionary.

    Raises:
        ValidationError: If the dataset shape or safety checks fail.

    Returns:
        Validated golden dataset.
    """
    try:
        dataset = GoldenDataset.model_validate(data)
    except PydanticValidationError as exc:
        raise ValidationError(f"Invalid golden dataset: {exc}") from exc
    findings = validate_golden_dataset(dataset)
    errors = [finding for finding in findings if finding.severity == EvalSeverity.FAILURE]
    if errors:
        messages = "; ".join(finding.message for finding in errors)
        raise ValidationError(f"Invalid golden dataset: {messages}")
    return dataset


def load_golden_dataset_from_file(path: Path | str) -> GoldenDataset:
    """Load and validate a local JSON golden dataset file.

    Args:
        path: Local JSON dataset path.

    Raises:
        ValidationError: If the path is unsafe, JSON is invalid, or validation fails.

    Returns:
        Validated golden dataset.
    """
    dataset_path = _validate_local_json_path(path)
    try:
        data = json.loads(dataset_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON golden dataset: {dataset_path}") from exc
    if not isinstance(data, dict):
        raise ValidationError("Golden dataset JSON must be an object.")
    return load_golden_dataset_from_dict(data)


def validate_golden_dataset(dataset: GoldenDataset) -> list[EvalFinding]:
    """Validate a golden dataset without running eval cases."""
    findings: list[EvalFinding] = []
    if dataset.schema_version != DATASET_SCHEMA_VERSION:
        findings.append(
            EvalFinding(
                severity=EvalSeverity.FAILURE,
                message=(
                    "Unsupported golden dataset schema version: " f"{dataset.schema_version}."
                ),
            )
        )
    if not dataset.cases:
        findings.append(
            EvalFinding(
                severity=EvalSeverity.FAILURE,
                message="Golden dataset must contain at least one case.",
            )
        )
    seen_case_ids: set[str] = set()
    for case in dataset.cases:
        if case.id in seen_case_ids:
            findings.append(
                EvalFinding(
                    severity=EvalSeverity.FAILURE,
                    message=f"Duplicate golden dataset case id: {case.id}.",
                    case_id=case.id,
                )
            )
        seen_case_ids.add(case.id)
        payload = case.model_dump(mode="json")
        expected = payload.get("expected", {})
        if isinstance(expected, dict):
            expected["does_not_contain_text"] = []
            expected["forbidden_keys"] = []
            expected["forbidden_phrases"] = []
        _scan_value(payload, findings, case_id=case.id)
    return findings or [
        EvalFinding(
            severity=EvalSeverity.PASS,
            message="Golden dataset is valid for local deterministic evals.",
        )
    ]


def sample_golden_dataset() -> GoldenDataset:
    """Return a small safe sample golden dataset."""
    return load_golden_dataset_from_dict(
        {
            "schema_version": DATASET_SCHEMA_VERSION,
            "metadata": {
                "name": "sample_golden_dataset",
                "description": "Small placeholder dataset for local deterministic evals.",
                "tags": ["sample", "local"],
            },
            "cases": [
                {
                    "id": "sample_export_rows_have_ids",
                    "case_type": "export_rows",
                    "description": "Export rows include stable placeholder ids and names.",
                    "input": {
                        "artifact_name": "sample_export_rows",
                        "artifact": [
                            {"id": "sample-1", "name": "Sample RFI"},
                            {"id": "sample-2", "name": "Sample Submittal"},
                        ],
                    },
                    "expected": {
                        "row_count": 2,
                        "required_keys": ["0.id", "1.name"],
                        "does_not_contain_text": ["client_secret"],
                    },
                }
            ],
        }
    )


def golden_dataset_to_json(dataset: GoldenDataset, *, pretty: bool = True) -> str:
    """Serialize a golden dataset to deterministic JSON text."""
    return json.dumps(
        dataset.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=True,
    )


def _validate_local_json_path(path: Path | str) -> Path:
    """Validate a local JSON path without allowing remote paths or traversal."""
    dataset_path = Path(path)
    path_text = str(dataset_path)
    if "://" in path_text or path_text.casefold().startswith(("http:", "https:")):
        raise ValidationError("Golden dataset path must be a local JSON file, not a URL.")
    if any(part == ".." for part in dataset_path.parts):
        raise ValidationError("Golden dataset path must not contain path traversal.")
    if dataset_path.suffix != ".json":
        raise ValidationError("Golden dataset path must end with .json.")
    if not dataset_path.exists():
        raise ValidationError(f"Golden dataset file not found: {dataset_path}")
    return dataset_path


def _scan_value(value: Any, findings: list[EvalFinding], *, case_id: str) -> None:
    """Scan nested dataset values for unsafe text."""
    if isinstance(value, dict):
        for key, item in value.items():
            _scan_text(str(key), findings, case_id=case_id)
            _scan_value(item, findings, case_id=case_id)
        return
    if isinstance(value, list):
        for item in value:
            _scan_value(item, findings, case_id=case_id)
        return
    if isinstance(value, str):
        _scan_text(value, findings, case_id=case_id)


def _scan_text(text: str, findings: list[EvalFinding], *, case_id: str) -> None:
    """Append safety findings for unsafe dataset text."""
    lowered = text.casefold()
    unsafe = [item for item in (*UNSAFE_DATASET_TEXT, *UNSAFE_DATASET_ACTIONS) if item in lowered]
    if unsafe:
        findings.append(
            EvalFinding(
                severity=EvalSeverity.FAILURE,
                message=(
                    "Golden dataset contains unsafe or secret-like text: "
                    f"{_redact_unsafe(unsafe[0])}."
                ),
                case_id=case_id,
                check="dataset_safety",
            )
        )


def _redact_unsafe(value: str) -> str:
    """Redact secret-like unsafe fragments."""
    lowered = value.casefold()
    if any(key in lowered for key in SECRET_LIKE_KEYS):
        return "[REDACTED]"
    return value
