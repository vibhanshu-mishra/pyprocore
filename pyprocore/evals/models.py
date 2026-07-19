"""Typed models for local deterministic PyProcore golden evals."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import Field

from pyprocore.models.base import ProcoreModel


class GoldenDatasetCaseType(str, Enum):
    """Supported local artifact categories for golden eval cases."""

    EXPORT_ROWS = "export_rows"
    AGENT_MANIFEST = "agent_manifest"
    AGENT_TOOL_SCHEMA = "agent_tool_schema"
    AI_WORKFLOW_PACKAGE = "ai_workflow_package"
    ASYNC_BATCH_PLAN = "async_batch_plan"
    ASYNC_BATCH_MANIFEST = "async_batch_manifest"
    PLUGIN_MANIFEST = "plugin_manifest"
    PLUGIN_CONFIG = "plugin_config"
    EXTENSION_PACK = "extension_pack"
    SAFETY_BOUNDARY = "safety_boundary"
    DOCS_TRUTH_SNIPPET = "docs_truth_snippet"


class EvalSeverity(str, Enum):
    """Severity for one deterministic eval finding."""

    PASS = "pass"
    INFO = "info"
    WARNING = "warning"
    FAILURE = "failure"


class EvalStatus(str, Enum):
    """Pass/fail/warning status for eval cases, suites, and reports."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


class GoldenDatasetMetadata(ProcoreModel):
    """Human-readable metadata for a local golden dataset."""

    name: str
    description: str
    owner: str = "pyprocore"
    tags: list[str] = Field(default_factory=list)
    mode: str = "local_deterministic"


class GoldenDatasetInput(ProcoreModel):
    """Input artifact for one golden dataset case."""

    artifact: Any
    artifact_name: str | None = None


class GoldenDatasetExpectedOutput(ProcoreModel):
    """Expected deterministic checks for one golden dataset case."""

    exact: Any | None = None
    required_keys: list[str] = Field(default_factory=list)
    forbidden_keys: list[str] = Field(default_factory=list)
    contains_text: list[str] = Field(default_factory=list)
    does_not_contain_text: list[str] = Field(default_factory=list)
    row_count: int | None = None
    required_values: dict[str, Any] = Field(default_factory=dict)
    json_serializable: bool = True
    redaction_required: bool = True
    manifest_required_keys: list[str] = Field(default_factory=list)


class GoldenDatasetCase(ProcoreModel):
    """One deterministic golden dataset case."""

    id: str
    case_type: GoldenDatasetCaseType
    description: str
    input: GoldenDatasetInput
    expected: GoldenDatasetExpectedOutput = Field(default_factory=GoldenDatasetExpectedOutput)
    tags: list[str] = Field(default_factory=list)


class GoldenDataset(ProcoreModel):
    """A local golden dataset containing deterministic eval cases."""

    schema_version: Literal["1"] = "1"
    metadata: GoldenDatasetMetadata
    cases: list[GoldenDatasetCase] = Field(default_factory=list)


class EvalSuite(ProcoreModel):
    """Metadata for a runnable deterministic eval suite."""

    name: str
    description: str
    dataset_name: str
    case_count: int


class EvalFinding(ProcoreModel):
    """One deterministic eval finding."""

    severity: EvalSeverity
    message: str
    case_id: str | None = None
    check: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class EvalScore(ProcoreModel):
    """Score for one deterministic check."""

    check: str
    passed: bool
    points: int
    max_points: int
    findings: list[EvalFinding] = Field(default_factory=list)


class EvalCaseResult(ProcoreModel):
    """Result for one deterministic eval case."""

    case_id: str
    case_type: GoldenDatasetCaseType
    status: EvalStatus
    passed: bool
    score: int
    max_score: int
    findings: list[EvalFinding] = Field(default_factory=list)


class EvalSuiteResult(ProcoreModel):
    """Result for one deterministic eval suite."""

    suite_name: str
    dataset_name: str
    status: EvalStatus
    passed: bool
    total_cases: int
    passed_cases: int
    failed_cases: int
    warnings: int
    score: int
    max_score: int
    findings: list[EvalFinding] = Field(default_factory=list)
    cases: list[EvalCaseResult] = Field(default_factory=list)


class EvalReport(ProcoreModel):
    """Report for one or more deterministic eval suites."""

    generated_at: datetime
    pyprocore_version: str
    mode: str = "local_deterministic"
    status: EvalStatus
    passed: bool
    total_suites: int
    passed_suites: int
    failed_suites: int
    total_cases: int
    passed_cases: int
    failed_cases: int
    warnings: int
    score: int
    max_score: int
    suites: list[EvalSuiteResult] = Field(default_factory=list)
