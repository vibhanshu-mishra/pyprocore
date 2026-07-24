"""Local API compatibility contracts, validation, diffs, and usage comparison."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from pyprocore import __version__
from pyprocore.catalog import PYPROCORE_SUPPORTED_AREAS
from pyprocore.core.exceptions import ValidationError
from pyprocore.discovery import list_discovery_capabilities
from pyprocore.maintenance.codebase import scan_pyprocore_usage
from pyprocore.maintenance.models import (
    ApiCompatibilityChange,
    ApiCompatibilityContract,
    ApiCompatibilityContractOptions,
    ApiCompatibilityDeprecation,
    ApiCompatibilityDiffReport,
    ApiCompatibilityKnownGap,
    ApiCompatibilityOperation,
    ApiCompatibilityResource,
    ApiCompatibilitySafetyBoundary,
    ApiCompatibilityValidationFinding,
    ApiCompatibilityValidationReport,
    CodebaseCompatibilityReport,
    PyprocoreUsage,
)

COMPATIBILITY_SCHEMA_VERSION = "1"
LOCAL_ONLY_FAMILIES = {
    "analytics",
    "automation",
    "catalog",
    "discovery",
    "evals",
    "integrations",
    "maintenance",
    "mcp",
    "plugins",
    "templates",
    "workflows",
}
SUPPORTED_CLI_GROUPS = [
    "agent",
    "analytics",
    "auth",
    "catalog",
    "companies",
    "discovery",
    "documents",
    "drawings",
    "enterprise",
    "evals",
    "integrations",
    "maintenance",
    "mcp",
    "plugins",
    "projects",
    "rfis",
    "submittals",
    "templates",
    "token-store",
    "webhook",
    "workflow-plan",
]
LOCAL_ONLY_FEATURES = [
    "agent discovery metadata",
    "analytics recipes over local exported data",
    "API maintenance reports and draft artifacts",
    "compatibility contracts",
    "discovery router metadata",
    "integration blueprints",
    "local automation plans",
    "MCP discovery metadata",
    "plugin metadata and trust validation",
    "starter templates",
]


def build_current_compatibility_contract(
    options: ApiCompatibilityContractOptions | None = None,
) -> ApiCompatibilityContract:
    """Build deterministic compatibility metadata for the current package."""
    contract_options = options or ApiCompatibilityContractOptions()
    resources = []
    for capability in list_discovery_capabilities():
        local_only = capability.resource_family in LOCAL_ONLY_FAMILIES
        resources.append(
            ApiCompatibilityResource(
                name=capability.resource_family,
                category="local_only" if local_only else "procore_read",
                operations=[
                    ApiCompatibilityOperation(
                        name=operation,
                        read_only=True,
                        local_only=local_only,
                    )
                    for operation in sorted(capability.operations)
                ],
                read_only=True,
                local_only=local_only,
            )
        )
    resources = _deduplicate_resources(resources)
    return ApiCompatibilityContract(
        contract_schema_version=COMPATIBILITY_SCHEMA_VERSION,
        pyprocore_version=__version__,
        generated_at=contract_options.generated_at,
        resources=resources,
        supported_read_only_service_areas=sorted(PYPROCORE_SUPPORTED_AREAS),
        supported_cli_groups=SUPPORTED_CLI_GROUPS,
        local_only_features=LOCAL_ONLY_FEATURES,
        safety_boundaries=_current_safety_boundaries(),
        known_gaps=[
            ApiCompatibilityKnownGap(
                family=family,
                status="deferred",
                reason=reason,
            )
            for family, reason in [
                (
                    "project_emails",
                    "A safe unambiguous read-only endpoint shape is not yet confirmed.",
                ),
                (
                    "transmittals",
                    "A safe unambiguous read-only endpoint shape is not yet confirmed.",
                ),
                (
                    "workforce_resource_requests",
                    "Company/group/project context remains too ambiguous for safe coverage.",
                ),
            ]
        ],
    )


def validate_compatibility_contract(
    contract: ApiCompatibilityContract | Mapping[str, Any],
) -> ApiCompatibilityValidationReport:
    """Validate required metadata and non-negotiable safety boundaries."""
    findings: list[ApiCompatibilityValidationFinding] = []
    typed: ApiCompatibilityContract | None
    if isinstance(contract, ApiCompatibilityContract):
        typed = contract
    else:
        required = [
            "contract_schema_version",
            "pyprocore_version",
            "resources",
            "safety_boundaries",
        ]
        for field in required:
            if not contract.get(field):
                findings.append(
                    _validation_finding("error", "missing_required_field", f"Missing {field}.")
                )
        try:
            typed = ApiCompatibilityContract.model_validate(contract)
        except PydanticValidationError as exc:
            findings.append(
                _validation_finding(
                    "error",
                    "invalid_contract_shape",
                    f"Contract does not match the compatibility schema: {exc.errors()[0]['msg']}",
                )
            )
            typed = None

    if typed is None:
        return ApiCompatibilityValidationReport(valid=False, findings=findings)
    if not typed.pyprocore_version:
        findings.append(
            _validation_finding("error", "missing_version", "PyProcore version is required.")
        )
    if not typed.contract_schema_version:
        findings.append(
            _validation_finding("error", "missing_schema", "Contract schema version is required.")
        )
    if not typed.safety_boundaries:
        findings.append(
            _validation_finding(
                "error",
                "missing_safety_boundaries",
                "At least one explicit safety boundary is required.",
            )
        )
    boundaries = {boundary.name: boundary.status for boundary in typed.safety_boundaries}
    required_boundaries = {
        "mcp": "discovery_only",
        "procore_write_actions": "disabled",
        "tool_execution": "disabled",
        "external_ai_model_calls": "none",
        "maintenance_remote_fetch": "none",
        "automatic_pull_requests": "disabled",
        "automatic_commits": "disabled",
    }
    for name, status in required_boundaries.items():
        if boundaries.get(name) != status:
            findings.append(
                _validation_finding(
                    "error",
                    "unsafe_or_missing_boundary",
                    f"Safety boundary {name!r} must be {status!r}.",
                )
            )
    known_names = {
        capability.resource_family for capability in list_discovery_capabilities()
    } | set(PYPROCORE_SUPPORTED_AREAS)
    for resource in typed.resources:
        if resource.name not in known_names:
            findings.append(
                _validation_finding(
                    "warning",
                    "unknown_resource_family",
                    f"Unknown resource family requires manual review: {resource.name}",
                )
            )
        if not resource.read_only:
            findings.append(
                _validation_finding(
                    "error",
                    "write_enabled_claim",
                    f"Resource family claims write support: {resource.name}",
                )
            )
    for item in [*typed.deprecations, *typed.removed_helpers]:
        if not item.migration_note.strip():
            findings.append(
                _validation_finding(
                    "error",
                    "missing_migration_note",
                    f"Migration note is required for {item.helper}.",
                )
            )
    return ApiCompatibilityValidationReport(
        valid=not any(row.severity == "error" for row in findings),
        findings=findings,
        contract=typed,
    )


def load_compatibility_contract(path: str | Path) -> ApiCompatibilityContract:
    """Load one local JSON compatibility contract without remote access."""
    source = _validate_local_json_path(path)
    payload = _load_json_mapping(source)
    report = validate_compatibility_contract(payload)
    if report.contract is None:
        message = report.findings[0].message if report.findings else "Invalid contract."
        raise ValidationError(message)
    return report.contract


def validate_compatibility_contract_file(
    path: str | Path,
) -> ApiCompatibilityValidationReport:
    """Validate one local JSON file and retain structured invalid findings."""
    source = _validate_local_json_path(path)
    return validate_compatibility_contract(_load_json_mapping(source))


def write_compatibility_contract(
    contract: ApiCompatibilityContract,
    path: str | Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Write one requested local JSON contract file without touching other paths."""
    destination = Path(path).expanduser().resolve()
    if destination.suffix.lower() != ".json":
        raise ValidationError("Compatibility contract output must use a .json suffix.")
    if destination.exists() and not overwrite:
        raise ValidationError(
            f"Compatibility contract already exists; use --overwrite: {destination}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(contract.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def diff_compatibility_contracts(
    old_contract_path: str | Path,
    new_contract_path: str | Path,
) -> ApiCompatibilityDiffReport:
    """Compare two local JSON compatibility contracts."""
    old_path = _validate_local_json_path(old_contract_path)
    new_path = _validate_local_json_path(new_contract_path)
    old = load_compatibility_contract(old_path)
    new = load_compatibility_contract(new_path)
    old_resources = {resource.name for resource in old.resources}
    new_resources = {resource.name for resource in new.resources}
    old_cli = set(old.supported_cli_groups)
    new_cli = set(new.supported_cli_groups)
    old_deprecations = {item.helper: item for item in old.deprecations}
    new_deprecations = {item.helper: item for item in new.deprecations}
    safety_changes = _changed_boundaries(old, new)
    gap_changes = _changed_gaps(old, new)
    added_resources = sorted(new_resources - old_resources)
    removed_resources = sorted(old_resources - new_resources)
    added_deprecations = [
        new_deprecations[name] for name in sorted(new_deprecations.keys() - old_deprecations)
    ]
    removed_deprecations = [
        old_deprecations[name] for name in sorted(old_deprecations.keys() - new_deprecations)
    ]
    changes = [
        *[
            ApiCompatibilityChange(
                change_type="added_resource_family",
                subject=name,
                risk_level="low",
                migration_note="No migration is required; review newly available metadata.",
            )
            for name in added_resources
        ],
        *[
            ApiCompatibilityChange(
                change_type="removed_resource_family",
                subject=name,
                risk_level="high",
                migration_note="Review all usage of this family before upgrading.",
            )
            for name in removed_resources
        ],
        *safety_changes,
        *gap_changes,
    ]
    risk_level = (
        "high"
        if removed_resources or any(row.risk_level == "high" for row in changes)
        else "medium" if safety_changes or added_deprecations or gap_changes else "low"
    )
    return ApiCompatibilityDiffReport(
        old_contract_path=str(old_path),
        new_contract_path=str(new_path),
        added_resource_families=added_resources,
        removed_resource_families=removed_resources,
        changed_safety_boundaries=safety_changes,
        added_cli_groups=sorted(new_cli - old_cli),
        removed_cli_groups=sorted(old_cli - new_cli),
        added_deprecations=added_deprecations,
        removed_deprecations=removed_deprecations,
        changed_known_gaps=gap_changes,
        changes=changes,
        risk_level=risk_level,
    )


def analyze_codebase_compatibility_with_contract(
    codebase_path: str | Path,
    contract_path: str | Path,
) -> CodebaseCompatibilityReport:
    """Compare detected local PyProcore usage with a local contract."""
    contract_source = _validate_local_json_path(contract_path)
    contract = load_compatibility_contract(contract_source)
    scan = scan_pyprocore_usage(codebase_path)
    families = {resource.name: resource for resource in contract.resources}
    deprecated = {item.helper: item for item in contract.deprecations}
    removed = {item.helper: item for item in contract.removed_helpers}
    buckets: dict[str, list[ApiCompatibilityValidationFinding]] = {
        "compatible": [],
        "deprecated": [],
        "removed": [],
        "unknown_manual_review": [],
        "local_only": [],
    }
    for usage in scan.usages:
        bucket, finding = _classify_usage(usage, families, deprecated, removed)
        buckets[bucket].append(finding)
    return CodebaseCompatibilityReport(
        scanned_path=scan.scanned_path,
        contract_path=str(contract_source),
        contract_version=contract.pyprocore_version,
        scan_report=scan,
        compatible=buckets["compatible"],
        deprecated=buckets["deprecated"],
        removed=buckets["removed"],
        unknown_manual_review=buckets["unknown_manual_review"],
        local_only=buckets["local_only"],
    )


def _classify_usage(
    usage: PyprocoreUsage,
    families: Mapping[str, ApiCompatibilityResource],
    deprecated: Mapping[str, ApiCompatibilityDeprecation],
    removed: Mapping[str, ApiCompatibilityDeprecation],
) -> tuple[str, ApiCompatibilityValidationFinding]:
    """Classify one redacted usage against contract metadata."""
    for helper, item in removed.items():
        if _symbol_matches(usage.symbol, helper):
            return "removed", _usage_finding(
                usage, "high", "removed_helper", "Removed helper requires migration.", item
            )
    for helper, item in deprecated.items():
        if _symbol_matches(usage.symbol, helper):
            return "deprecated", _usage_finding(
                usage,
                "warning",
                "deprecated_helper",
                "Deprecated helper requires migration review.",
                item,
            )
    resource = families.get(usage.capability_family)
    if resource is None:
        return "unknown_manual_review", _usage_finding(
            usage,
            "warning",
            "unknown_family",
            "Capability family is not declared by this contract; review manually.",
        )
    if resource.local_only:
        return "local_only", _usage_finding(
            usage,
            "info",
            "local_only_compatible",
            "Local-only capability is declared compatible by this contract.",
        )
    return "compatible", _usage_finding(
        usage,
        "info",
        "supported_family",
        "Read-only capability family is declared supported by this contract.",
    )


def _current_safety_boundaries() -> list[ApiCompatibilitySafetyBoundary]:
    """Return explicit current safety boundaries."""
    values = [
        ("mcp", "discovery_only", "MCP exposes discovery metadata only."),
        ("tool_execution", "disabled", "Agent and Procore tool execution is disabled."),
        (
            "procore_write_actions",
            "disabled",
            "Create, update, delete, upload, approval, submit, and payment actions are disabled.",
        ),
        ("external_ai_model_calls", "none", "No external AI/model call is made."),
        (
            "maintenance_remote_fetch",
            "none",
            "Maintenance workflows read only user-selected local files.",
        ),
        ("automatic_pull_requests", "disabled", "No pull request is opened automatically."),
        ("automatic_commits", "disabled", "No git command or commit is run automatically."),
        (
            "maintenance_human_review",
            "required",
            "Migration, patch, PR draft, and compatibility decisions require human review.",
        ),
    ]
    return [
        ApiCompatibilitySafetyBoundary(name=name, status=status, description=description)
        for name, status, description in values
    ]


def _deduplicate_resources(
    resources: list[ApiCompatibilityResource],
) -> list[ApiCompatibilityResource]:
    """Merge duplicate discovery families deterministically."""
    grouped: dict[str, ApiCompatibilityResource] = {}
    for resource in resources:
        existing = grouped.get(resource.name)
        if existing is None:
            grouped[resource.name] = resource
            continue
        names = {operation.name for operation in existing.operations}
        operations = [
            *existing.operations,
            *[operation for operation in resource.operations if operation.name not in names],
        ]
        grouped[resource.name] = existing.model_copy(
            update={"operations": sorted(operations, key=lambda row: row.name)}
        )
    return [grouped[name] for name in sorted(grouped)]


def _changed_boundaries(
    old: ApiCompatibilityContract,
    new: ApiCompatibilityContract,
) -> list[ApiCompatibilityChange]:
    """Return changed safety boundary rows."""
    old_values = {row.name: row.status for row in old.safety_boundaries}
    new_values = {row.name: row.status for row in new.safety_boundaries}
    return [
        ApiCompatibilityChange(
            change_type="changed_safety_boundary",
            subject=name,
            before=old_values.get(name),
            after=new_values.get(name),
            risk_level="high",
            migration_note="Stop and review any safety-boundary change manually.",
        )
        for name in sorted(old_values.keys() | new_values.keys())
        if old_values.get(name) != new_values.get(name)
    ]


def _changed_gaps(
    old: ApiCompatibilityContract,
    new: ApiCompatibilityContract,
) -> list[ApiCompatibilityChange]:
    """Return added, removed, or changed known-gap rows."""
    old_values = {row.family: f"{row.status}: {row.reason}" for row in old.known_gaps}
    new_values = {row.family: f"{row.status}: {row.reason}" for row in new.known_gaps}
    return [
        ApiCompatibilityChange(
            change_type="changed_known_gap",
            subject=name,
            before=old_values.get(name),
            after=new_values.get(name),
            risk_level="medium",
            migration_note="Review whether this known-gap change affects local usage.",
        )
        for name in sorted(old_values.keys() | new_values.keys())
        if old_values.get(name) != new_values.get(name)
    ]


def _usage_finding(
    usage: PyprocoreUsage,
    severity: str,
    code: str,
    message: str,
    deprecation: ApiCompatibilityDeprecation | None = None,
) -> ApiCompatibilityValidationFinding:
    """Build one codebase compatibility finding."""
    return ApiCompatibilityValidationFinding(
        severity=severity,
        code=code,
        message=message,
        file_path=usage.file_path,
        symbol=usage.symbol,
        family=usage.capability_family,
        migration_note=deprecation.migration_note if deprecation else None,
    )


def _symbol_matches(symbol: str, helper: str) -> bool:
    """Return whether a normalized usage symbol references one helper."""
    return symbol == helper or symbol.endswith(f".{helper}")


def _validation_finding(
    severity: str,
    code: str,
    message: str,
) -> ApiCompatibilityValidationFinding:
    """Build one contract validation finding."""
    return ApiCompatibilityValidationFinding(
        severity=severity,
        code=code,
        message=message,
    )


def _validate_local_json_path(path: str | Path) -> Path:
    """Validate a local JSON path and reject URL-like values."""
    value = str(path)
    if "://" in value:
        raise ValidationError("Compatibility contracts must be local JSON files.")
    source = Path(path).expanduser().resolve()
    if source.suffix.lower() != ".json":
        raise ValidationError("Compatibility contract path must use a .json suffix.")
    if not source.is_file():
        raise ValidationError(f"Compatibility contract does not exist: {source}")
    return source


def _load_json_mapping(path: Path) -> Mapping[str, Any]:
    """Load one JSON object from a validated local path."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"Could not read compatibility contract: {path}") from exc
    if not isinstance(payload, Mapping):
        raise ValidationError("Compatibility contract JSON must contain an object.")
    return payload
