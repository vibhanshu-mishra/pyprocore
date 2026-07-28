"""JSON and Markdown rendering for intake sync artifacts."""

from __future__ import annotations

import json
from typing import Any

from pyprocore.intake.models import IntakeSyncFinding, IntakeSyncRunResult, IntakeSyncState


def intake_to_json(value: Any) -> str:
    """Render an intake model or local value as indented JSON."""
    payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    return json.dumps(payload, indent=2, sort_keys=True, default=str)


def intake_run_result_to_markdown(result: IntakeSyncRunResult) -> str:
    """Render a mocked intake result as Markdown."""
    summary = result.summary
    lines = [
        "# RFI/Submittal Intake Sync Summary",
        "",
        f"- Status: `{summary.status}`",
        f"- Projects: {summary.project_count}",
        f"- RFIs: {summary.rfi_count}",
        f"- Submittals: {summary.submittal_count}",
        f"- Attachment manifest items: {summary.attachment_count}",
        f"- Findings: {summary.finding_count}",
        "- Mode: mocked/local records only",
        "- Procore API calls made: false",
        "- Remote attachment downloads made: false",
        "- Procore write actions enabled: false",
        "",
        "GC/Owner installation, permitted projects, and DMSA permissions control "
        "live visibility. PyProcore does not grant access.",
    ]
    if result.findings:
        lines.extend(["", "## Findings"])
        lines.extend(
            f"- **{item.level}: {item.code}** - {item.message}" for item in result.findings
        )
    return "\n".join(lines) + "\n"


def intake_validation_to_markdown(findings: list[IntakeSyncFinding]) -> str:
    """Render intake configuration findings as Markdown."""
    valid = not any(item.level == "error" for item in findings)
    lines = [
        "# Intake Configuration Validation",
        "",
        f"**Valid:** {'Yes' if valid else 'No'}",
        "",
    ]
    if not findings:
        lines.append("No findings.")
    else:
        lines.append("## Findings")
        lines.extend(f"- **{item.level}: {item.code}** - {item.message}" for item in findings)
    return "\n".join(lines) + "\n"


def intake_state_to_markdown(state: IntakeSyncState) -> str:
    """Render local intake state as Markdown."""
    return (
        "\n".join(
            [
                "# Intake Sync State",
                "",
                f"- Profile: {state.profile_name or 'Not documented'}",
                f"- Company ID: {state.company_id or 'Not documented'}",
                f"- Projects: {', '.join(str(value) for value in state.project_ids) or 'None'}",
                f"- Last status: {state.last_run_status or 'Never run'}",
                f"- Last attempted: {state.last_attempted_sync_at or 'Never'}",
                f"- Last successful: {state.last_successful_sync_at or 'Never'}",
                f"- Record counts: {state.record_counts}",
                "",
                "This state contains polling metadata only. It contains no credentials.",
            ]
        )
        + "\n"
    )
