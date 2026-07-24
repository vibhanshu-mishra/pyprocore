"""Deterministic local scoring helpers for project health recipes."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

from pyprocore.analytics.loaders import redact_sensitive_data
from pyprocore.analytics.models import (
    AnalyticsSeverity,
    ChangeExposureSummary,
    DailyLogCompletenessSummary,
    ProjectHealthFinding,
    ProjectHealthInput,
    ProjectHealthLabel,
    ProjectHealthReport,
    RfiAgingSummary,
    SubmittalDelaySummary,
)

OPEN_STATUSES = {"open", "draft", "pending", "review", "in review", "unanswered"}
CLOSED_STATUSES = {"closed", "answered", "approved", "rejected", "void", "voided", "complete"}
APPROVED_STATUSES = {"approved", "executed", "complete", "completed"}
REJECTED_STATUSES = {"rejected", "void", "voided", "canceled", "cancelled"}


def analyze_rfi_aging(
    records: list[dict[str, Any]],
    *,
    today: date | None = None,
) -> RfiAgingSummary:
    """Analyze local RFI records for aging and overdue review risk."""
    current_date = today or date.today()
    sanitized = [redact_sensitive_data(record) for record in records]
    open_records = [record for record in sanitized if _is_open_status(_text(record.get("status")))]
    ages = [_age_days(record.get("created_at"), current_date) for record in open_records]
    overdue_records = [
        record for record in open_records if _date_before(record.get("due_date"), current_date)
    ]
    average_age = _average([age for age in ages if age is not None])
    max_age = max([age for age in ages if age is not None], default=0)
    score = _clamp(
        (len(overdue_records) * 12)
        + (average_age * 1.2)
        + (max_age * 0.4)
        + (len(open_records) * 2)
    )
    findings = _rfi_findings(open_records, overdue_records, current_date)
    return RfiAgingSummary(
        record_count=len(sanitized),
        open_count=len(open_records),
        overdue_count=len(overdue_records),
        average_age_days=round(average_age, 2),
        max_age_days=max_age,
        risk_score=score,
        severity=_severity(score),
        findings=findings,
    )


def analyze_submittal_delay(
    records: list[dict[str, Any]],
    *,
    today: date | None = None,
    due_soon_days: int = 7,
) -> SubmittalDelaySummary:
    """Analyze local submittal records for due-date delay risk."""
    current_date = today or date.today()
    sanitized = [redact_sensitive_data(record) for record in records]
    pending_records = [
        record for record in sanitized if _is_open_status(_text(record.get("status")))
    ]
    overdue_records = [
        record for record in pending_records if _date_before(record.get("due_date"), current_date)
    ]
    due_soon_records = [
        record
        for record in pending_records
        if _date_in_window(record.get("due_date"), current_date, due_soon_days)
    ]
    overdue_days = _compact_ints(
        [_days_between(record.get("due_date"), current_date) for record in overdue_records]
    )
    average_overdue = _average([max(days, 0) for days in overdue_days])
    score = _clamp(
        (len(overdue_records) * 15)
        + (average_overdue * 2)
        + (len(due_soon_records) * 5)
        + (len(pending_records) * 1.5)
    )
    findings = _submittal_findings(overdue_records, due_soon_records, current_date)
    return SubmittalDelaySummary(
        record_count=len(sanitized),
        pending_count=len(pending_records),
        overdue_count=len(overdue_records),
        due_soon_count=len(due_soon_records),
        average_days_overdue=round(average_overdue, 2),
        risk_score=score,
        severity=_severity(score),
        findings=findings,
    )


def analyze_change_exposure(records: list[dict[str, Any]]) -> ChangeExposureSummary:
    """Summarize local change exposure records."""
    sanitized = [redact_sensitive_data(record) for record in records]
    total = 0.0
    open_exposure = 0.0
    approved = 0.0
    rejected = 0.0
    counts: dict[str, int] = {}
    for record in sanitized:
        status = _normalized_status(record.get("status"))
        amount = _amount(record)
        total += amount
        counts[status] = counts.get(status, 0) + 1
        if status in APPROVED_STATUSES:
            approved += amount
        elif status in REJECTED_STATUSES:
            rejected += amount
        else:
            open_exposure += amount
    exposure_ratio = (open_exposure / total) if total > 0 else 0
    score = _clamp((exposure_ratio * 65) + (len(sanitized) * 3) + min(open_exposure / 10000, 25))
    findings = _change_findings(sanitized, open_exposure, total)
    return ChangeExposureSummary(
        record_count=len(sanitized),
        total_estimated_exposure=round(total, 2),
        open_exposure=round(open_exposure, 2),
        approved_exposure=round(approved, 2),
        rejected_or_void_exposure=round(rejected, 2),
        count_by_status=dict(sorted(counts.items())),
        risk_score=score,
        severity=_severity(score),
        findings=findings,
    )


def analyze_daily_log_completeness(
    records: list[dict[str, Any]],
    *,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
) -> DailyLogCompletenessSummary:
    """Analyze local daily log records for date coverage completeness."""
    sanitized = [redact_sensitive_data(record) for record in records]
    days_with_logs = {
        parsed.isoformat()
        for record in sanitized
        for parsed in [_parse_date(record.get("date") or record.get("log_date"))]
        if parsed is not None
    }
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    expected_dates: list[str] | None = None
    if start is not None and end is not None and end >= start:
        expected_dates = [
            (start + timedelta(days=offset)).isoformat() for offset in range((end - start).days + 1)
        ]
    if expected_dates is None:
        missing_days: list[str] = []
        expected_count = None
        completeness = 100.0 if days_with_logs else 0.0
    else:
        missing_days = [day for day in expected_dates if day not in days_with_logs]
        expected_count = len(expected_dates)
        completeness = (
            ((expected_count - len(missing_days)) / expected_count) * 100
            if expected_count
            else 100.0
        )
    score = _clamp(100 - completeness)
    if expected_dates and len(missing_days) >= 3:
        score = _clamp(score + 10)
    findings = _daily_log_findings(missing_days, completeness)
    return DailyLogCompletenessSummary(
        record_count=len(sanitized),
        expected_date_count=expected_count,
        days_with_logs=len(days_with_logs),
        missing_days=missing_days,
        completeness_percentage=round(completeness, 2),
        risk_score=score,
        severity=_severity(score),
        findings=findings,
    )


def build_project_health_report(
    project_input: ProjectHealthInput,
    *,
    today: date | None = None,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
) -> ProjectHealthReport:
    """Build a combined local project health report from available components."""
    components: dict[str, tuple[float, float, list[ProjectHealthFinding]]] = {}
    rfi_summary = None
    submittal_summary = None
    change_summary = None
    daily_log_summary = None
    if project_input.rfis:
        rfi_summary = analyze_rfi_aging(project_input.rfis, today=today)
        components["rfi_aging"] = (rfi_summary.risk_score, 0.30, rfi_summary.findings)
    if project_input.submittals:
        submittal_summary = analyze_submittal_delay(project_input.submittals, today=today)
        components["submittal_delay"] = (
            submittal_summary.risk_score,
            0.30,
            submittal_summary.findings,
        )
    if project_input.changes:
        change_summary = analyze_change_exposure(project_input.changes)
        components["change_exposure"] = (
            change_summary.risk_score,
            0.25,
            change_summary.findings,
        )
    if project_input.daily_logs:
        daily_log_summary = analyze_daily_log_completeness(
            project_input.daily_logs,
            start_date=start_date,
            end_date=end_date,
        )
        components["daily_log_completeness"] = (
            daily_log_summary.risk_score,
            0.15,
            daily_log_summary.findings,
        )
    score, weights = _weighted_score(components)
    findings = _top_findings([finding for _, _, items in components.values() for finding in items])
    return ProjectHealthReport(
        overall_score=score,
        health_label=_health_label(score),
        component_scores={name: round(data[0], 2) for name, data in components.items()},
        component_weights=weights,
        top_findings=findings,
        recommended_next_reviews=_review_recommendations(findings),
        rfi_aging=rfi_summary,
        submittal_delay=submittal_summary,
        change_exposure=change_summary,
        daily_log_completeness=daily_log_summary,
        data_source=project_input.source_description,
    )


def _rfi_findings(
    open_records: list[dict[str, Any]],
    overdue_records: list[dict[str, Any]],
    current_date: date,
) -> list[ProjectHealthFinding]:
    findings: list[ProjectHealthFinding] = []
    for record in overdue_records[:5]:
        due_date = _parse_date(record.get("due_date"))
        days = (current_date - due_date).days if due_date else 0
        findings.append(
            ProjectHealthFinding(
                severity="high" if days < 14 else "critical",
                title=f"RFI {record.get('number', record.get('id', 'unknown'))} is overdue",
                reason=f"Due date is {days} days behind the review date.",
                record_id=record.get("id"),
                recommended_review="Review ball-in-court and responsible contractor context.",
            )
        )
    aged = [
        record
        for record in open_records
        if (_age_days(record.get("created_at"), current_date) or 0) > 30
    ]
    if aged:
        findings.append(
            ProjectHealthFinding(
                severity="medium",
                title="Open RFIs older than 30 days",
                reason=f"{len(aged)} open RFI record(s) are older than 30 days.",
                recommended_review="Review older open RFIs for schedule or coordination risk.",
            )
        )
    return findings


def _submittal_findings(
    overdue_records: list[dict[str, Any]],
    due_soon_records: list[dict[str, Any]],
    current_date: date,
) -> list[ProjectHealthFinding]:
    findings: list[ProjectHealthFinding] = []
    for record in overdue_records[:5]:
        due_date = _parse_date(record.get("due_date"))
        days = (current_date - due_date).days if due_date else 0
        findings.append(
            ProjectHealthFinding(
                severity="high" if days < 10 else "critical",
                title=f"Submittal {record.get('number', record.get('id', 'unknown'))} is overdue",
                reason=f"Due date is {days} days behind the review date.",
                record_id=record.get("id"),
                recommended_review="Review reviewer workload and required-on-site dates.",
            )
        )
    if due_soon_records:
        findings.append(
            ProjectHealthFinding(
                severity="medium",
                title="Submittals due soon",
                reason=f"{len(due_soon_records)} pending submittal record(s) are due soon.",
                recommended_review=(
                    "Review upcoming submittal due dates before they become overdue."
                ),
            )
        )
    return findings


def _change_findings(
    records: list[dict[str, Any]],
    open_exposure: float,
    total_exposure: float,
) -> list[ProjectHealthFinding]:
    findings: list[ProjectHealthFinding] = []
    if open_exposure > 0:
        findings.append(
            ProjectHealthFinding(
                severity="medium" if open_exposure < 50000 else "high",
                title="Open change exposure exists",
                reason=f"Open estimated exposure is {open_exposure:.2f} of {total_exposure:.2f}.",
                recommended_review=(
                    "Review open change items with project controls or finance context."
                ),
            )
        )
    large_records = [record for record in records if _amount(record) >= 50000]
    if large_records:
        findings.append(
            ProjectHealthFinding(
                severity="high",
                title="Large change exposure records found",
                reason=(
                    f"{len(large_records)} change record(s) are at least 50000 in "
                    "estimated exposure."
                ),
                recommended_review="Review large change exposure records individually.",
            )
        )
    return findings


def _daily_log_findings(
    missing_days: list[str],
    completeness: float,
) -> list[ProjectHealthFinding]:
    if not missing_days:
        return []
    severity: AnalyticsSeverity = "medium"
    if completeness < 70:
        severity = "high"
    if completeness < 50:
        severity = "critical"
    return [
        ProjectHealthFinding(
            severity=severity,
            title="Missing daily log dates",
            reason=f"{len(missing_days)} expected date(s) have no local daily log record.",
            recommended_review=(
                "Review whether logs are missing, exported separately, or outside the selected "
                "range."
            ),
        )
    ]


def _compact_ints(values: list[int | None]) -> list[int]:
    return [value for value in values if value is not None]


def _weighted_score(
    components: dict[str, tuple[float, float, list[ProjectHealthFinding]]],
) -> tuple[float, dict[str, float]]:
    if not components:
        return 0.0, {}
    total_weight = sum(weight for _, weight, _ in components.values())
    normalized = {
        name: round(weight / total_weight, 4) for name, (_, weight, _) in components.items()
    }
    score = sum(score * normalized[name] for name, (score, _, _) in components.items())
    return round(score, 2), normalized


def _top_findings(findings: list[ProjectHealthFinding]) -> list[ProjectHealthFinding]:
    priority = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(findings, key=lambda item: priority[item.severity])[:8]


def _review_recommendations(findings: list[ProjectHealthFinding]) -> list[str]:
    recommendations = [
        finding.recommended_review for finding in findings if finding.recommended_review
    ]
    unique: list[str] = []
    for item in recommendations:
        if item not in unique:
            unique.append(item)
    if not unique:
        unique.append(
            "Review the local source data and confirm it reflects the intended project period."
        )
    return unique[:5]


def _severity(score: float) -> AnalyticsSeverity:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _health_label(score: float) -> ProjectHealthLabel:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "at_risk"
    if score >= 25:
        return "watch"
    return "healthy"


def _is_open_status(status: str) -> bool:
    normalized = _normalized_status(status)
    if normalized in CLOSED_STATUSES:
        return False
    return normalized in OPEN_STATUSES or normalized not in CLOSED_STATUSES


def _normalized_status(value: Any) -> str:
    status = _text(value).casefold().replace("_", " ").replace("-", " ").strip()
    return "unknown" if not status else " ".join(status.split())


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    raw = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw).astimezone(UTC).date()
    except ValueError:
        pass
    for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(raw[:10], pattern).date()
        except ValueError:
            continue
    return None


def _age_days(created_at: Any, current_date: date) -> int | None:
    created = _parse_date(created_at)
    if created is None:
        return None
    return max((current_date - created).days, 0)


def _days_between(value: Any, current_date: date) -> int | None:
    parsed = _parse_date(value)
    if parsed is None:
        return None
    return (current_date - parsed).days


def _date_before(value: Any, current_date: date) -> bool:
    parsed = _parse_date(value)
    return parsed is not None and parsed < current_date


def _date_in_window(value: Any, current_date: date, days: int) -> bool:
    parsed = _parse_date(value)
    return parsed is not None and current_date <= parsed <= current_date + timedelta(days=days)


def _average(values: list[int | float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _amount(record: dict[str, Any]) -> float:
    for key in (
        "estimated_exposure",
        "estimated_amount",
        "amount",
        "value",
        "budget_exposure",
        "latest_price",
        "total",
    ):
        if key in record:
            return _parse_amount(record.get(key))
    return 0.0


def _parse_amount(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, int | float):
        return float(value)
    cleaned = re.sub(r"[^0-9.\-]", "", str(value))
    if cleaned in {"", "-", "."}:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)
