"""Local metadata-only trust policy support for PyProcore plugins.

Phase 16B trust checks validate JSON metadata only. They do not install plugin
packages, import plugin modules, fetch remote registries, execute plugin code,
call Procore, or enable MCP/tool execution.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Literal

from pydantic import Field
from pydantic import ValidationError as PydanticValidationError

from pyprocore.core.exceptions import ValidationError
from pyprocore.models.base import ProcoreModel
from pyprocore.plugins.config import (
    PluginConfig,
    load_plugin_config_from_dict,
    validate_plugin_config,
)
from pyprocore.plugins.extension_pack import (
    PluginExtensionPack,
    load_extension_pack_manifest_from_dict,
    validate_extension_pack_manifest,
)
from pyprocore.plugins.hooks import redact_sensitive_text
from pyprocore.plugins.models import PluginCapability, PluginManifest, PluginSafetyLevel
from pyprocore.plugins.validation import (
    SAFE_PLUGIN_NAME_PATTERN,
    SAFE_VERSION_PATTERN,
    load_plugin_manifest_from_dict,
    validate_plugin_manifest,
)

PLUGIN_TRUST_POLICY_SCHEMA_VERSION = "1"
SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")
SIGNATURE_PATTERN = re.compile(r"^[A-Za-z0-9+/=_:.\-]{16,4096}$")
SAFE_PUBLISHER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._@-]{1,120}$")
REPORT_TARGETS = Literal["manifest", "extension_pack", "config"]


def _pyprocore_version() -> str:
    """Return the installed PyProcore version without importing the package root."""
    try:
        return version("pyprocore")
    except PackageNotFoundError:
        return "2.3.0"


class PluginTrustPolicy(ProcoreModel):
    """JSON-only local trust policy for plugin metadata.

    Attributes:
        schema_version: Trust policy schema version.
        allowed_publishers: Publisher identifiers allowed by local policy.
        allowed_plugin_names: Plugin or extension-pack names allowed by policy.
        allowed_capabilities: Capability categories allowed by policy.
        allowed_safety_levels: Safety levels allowed by policy.
        deny_remote_install: Must remain true; remote installation is unsupported.
        deny_execution: Must remain true; manifest/config execution is unsupported.
        deny_arbitrary_import: Must remain true; arbitrary imports are unsupported.
        require_trusted_publisher: Require a publisher or author to match policy.
        require_checksum_or_signature: Require checksum/signature metadata to be present.
        allow_unsigned: Permit manifests without signature metadata.
        min_pyprocore_version: Minimum local PyProcore version policy note.
        max_pyprocore_version: Maximum local PyProcore version policy note.
        notes: Human-readable local policy notes.
    """

    schema_version: str = PLUGIN_TRUST_POLICY_SCHEMA_VERSION
    allowed_publishers: list[str] = Field(default_factory=list)
    allowed_plugin_names: list[str] = Field(default_factory=list)
    allowed_capabilities: list[PluginCapability] = Field(default_factory=list)
    allowed_safety_levels: list[PluginSafetyLevel] = Field(
        default_factory=lambda: [PluginSafetyLevel.METADATA_ONLY]
    )
    deny_remote_install: bool = True
    deny_execution: bool = True
    deny_arbitrary_import: bool = True
    require_trusted_publisher: bool = True
    require_checksum_or_signature: bool = False
    allow_unsigned: bool = True
    min_pyprocore_version: str | None = ">=2.3.0"
    max_pyprocore_version: str | None = None
    notes: list[str] = Field(default_factory=list)


class PluginTrustFinding(ProcoreModel):
    """One trust policy validation finding."""

    severity: str
    code: str
    message: str
    field: str | None = None


class PluginTrustReport(ProcoreModel):
    """Local JSON-serializable compatibility and trust report."""

    target_type: str
    target_name: str
    trusted: bool
    valid: bool
    pyprocore_version: str = Field(default_factory=_pyprocore_version)
    finding_count: int
    findings: list[PluginTrustFinding] = Field(default_factory=list)
    policy: PluginTrustPolicy
    mode: str = "metadata_only_no_execution"


def load_trust_policy_from_dict(data: Mapping[str, Any]) -> PluginTrustPolicy:
    """Load a trust policy from local JSON-compatible dictionary data.

    Args:
        data: Parsed local JSON object.

    Returns:
        Parsed trust policy model.

    Raises:
        ValidationError: If the policy cannot be parsed.
    """
    try:
        return PluginTrustPolicy.model_validate(dict(data))
    except PydanticValidationError as exc:
        raise ValidationError(redact_sensitive_text(str(exc))) from exc


def load_trust_policy_from_file(path: Path | str) -> PluginTrustPolicy:
    """Load a JSON-only local trust policy file."""
    return load_trust_policy_from_dict(_read_local_json_file(path, label="trust policy"))


def export_trust_policy_template() -> PluginTrustPolicy:
    """Return a conservative sample trust policy."""
    return PluginTrustPolicy(
        allowed_publishers=["PyProcore", "Your Organization"],
        allowed_plugin_names=[
            "csv_exporter_plugin",
            "jsonl_exporter_plugin",
            "starter_export_pack",
        ],
        allowed_capabilities=[
            PluginCapability.EXPORTER,
            PluginCapability.FORMATTER,
            PluginCapability.VALIDATOR,
            PluginCapability.REPORT,
            PluginCapability.AGENT_METADATA,
            PluginCapability.MCP_METADATA,
        ],
        notes=[
            "Local metadata validation only.",
            "Remote install, execution, and arbitrary imports are denied by default.",
        ],
    )


def validate_manifest_trust(
    manifest: PluginManifest,
    policy: PluginTrustPolicy,
) -> PluginTrustReport:
    """Validate a plugin manifest against local trust policy metadata."""
    findings = _policy_findings(policy)
    validation = validate_plugin_manifest(manifest)
    findings.extend(
        PluginTrustFinding(severity="error", code="manifest_invalid", message=error)
        for error in validation.errors
    )
    findings.extend(
        PluginTrustFinding(severity="warning", code="manifest_warning", message=warning)
        for warning in validation.warnings
    )
    findings.extend(_manifest_findings(manifest, policy))
    return _build_report("manifest", manifest.name, policy, findings)


def validate_extension_pack_trust(
    extension_pack: PluginExtensionPack,
    policy: PluginTrustPolicy,
) -> PluginTrustReport:
    """Validate an extension-pack manifest against local trust policy metadata."""
    findings = _policy_findings(policy)
    validation = validate_extension_pack_manifest(extension_pack)
    findings.extend(
        PluginTrustFinding(severity="error", code="extension_pack_invalid", message=error)
        for error in validation.errors
    )
    findings.extend(
        PluginTrustFinding(severity="warning", code="extension_pack_warning", message=warning)
        for warning in validation.warnings
    )
    findings.extend(_extension_pack_findings(extension_pack, policy))
    return _build_report("extension_pack", extension_pack.name, policy, findings)


def validate_config_trust(config: PluginConfig, policy: PluginTrustPolicy) -> PluginTrustReport:
    """Validate plugin config preferences against local trust policy metadata."""
    findings = _policy_findings(policy)
    validation = validate_plugin_config(config)
    findings.extend(
        PluginTrustFinding(severity="error", code="config_invalid", message=error)
        for error in validation.errors
    )
    findings.extend(
        PluginTrustFinding(severity="warning", code="config_warning", message=warning)
        for warning in validation.warnings
    )
    findings.extend(_config_findings(config, policy))
    return _build_report("config", "plugin_config", policy, findings)


def build_trust_report_for_path(
    path: Path | str,
    policy: PluginTrustPolicy,
) -> PluginTrustReport:
    """Build a trust report for one local JSON manifest/config/extension pack path."""
    data = _read_local_json_file(path, label="plugin trust target")
    target_type = _detect_target_type(data)
    if target_type == "extension_pack":
        return validate_extension_pack_trust(load_extension_pack_manifest_from_dict(data), policy)
    if target_type == "config":
        return validate_config_trust(load_plugin_config_from_dict(data), policy)
    return validate_manifest_trust(load_plugin_manifest_from_dict(data), policy)


def render_trust_report_markdown(report: PluginTrustReport) -> str:
    """Render a trust report as Markdown."""
    lines = [
        "# PyProcore Plugin Trust Report",
        "",
        f"- Target: `{report.target_name}`",
        f"- Type: `{report.target_type}`",
        f"- Trusted: `{report.trusted}`",
        f"- Valid: `{report.valid}`",
        f"- Mode: `{report.mode}`",
        "",
        "This report is metadata-only. It does not install plugins, import plugin modules, "
        "fetch remote registries, execute plugin code, call Procore, or enable MCP/tool execution.",
        "",
        "## Findings",
    ]
    if not report.findings:
        lines.append("- No findings.")
    else:
        lines.extend(
            f"- **{finding.severity.upper()}** `{finding.code}`: {finding.message}"
            for finding in report.findings
        )
    return "\n".join(lines) + "\n"


def trust_report_to_json(report: PluginTrustReport, *, pretty: bool = True) -> str:
    """Serialize a trust report to JSON."""
    return json.dumps(report.model_dump(mode="json"), indent=2 if pretty else None)


def _read_local_json_file(path: Path | str, *, label: str) -> dict[str, Any]:
    """Read one local JSON object without allowing remote URLs or traversal."""
    target = Path(path)
    path_text = str(path)
    if "://" in path_text:
        raise ValidationError(f"Remote {label} URLs are not supported.")
    if any(part == ".." for part in target.parts):
        raise ValidationError(f"{label.title()} paths must not contain path traversal.")
    if target.suffix.casefold() != ".json":
        raise ValidationError(f"{label.title()} files must use JSON with a .json suffix.")
    try:
        parsed = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{label.title()} JSON is invalid: {exc.msg}.") from exc
    if not isinstance(parsed, dict):
        raise ValidationError(f"{label.title()} JSON must contain an object at the top level.")
    return parsed


def _detect_target_type(data: Mapping[str, Any]) -> REPORT_TARGETS:
    """Detect which local plugin metadata object a JSON document describes."""
    if "included_plugins" in data or "included_hooks" in data:
        return "extension_pack"
    if "enabled_plugins" in data or "config_version" in data:
        return "config"
    return "manifest"


def _policy_findings(policy: PluginTrustPolicy) -> list[PluginTrustFinding]:
    """Return findings for risky policy settings."""
    findings: list[PluginTrustFinding] = []
    if policy.schema_version != PLUGIN_TRUST_POLICY_SCHEMA_VERSION:
        findings.append(
            _error(
                "policy_schema_version",
                "Unsupported trust policy schema version.",
                field="schema_version",
            )
        )
    if not policy.deny_remote_install:
        findings.append(_error("remote_install_allowed", "Trust policy must deny remote install."))
    if not policy.deny_execution:
        findings.append(_error("execution_allowed", "Trust policy must deny plugin execution."))
    if not policy.deny_arbitrary_import:
        findings.append(
            _error("arbitrary_import_allowed", "Trust policy must deny arbitrary imports.")
        )
    for name in policy.allowed_plugin_names:
        if not SAFE_PLUGIN_NAME_PATTERN.fullmatch(name):
            findings.append(_error("unsafe_policy_plugin_name", f"Unsafe plugin name {name!r}."))
    for publisher in policy.allowed_publishers:
        if not SAFE_PUBLISHER_PATTERN.fullmatch(publisher):
            findings.append(_error("unsafe_policy_publisher", "Unsafe publisher identifier."))
    return findings


def _manifest_findings(
    manifest: PluginManifest,
    policy: PluginTrustPolicy,
) -> list[PluginTrustFinding]:
    """Return manifest trust findings."""
    findings = _common_metadata_findings(
        name=manifest.name,
        publisher=manifest.publisher or manifest.author,
        capabilities=manifest.capabilities,
        safety_level=manifest.safety_level,
        policy=policy,
    )
    findings.extend(
        _version_metadata_findings(
            min_version=manifest.min_pyprocore_version,
            max_version=manifest.max_pyprocore_version,
            requires_pyprocore=manifest.requires_pyprocore,
        )
    )
    findings.extend(_signature_checksum_findings(manifest, policy))
    if manifest.entry_points and policy.deny_arbitrary_import:
        findings.append(
            _warning(
                "entry_points_metadata_only",
                "Manifest contains entry-point metadata; trust policy still denies "
                "arbitrary imports.",
                field="entry_points",
            )
        )
    if manifest.enabled_by_default:
        findings.append(
            _warning(
                "enabled_by_default_ignored",
                "enabled_by_default is metadata only and does not enable execution.",
            )
        )
    if manifest.allowed_capability_categories:
        declared = set(manifest.allowed_capability_categories)
        actual = set(manifest.capabilities)
        if not actual.issubset(declared):
            findings.append(
                _error(
                    "capability_boundary_mismatch",
                    "Manifest capabilities exceed allowed_capability_categories.",
                )
            )
    if not manifest.safety_boundaries:
        findings.append(
            _warning(
                "missing_safety_boundaries",
                "Manifest does not declare safety boundary notes.",
                field="safety_boundaries",
            )
        )
    return findings


def _extension_pack_findings(
    extension_pack: PluginExtensionPack,
    policy: PluginTrustPolicy,
) -> list[PluginTrustFinding]:
    """Return extension-pack trust findings."""
    findings = _common_metadata_findings(
        name=extension_pack.name,
        publisher=getattr(extension_pack, "publisher", None) or extension_pack.author,
        capabilities=extension_pack.capabilities,
        safety_level=extension_pack.safety_level,
        policy=policy,
    )
    findings.extend(
        _version_metadata_findings(
            min_version=getattr(extension_pack, "min_pyprocore_version", None),
            max_version=getattr(extension_pack, "max_pyprocore_version", None),
            requires_pyprocore=extension_pack.requires_pyprocore,
        )
    )
    for item in extension_pack.included_plugins:
        if policy.allowed_plugin_names and item.plugin_name not in policy.allowed_plugin_names:
            findings.append(
                _error(
                    "included_plugin_not_allowed",
                    f"Included plugin {item.plugin_name!r} is not allowed by policy.",
                )
            )
    return findings


def _config_findings(config: PluginConfig, policy: PluginTrustPolicy) -> list[PluginTrustFinding]:
    """Return config trust findings."""
    findings: list[PluginTrustFinding] = []
    for name in config.enabled_plugins + config.disabled_plugins + config.extension_packs:
        if policy.allowed_plugin_names and name not in policy.allowed_plugin_names:
            findings.append(
                _error("config_plugin_not_allowed", f"Plugin/config name {name!r} is not allowed.")
            )
    for capability in config.enabled_capabilities:
        if policy.allowed_capabilities and capability not in policy.allowed_capabilities:
            findings.append(
                _error(
                    "config_capability_not_allowed",
                    f"Capability {capability.value!r} is not allowed by policy.",
                )
            )
    return findings


def _common_metadata_findings(
    *,
    name: str,
    publisher: str | None,
    capabilities: list[PluginCapability],
    safety_level: PluginSafetyLevel,
    policy: PluginTrustPolicy,
) -> list[PluginTrustFinding]:
    """Return common trust findings for plugin-like metadata."""
    findings: list[PluginTrustFinding] = []
    if policy.allowed_plugin_names and name not in policy.allowed_plugin_names:
        findings.append(_error("plugin_not_allowed", f"Plugin name {name!r} is not allowed."))
    if policy.require_trusted_publisher and not publisher:
        findings.append(_error("publisher_required", "A trusted publisher or author is required."))
    if publisher and policy.allowed_publishers and publisher not in policy.allowed_publishers:
        findings.append(_error("publisher_not_allowed", f"Publisher {publisher!r} is not allowed."))
    if policy.allowed_capabilities:
        disallowed = [
            item.value for item in capabilities if item not in policy.allowed_capabilities
        ]
        if disallowed:
            findings.append(
                _error(
                    "capability_not_allowed",
                    "Disallowed capabilities: " + ", ".join(sorted(disallowed)),
                )
            )
    if safety_level not in policy.allowed_safety_levels:
        findings.append(
            _error(
                "safety_level_not_allowed", f"Safety level {safety_level.value!r} is not allowed."
            )
        )
    return findings


def _version_metadata_findings(
    *,
    min_version: str | None,
    max_version: str | None,
    requires_pyprocore: str | None,
) -> list[PluginTrustFinding]:
    """Return syntactic compatibility metadata findings."""
    findings: list[PluginTrustFinding] = []
    for field, value in (
        ("min_pyprocore_version", min_version),
        ("max_pyprocore_version", max_version),
    ):
        if value and not SAFE_VERSION_PATTERN.fullmatch(value):
            findings.append(
                _error("invalid_version_metadata", f"{field} must be semantic.", field=field)
            )
    if requires_pyprocore and not requires_pyprocore.startswith((">=", "==", "~=", "<=")):
        findings.append(
            _warning(
                "requires_pyprocore_unparsed",
                "requires_pyprocore is recorded as metadata and was not fully parsed.",
                field="requires_pyprocore",
            )
        )
    return findings


def _signature_checksum_findings(
    manifest: PluginManifest,
    policy: PluginTrustPolicy,
) -> list[PluginTrustFinding]:
    """Return syntactic signature/checksum findings without cryptographic verification."""
    findings: list[PluginTrustFinding] = []
    if policy.require_checksum_or_signature and not (
        manifest.signature or manifest.checksum_sha256
    ):
        findings.append(
            _error("signature_or_checksum_required", "Signature or checksum metadata is required.")
        )
    if not policy.allow_unsigned and not manifest.signature:
        findings.append(
            _error("signature_required", "Unsigned manifests are not allowed by policy.")
        )
    if manifest.signature and not SIGNATURE_PATTERN.fullmatch(manifest.signature):
        findings.append(
            _error(
                "invalid_signature_metadata",
                "Signature metadata has invalid syntax.",
                field="signature",
            )
        )
    if manifest.checksum_sha256 and not SHA256_PATTERN.fullmatch(manifest.checksum_sha256):
        findings.append(
            _error(
                "invalid_checksum_metadata",
                "checksum_sha256 must be 64 hexadecimal characters.",
                field="checksum_sha256",
            )
        )
    if manifest.signature:
        findings.append(
            _warning(
                "signature_not_cryptographically_verified",
                "Signature metadata is syntactically checked only; no cryptographic "
                "verification was performed.",
            )
        )
    if manifest.checksum_sha256:
        findings.append(
            _warning(
                "checksum_not_verified_against_artifact",
                "Checksum metadata is syntactically checked only; no remote artifact was fetched.",
            )
        )
    return findings


def _build_report(
    target_type: str,
    target_name: str,
    policy: PluginTrustPolicy,
    findings: list[PluginTrustFinding],
) -> PluginTrustReport:
    """Build a trust report from findings."""
    has_errors = any(finding.severity == "error" for finding in findings)
    return PluginTrustReport(
        target_type=target_type,
        target_name=target_name,
        trusted=not has_errors,
        valid=not has_errors,
        finding_count=len(findings),
        findings=findings,
        policy=policy,
    )


def _error(code: str, message: str, *, field: str | None = None) -> PluginTrustFinding:
    """Return an error finding."""
    return PluginTrustFinding(severity="error", code=code, message=message, field=field)


def _warning(code: str, message: str, *, field: str | None = None) -> PluginTrustFinding:
    """Return a warning finding."""
    return PluginTrustFinding(severity="warning", code=code, message=message, field=field)
