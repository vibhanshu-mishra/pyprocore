"""AST and lexical detection of local PyProcore usage."""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable

from pyprocore.maintenance.models import (
    PyprocoreCallUsage,
    PyprocoreCliUsage,
    PyprocoreImportUsage,
    PyprocoreUsage,
)

CAPABILITY_FAMILIES = {
    "companies",
    "projects",
    "rfis",
    "submittals",
    "documents",
    "drawings",
    "specifications",
    "photos",
    "daily_logs",
    "observations",
    "punch_items",
    "correspondence",
    "meetings",
    "inspections",
    "incidents",
    "directory",
    "financials",
    "contracts",
    "project_management",
    "project_tools",
    "workflows",
    "async_client",
    "plugins",
    "catalog",
    "discovery",
    "integrations",
    "analytics",
    "templates",
    "maintenance",
}

MODULE_FAMILY_MAP = {
    "pyprocore.workflows": "workflows",
    "pyprocore.analytics": "analytics",
    "pyprocore.catalog": "catalog",
    "pyprocore.discovery": "discovery",
    "pyprocore.integrations": "integrations",
    "pyprocore.templates": "templates",
    "pyprocore.maintenance": "maintenance",
    "pyprocore.plugins": "plugins",
    "pyprocore.async_client": "async_client",
}

CLIENT_FAMILY_MAP = {
    "companies": "companies",
    "projects": "projects",
    "rfis": "rfis",
    "submittals": "submittals",
    "documents": "documents",
    "drawings": "drawings",
    "specifications": "specifications",
    "photos": "photos",
    "daily_logs": "daily_logs",
    "observations": "observations",
    "punch_items": "punch_items",
    "correspondence": "correspondence",
    "meetings": "meetings",
    "inspections": "inspections",
    "incidents": "incidents",
    "directory": "directory",
    "financials": "financials",
    "contracts": "contracts",
    "project_management": "project_management",
    "project_tools": "project_tools",
}

CLI_FAMILY_MAP = {
    **CLIENT_FAMILY_MAP,
    "project-tools": "project_tools",
    "workflow-plan": "workflows",
    "project-context": "workflows",
    "async-batch": "async_client",
    "plugins": "plugins",
    "catalog": "catalog",
    "discovery": "discovery",
    "integrations": "integrations",
    "analytics": "analytics",
    "templates": "templates",
    "maintenance": "maintenance",
}

HELPER_PREFIX_FAMILIES = {
    "build_project_context": "workflows",
    "build_enhanced_rfi": "workflows",
    "build_enhanced_submittal": "workflows",
    "build_ai_": "workflows",
    "run_workflow": "workflows",
    "run_rfi_aging": "analytics",
    "run_submittal_delay": "analytics",
    "run_change_exposure": "analytics",
    "run_daily_log": "analytics",
    "run_project_health": "analytics",
    "load_oas_catalog": "catalog",
    "compare_oas_catalogs": "maintenance",
    "scan_pyprocore_usage": "maintenance",
    "analyze_codebase_api_impact": "maintenance",
}

CLI_PATTERN = re.compile(r"\bprocore-sdk\s+([a-z0-9][a-z0-9-]*)", re.IGNORECASE)
PYPROCORE_REFERENCE_PATTERN = re.compile(r"\bpyprocore(?:\[[^\]]+\])?\b", re.IGNORECASE)
SECRET_PATTERNS = [
    re.compile(
        r"(?i)\b(access_token|refresh_token|client_secret|password|api[_-]?key|secret)"
        r"([\"']?\s*[=:]\s*)([\"']?)[^\s,\"'}]+"
    ),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"),
]


def detect_python_usages(
    text: str,
    file_path: str,
) -> tuple[
    list[PyprocoreImportUsage],
    list[PyprocoreCallUsage],
    list[PyprocoreUsage],
]:
    """Detect imports and calls from Python source without importing it."""
    try:
        tree = ast.parse(text, filename=file_path)
    except SyntaxError:
        return [], [], _detect_package_references(text, file_path, confidence="low")

    lines = text.splitlines()
    imports: list[PyprocoreImportUsage] = []
    calls: list[PyprocoreCallUsage] = []
    other: list[PyprocoreUsage] = []
    imported_families: dict[str, str] = {}
    client_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not alias.name.startswith("pyprocore"):
                    continue
                local_name = alias.asname or alias.name.split(".")[0]
                family = capability_family_for_module(alias.name)
                imported_families[local_name] = family
                imports.append(
                    _import_usage(
                        file_path,
                        lines,
                        node.lineno,
                        alias.name,
                        None,
                        family,
                    )
                )
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("pyprocore"):
            module = node.module or "pyprocore"
            module_family = capability_family_for_module(module)
            for alias in node.names:
                local_name = alias.asname or alias.name
                family = capability_family_for_symbol(alias.name, module_family)
                imported_families[local_name] = family
                imports.append(
                    _import_usage(
                        file_path,
                        lines,
                        node.lineno,
                        module,
                        alias.name,
                        family,
                    )
                )
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call_chain = _call_chain(node.value.func)
            if call_chain and call_chain.split(".")[-1] in {"Procore", "AsyncProcore"}:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        client_names.add(target.id)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        chain = _call_chain(node.func)
        if chain:
            parts = chain.split(".")
            terminal = parts[-1]
            if terminal in {"Procore", "AsyncProcore"}:
                family = "async_client" if terminal == "AsyncProcore" else "projects"
                calls.append(_call_usage(file_path, lines, node.lineno, chain, family))
                continue
            client_family = _family_from_client_chain(parts, client_names)
            if client_family:
                calls.append(_call_usage(file_path, lines, node.lineno, chain, client_family))
                continue
            imported_family = imported_families.get(parts[0])
            if imported_family:
                calls.append(_call_usage(file_path, lines, node.lineno, chain, imported_family))
                continue
            helper_family = capability_family_for_symbol(terminal, "unknown")
            if helper_family != "unknown":
                calls.append(_call_usage(file_path, lines, node.lineno, chain, helper_family))
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in client_names
        ):
            dynamic_family = _dynamic_family_hint(node)
            other.append(
                PyprocoreUsage(
                    usage_type="dynamic_usage",
                    file_path=file_path,
                    line_number=node.lineno,
                    symbol="getattr",
                    capability_family=dynamic_family,
                    snippet=_line_snippet(lines, node.lineno),
                    confidence="medium" if dynamic_family != "unknown" else "low",
                    dynamic=True,
                )
            )
    return imports, _deduplicate(calls), _deduplicate(other)


def detect_text_usages(
    text: str,
    file_path: str,
) -> tuple[list[PyprocoreCliUsage], list[PyprocoreUsage]]:
    """Detect CLI commands and package references in local text."""
    cli_usages: list[PyprocoreCliUsage] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in CLI_PATTERN.finditer(line):
            command = match.group(1).lower()
            cli_usages.append(
                PyprocoreCliUsage(
                    usage_type="cli",
                    file_path=file_path,
                    line_number=line_number,
                    symbol=f"procore-sdk {command}",
                    command=command,
                    capability_family=CLI_FAMILY_MAP.get(command, "unknown"),
                    snippet=redact_snippet(line),
                )
            )
    references = _detect_package_references(text, file_path)
    return _deduplicate(cli_usages), _deduplicate(references)


def capability_family_for_module(module: str) -> str:
    """Map a PyProcore module path to a broad capability family."""
    for prefix, family in MODULE_FAMILY_MAP.items():
        if module == prefix or module.startswith(f"{prefix}."):
            return family
    if module.startswith("pyprocore.services."):
        candidate = module.rsplit(".", maxsplit=1)[-1]
        return CLIENT_FAMILY_MAP.get(candidate, "unknown")
    return "unknown"


def capability_family_for_symbol(symbol: str, fallback: str = "unknown") -> str:
    """Map a helper symbol to a broad capability family."""
    normalized = symbol.lower()
    for prefix, family in HELPER_PREFIX_FAMILIES.items():
        if normalized.startswith(prefix):
            return family
    return fallback


def redact_snippet(value: str, *, max_length: int = 240) -> str:
    """Redact common secret-looking values from a bounded report snippet."""
    redacted = value
    for pattern in SECRET_PATTERNS:
        if "bearer" in pattern.pattern.lower():
            redacted = pattern.sub("Bearer [REDACTED]", redacted)
        else:
            redacted = pattern.sub(
                lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]",
                redacted,
            )
    return redacted.strip()[:max_length]


def _family_from_client_chain(parts: list[str], client_names: set[str]) -> str | None:
    """Return an object-client family from an attribute call chain."""
    if len(parts) < 3 or parts[0] not in client_names:
        return None
    return CLIENT_FAMILY_MAP.get(parts[1])


def _call_chain(node: ast.expr) -> str | None:
    """Return a dotted name for a static AST call target."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_chain(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _dynamic_family_hint(node: ast.Call) -> str:
    """Return a conservative family hint for ``getattr(client, "service")``."""
    if len(node.args) < 2:
        return "unknown"
    service_name = node.args[1]
    if not isinstance(service_name, ast.Constant) or not isinstance(service_name.value, str):
        return "unknown"
    return CLIENT_FAMILY_MAP.get(service_name.value, "unknown")


def _import_usage(
    file_path: str,
    lines: list[str],
    line_number: int,
    module: str,
    imported_name: str | None,
    family: str,
) -> PyprocoreImportUsage:
    """Build a normalized import usage."""
    symbol = f"{module}.{imported_name}" if imported_name else module
    return PyprocoreImportUsage(
        usage_type="import",
        file_path=file_path,
        line_number=line_number,
        symbol=symbol,
        module=module,
        imported_name=imported_name,
        capability_family=family,
        snippet=_line_snippet(lines, line_number),
    )


def _call_usage(
    file_path: str,
    lines: list[str],
    line_number: int,
    chain: str,
    family: str,
) -> PyprocoreCallUsage:
    """Build a normalized static-call usage."""
    return PyprocoreCallUsage(
        usage_type="call",
        file_path=file_path,
        line_number=line_number,
        symbol=chain,
        call_chain=chain,
        capability_family=family,
        snippet=_line_snippet(lines, line_number),
    )


def _line_snippet(lines: list[str], line_number: int) -> str | None:
    """Return one redacted source line."""
    if line_number < 1 or line_number > len(lines):
        return None
    return redact_snippet(lines[line_number - 1])


def _detect_package_references(
    text: str,
    file_path: str,
    *,
    confidence: str = "medium",
) -> list[PyprocoreUsage]:
    """Detect bounded package references not represented by richer usage rows."""
    usages: list[PyprocoreUsage] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not PYPROCORE_REFERENCE_PATTERN.search(line):
            continue
        usages.append(
            PyprocoreUsage(
                usage_type="package_reference",
                file_path=file_path,
                line_number=line_number,
                symbol="pyprocore",
                capability_family="unknown",
                snippet=redact_snippet(line),
                confidence=confidence,
            )
        )
    return usages


def _deduplicate[T: PyprocoreUsage](usages: Iterable[T]) -> list[T]:
    """Deduplicate usage rows while preserving discovery order."""
    seen: set[tuple[str, int | None, str, str]] = set()
    unique: list[T] = []
    for usage in usages:
        key = (
            usage.file_path,
            usage.line_number,
            usage.usage_type,
            usage.symbol,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(usage)
    return unique
