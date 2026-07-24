"""Typed models for local project health analytics recipes."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

AnalyticsSeverity = Literal["low", "medium", "high", "critical"]
ProjectHealthLabel = Literal["healthy", "watch", "at_risk", "critical"]


class ProjectHealthInput(BaseModel):
    """Local Procore-style exported records used by analytics recipes.

    Attributes:
        rfis: Local RFI records.
        submittals: Local submittal records.
        changes: Local change exposure records.
        daily_logs: Local daily log records.
        source_description: Human-readable source label.
    """

    rfis: list[dict[str, Any]] = Field(default_factory=list)
    submittals: list[dict[str, Any]] = Field(default_factory=list)
    changes: list[dict[str, Any]] = Field(default_factory=list)
    daily_logs: list[dict[str, Any]] = Field(default_factory=list)
    source_description: str = "local/exported data"


class ProjectHealthSignal(BaseModel):
    """A transparent numeric signal used in a health recipe."""

    name: str
    value: float | int | str
    description: str


class ProjectHealthFinding(BaseModel):
    """Review-oriented finding generated from local analytics recipes."""

    severity: AnalyticsSeverity
    title: str
    reason: str
    record_id: str | int | None = None
    recommended_review: str | None = None


class ProjectHealthScore(BaseModel):
    """A normalized heuristic score where higher means higher review risk."""

    score: float
    label: AnalyticsSeverity | ProjectHealthLabel
    signals: list[ProjectHealthSignal] = Field(default_factory=list)


class RfiAgingSummary(BaseModel):
    """RFI aging recipe output from local records."""

    record_count: int
    open_count: int
    overdue_count: int
    average_age_days: float
    max_age_days: int
    risk_score: float
    severity: AnalyticsSeverity
    findings: list[ProjectHealthFinding] = Field(default_factory=list)


class SubmittalDelaySummary(BaseModel):
    """Submittal delay recipe output from local records."""

    record_count: int
    pending_count: int
    overdue_count: int
    due_soon_count: int
    average_days_overdue: float
    risk_score: float
    severity: AnalyticsSeverity
    findings: list[ProjectHealthFinding] = Field(default_factory=list)


class ChangeExposureSummary(BaseModel):
    """Change exposure recipe output from local records."""

    record_count: int
    total_estimated_exposure: float
    open_exposure: float
    approved_exposure: float
    rejected_or_void_exposure: float
    count_by_status: dict[str, int] = Field(default_factory=dict)
    risk_score: float
    severity: AnalyticsSeverity
    findings: list[ProjectHealthFinding] = Field(default_factory=list)


class DailyLogCompletenessSummary(BaseModel):
    """Daily log completeness recipe output from local records."""

    record_count: int
    expected_date_count: int | None
    days_with_logs: int
    missing_days: list[str] = Field(default_factory=list)
    completeness_percentage: float
    risk_score: float
    severity: AnalyticsSeverity
    findings: list[ProjectHealthFinding] = Field(default_factory=list)


class ProjectHealthReport(BaseModel):
    """Combined local project health report."""

    overall_score: float
    health_label: ProjectHealthLabel
    component_scores: dict[str, float] = Field(default_factory=dict)
    component_weights: dict[str, float] = Field(default_factory=dict)
    top_findings: list[ProjectHealthFinding] = Field(default_factory=list)
    recommended_next_reviews: list[str] = Field(default_factory=list)
    rfi_aging: RfiAgingSummary | None = None
    submittal_delay: SubmittalDelaySummary | None = None
    change_exposure: ChangeExposureSummary | None = None
    daily_log_completeness: DailyLogCompletenessSummary | None = None
    data_source: str = "local/exported data"
    procore_api_call_required: bool = False
    external_ai_call_required: bool = False
    write_actions_enabled: bool = False
    scoring_note: str = (
        "Heuristic, review-oriented project health analytics. Validate outputs "
        "against your own project context."
    )


class ProjectHealthRecipeResult(BaseModel):
    """Generic wrapper for one local analytics recipe result."""

    recipe: str
    summary: (
        RfiAgingSummary
        | SubmittalDelaySummary
        | ChangeExposureSummary
        | DailyLogCompletenessSummary
        | ProjectHealthReport
    )
    data_source: str = "local/exported data"
    procore_api_call_required: bool = False
    external_ai_call_required: bool = False
    write_actions_enabled: bool = False
