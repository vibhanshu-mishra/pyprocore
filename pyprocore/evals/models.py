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
    RFI_WORKFLOW_PACKAGE = "rfi_workflow_package"
    SUBMITTAL_WORKFLOW_PACKAGE = "submittal_workflow_package"
    ASYNC_EXPORT_MANIFEST = "async_export_manifest"
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
    expected_fields: list[str] = Field(default_factory=list)
    required_phrases: list[str] = Field(default_factory=list)
    forbidden_phrases: list[str] = Field(default_factory=list)
    output_dir: str | None = None
    output_paths: list[str] = Field(default_factory=list)
    manifest_status: str | None = None
    allowed_capabilities: list[str] = Field(default_factory=list)
    allowed_hook_types: list[str] = Field(default_factory=list)
    placeholder_only: bool = False
    no_mutation_instructions: bool = False
    no_secret_like_values: bool = False


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


class EvalBaselineMetadata(ProcoreModel):
    """Metadata describing one local deterministic eval baseline.

    Attributes:
        baseline_name: Human-readable baseline name.
        created_at: UTC timestamp when the baseline was created.
        pyprocore_version: PyProcore version used to create the baseline.
        mode: Baseline mode. This is always local and deterministic.
        suite_count: Number of suites represented by the baseline.
        case_count: Number of cases represented by the baseline.
        total_score: Baseline score.
        max_score: Maximum possible baseline score.
        pass_count: Number of passing cases.
        fail_count: Number of failing cases.
        warning_count: Number of warnings.
        notes: Optional maintainer notes.
    """

    baseline_name: str
    created_at: datetime
    pyprocore_version: str
    mode: str = "local_deterministic"
    suite_count: int
    case_count: int
    total_score: int
    max_score: int
    pass_count: int
    fail_count: int
    warning_count: int
    notes: str | None = None


class EvalBaselineCase(ProcoreModel):
    """Baseline snapshot for one deterministic eval case."""

    case_id: str
    case_type: GoldenDatasetCaseType
    status: EvalStatus
    passed: bool
    score: int
    max_score: int
    finding_count: int = 0
    warning_count: int = 0
    failure_count: int = 0
    finding_messages: list[str] = Field(default_factory=list)


class EvalBaselineSuite(ProcoreModel):
    """Baseline snapshot for one deterministic eval suite."""

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
    cases: list[EvalBaselineCase] = Field(default_factory=list)


class EvalBaseline(ProcoreModel):
    """Local JSON-serializable baseline for deterministic eval results."""

    schema_version: Literal["1"] = "1"
    metadata: EvalBaselineMetadata
    suites: list[EvalBaselineSuite] = Field(default_factory=list)


class EvalRegressionSeverity(str, Enum):
    """Severity for deterministic baseline comparison findings."""

    PASS = "pass"
    INFO = "info"
    WARNING = "warning"
    FAILURE = "failure"


class EvalScoreDelta(ProcoreModel):
    """Score delta between a current eval result and a baseline."""

    baseline_score: int
    current_score: int
    baseline_max_score: int
    current_max_score: int

    @property
    def score_delta(self) -> int:
        """Return the current score minus the baseline score."""
        return self.current_score - self.baseline_score

    @property
    def max_score_delta(self) -> int:
        """Return the current max score minus the baseline max score."""
        return self.current_max_score - self.baseline_max_score


class EvalRegressionFinding(ProcoreModel):
    """One deterministic baseline comparison finding."""

    severity: EvalRegressionSeverity
    message: str
    suite_name: str | None = None
    case_id: str | None = None
    check: str | None = None
    score_delta: EvalScoreDelta | None = None


class EvalThresholdPolicy(ProcoreModel):
    """Local score and regression threshold policy.

    Attributes:
        minimum_total_score: Optional absolute minimum total score.
        minimum_score_ratio: Optional minimum score ratio from 0.0 to 1.0.
        allow_new_warnings: Whether new warnings are allowed.
        allow_new_failures: Whether new failures are allowed.
        max_allowed_failures: Maximum current failed case count.
        max_allowed_warnings: Maximum current warning count.
        fail_on_missing_suite: Whether missing suites fail the comparison.
        fail_on_missing_case: Whether missing cases fail the comparison.
        fail_on_score_drop: Whether any score drop fails the comparison.
        warning_on_new_suite: Whether new suites are informational warnings.
        notes: Optional maintainer notes.
    """

    minimum_total_score: int | None = None
    minimum_score_ratio: float | None = None
    allow_new_warnings: bool = True
    allow_new_failures: bool = False
    max_allowed_failures: int = 0
    max_allowed_warnings: int | None = None
    fail_on_missing_suite: bool = True
    fail_on_missing_case: bool = True
    fail_on_score_drop: bool = True
    warning_on_new_suite: bool = True
    notes: str | None = None


class EvalRegressionResult(ProcoreModel):
    """Result of comparing current deterministic eval output to a baseline."""

    generated_at: datetime
    mode: str = "local_deterministic"
    passed: bool
    status: EvalStatus
    baseline_name: str
    pyprocore_version: str
    suite_count: int
    case_count: int
    score: int
    max_score: int
    baseline_score: int
    baseline_max_score: int
    findings: list[EvalRegressionFinding] = Field(default_factory=list)
    threshold_policy: EvalThresholdPolicy | None = None


class EvalComparisonResult(ProcoreModel):
    """Alias-friendly comparison result model for deterministic eval regressions."""

    regression: EvalRegressionResult


class EvalHistorySnapshot(ProcoreModel):
    """Append-only local history snapshot for deterministic eval reports."""

    generated_at: datetime
    pyprocore_version: str
    mode: str = "local_deterministic"
    status: EvalStatus
    passed: bool
    total_suites: int
    total_cases: int
    passed_cases: int
    failed_cases: int
    warnings: int
    score: int
    max_score: int
    label: str | None = None


class EvalHistorySummary(ProcoreModel):
    """Summary of local deterministic eval history snapshots."""

    snapshot_count: int
    latest: EvalHistorySnapshot | None = None
    best_score: int | None = None
    worst_score: int | None = None
    score_trend: str = "none"
    snapshots: list[EvalHistorySnapshot] = Field(default_factory=list)
