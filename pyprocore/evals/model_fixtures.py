"""Offline model-response fixture loading and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from pyprocore.core.exceptions import ValidationError
from pyprocore.evals.models import (
    EvalSeverity,
    ModelResponseFinding,
    ModelResponseFixture,
    ModelResponseFixtureType,
)
from pyprocore.evals.scoring import SECRET_LIKE_KEYS

MODEL_FIXTURE_SCHEMA_VERSION = "1"
UNSAFE_MODEL_FIXTURE_FIELDS = (
    "access_token",
    "refresh_token",
    "client_secret",
    "authorization",
    "api_key",
)
UNSAFE_MODEL_FIXTURE_TEXT = (
    "authorization:",
    "bearer ",
    "sk-",
    "x-api-key",
    "http://",
    "https://",
    " ".join(("pip", "install")),
    "curl ",
    "wget ",
)


def load_model_response_fixture_from_dict(data: dict[str, Any]) -> ModelResponseFixture:
    """Load and validate one offline model-response fixture from a dictionary."""
    try:
        fixture = ModelResponseFixture.model_validate(data)
    except PydanticValidationError as exc:
        raise ValidationError(f"Invalid model-response fixture: {_redact_text(str(exc))}") from exc
    findings = validate_model_response_fixture(fixture)
    errors = [finding for finding in findings if finding.severity == EvalSeverity.FAILURE]
    if errors:
        messages = "; ".join(finding.message for finding in errors)
        raise ValidationError(f"Invalid model-response fixture: {_redact_text(messages)}")
    return fixture


def load_model_response_fixture_from_file(path: Path | str) -> ModelResponseFixture:
    """Load and validate one local JSON model-response fixture file."""
    fixture_path = validate_local_model_fixture_path(path)
    try:
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON model-response fixture: {fixture_path}") from exc
    if not isinstance(data, dict):
        raise ValidationError("Model-response fixture JSON must be an object.")
    return load_model_response_fixture_from_dict(data)


def validate_local_model_fixture_path(path: Path | str, *, must_exist: bool = True) -> Path:
    """Validate a local JSON fixture path without remote URLs or traversal."""
    fixture_path = Path(path)
    path_text = str(fixture_path)
    if "://" in path_text or path_text.casefold().startswith(("http:", "https:")):
        raise ValidationError("Model-response fixture path must be local, not a URL.")
    if any(part == ".." for part in fixture_path.parts):
        raise ValidationError("Model-response fixture path must not contain path traversal.")
    if fixture_path.suffix != ".json":
        raise ValidationError("Model-response fixture path must end with .json.")
    if must_exist and not fixture_path.exists():
        raise ValidationError(f"Model-response fixture file not found: {fixture_path}")
    return fixture_path


def validate_model_response_fixture(fixture: ModelResponseFixture) -> list[ModelResponseFinding]:
    """Validate one offline fixture without scoring response quality."""
    findings: list[ModelResponseFinding] = []
    if fixture.schema_version != MODEL_FIXTURE_SCHEMA_VERSION:
        findings.append(_finding("fixture_schema", False, "Unsupported fixture schema version."))
    if fixture.fixture_type not in set(ModelResponseFixtureType):
        findings.append(_finding("fixture_type", False, "Unsupported fixture type."))
    if fixture.response_text is None and fixture.response_json is None:
        findings.append(
            _finding(
                "fixture_response", False, "Fixture must include response_text or response_json."
            )
        )
    searchable_payload = fixture.model_dump(mode="json")
    _scan_safe_fields(searchable_payload, findings)
    return findings or [_finding("fixture_validation", True, "Model-response fixture is valid.")]


def model_response_fixture_to_json(
    fixture: ModelResponseFixture,
    *,
    pretty: bool = True,
) -> str:
    """Serialize one model-response fixture to deterministic JSON text."""
    return json.dumps(
        fixture.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=True,
    )


def sample_model_response_fixture() -> ModelResponseFixture:
    """Return a safe placeholder offline response fixture."""
    return load_model_response_fixture_from_dict(
        {
            "schema_version": MODEL_FIXTURE_SCHEMA_VERSION,
            "fixture_name": "sample_rfi_review_response",
            "fixture_type": "rfi_review_response",
            "workflow_name": "rfi_review",
            "input_context": {
                "prompt": "Review the sample RFI using only provided sources.",
                "context_summary": "Placeholder RFI context with labeled sources.",
                "source_labels": ["RFI-001", "SPEC-001"],
            },
            "expected_behavior": {
                "expected_sections": ["Summary", "Sources", "Limitations"],
                "required_phrases": ["based on the provided context"],
                "forbidden_phrases": ["I approved this submittal"],
                "citations": {
                    "allowed_labels": ["RFI-001", "SPEC-001"],
                    "required_labels": ["RFI-001"],
                },
                "grounding": {
                    "expected_sources": ["RFI-001"],
                    "required_statement": "based on the provided context",
                },
            },
            "response_text": (
                "Summary\nBased on the provided context, the sample RFI asks for a "
                "coordination clarification. [RFI-001]\n\nSources\n- [RFI-001]\n\n"
                "Limitations\nThis is a local fixture and requires human review."
            ),
            "notes": "Safe local sample. No model or Procore calls are made.",
        }
    )


def _scan_safe_fields(value: Any, findings: list[ModelResponseFinding]) -> None:
    """Scan metadata fields for secrets, URLs, and executable hints."""
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).casefold()
            if key_text in UNSAFE_MODEL_FIXTURE_FIELDS:
                findings.append(_finding("fixture_safety", False, "Fixture contains secret field."))
            _scan_safe_fields(item, findings)
        return
    if isinstance(value, list):
        for item in value:
            _scan_safe_fields(item, findings)
        return
    if isinstance(value, str):
        lowered = value.casefold()
        unsafe = [item for item in UNSAFE_MODEL_FIXTURE_TEXT if item in lowered]
        if unsafe:
            findings.append(
                _finding(
                    "fixture_safety",
                    False,
                    f"Fixture contains unsafe local-only text: {_redact_text(unsafe[0])}.",
                )
            )


def _finding(check: str, passed: bool, message: str) -> ModelResponseFinding:
    """Build one fixture validation finding."""
    return ModelResponseFinding(
        check=check,
        severity=EvalSeverity.PASS if passed else EvalSeverity.FAILURE,
        passed=passed,
        message=message,
    )


def _redact_text(value: str) -> str:
    """Redact secret-like fragments from validation errors."""
    lowered = value.casefold()
    if any(key in lowered for key in (*SECRET_LIKE_KEYS, "api_key", "sk-")):
        return "[REDACTED]"
    return value
