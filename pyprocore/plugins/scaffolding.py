"""Safe local plugin scaffold planning and writing helpers.

Phase 11D scaffolding writes local JSON, Markdown, and static text templates
only. It does not install plugins, fetch remote resources, load modules, execute
generated files, register hook callables, or call Procore.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import Field

from pyprocore.core.exceptions import ValidationError
from pyprocore.models.base import ProcoreModel
from pyprocore.plugins.hooks import redact_sensitive_text
from pyprocore.plugins.templates import PluginTemplateKind, render_template
from pyprocore.plugins.validation import SAFE_PLUGIN_NAME_PATTERN

SCAFFOLD_SCHEMA_VERSION = "1"
SAFE_SCAFFOLD_KINDS = {
    PluginTemplateKind.PLUGIN_MANIFEST: (
        ("plugin_manifest.json", PluginTemplateKind.PLUGIN_MANIFEST),
    ),
    PluginTemplateKind.PLUGIN_CONFIG: (("plugin_config.json", PluginTemplateKind.PLUGIN_CONFIG),),
    PluginTemplateKind.EXTENSION_PACK: (
        ("extension_pack_manifest.json", PluginTemplateKind.EXTENSION_PACK),
    ),
    PluginTemplateKind.HOOK_MANIFEST: (("hook_manifest.json", PluginTemplateKind.HOOK_MANIFEST),),
    PluginTemplateKind.README: (("README.md", PluginTemplateKind.README),),
    PluginTemplateKind.TESTS: (("tests/test_plugin_manifest.py", PluginTemplateKind.TESTS),),
    PluginTemplateKind.DOCS: (("docs/plugin-pack.md", PluginTemplateKind.DOCS),),
    PluginTemplateKind.FULL_PACK: (
        ("README.md", PluginTemplateKind.README),
        ("CHANGELOG.md", PluginTemplateKind.CHANGELOG),
        ("plugin_manifest.json", PluginTemplateKind.PLUGIN_MANIFEST),
        ("plugin_config.json", PluginTemplateKind.PLUGIN_CONFIG),
        ("extension_pack_manifest.json", PluginTemplateKind.EXTENSION_PACK),
        ("hook_manifest.json", PluginTemplateKind.HOOK_MANIFEST),
        ("docs/plugin-pack.md", PluginTemplateKind.DOCS),
        ("examples/plugin_usage.py", PluginTemplateKind.EXAMPLE),
        ("tests/test_plugin_manifest.py", PluginTemplateKind.TESTS),
    ),
}
UNSAFE_TEXT_FRAGMENTS = (
    "access_token",
    "refresh_token",
    "client_secret",
    "authorization:",
    "bearer ",
    "password",
    "secret=",
    "token=",
    "://",
    "__import__",
    "import" + "lib",
    "sub" + "process",
    "e" + "val(",
    "ex" + "ec(",
    " ".join(("pip", "install")),
    "python -m pip",
    "curl ",
    "wget ",
)
UNSAFE_ACTION_WORDS = (
    "create" + "_procore",
    "update" + "_procore",
    "delete" + "_procore",
    "upload" + "_procore",
    "approve" + "_procore",
    "reject" + "_procore",
    "submit" + "_procore",
    "payment" + "_procore",
)


class PluginScaffoldFinding(ProcoreModel):
    """One scaffold validation or write finding."""

    severity: str
    message: str
    path: str | None = None


class PluginScaffoldFile(ProcoreModel):
    """One file in a local scaffold plan or result."""

    path: str
    template_kind: PluginTemplateKind
    content: str
    exists: bool = False
    status: str = "planned"


class PluginScaffoldRequest(ProcoreModel):
    """Request to plan or create a local plugin scaffold."""

    name: str
    output_dir: Path
    kind: PluginTemplateKind = PluginTemplateKind.FULL_PACK
    description: str | None = None
    overwrite: bool = False
    dry_run: bool = True


class PluginScaffoldPlan(ProcoreModel):
    """Dry-run scaffold plan containing rendered file metadata."""

    schema_version: str = SCAFFOLD_SCHEMA_VERSION
    request: PluginScaffoldRequest
    files: list[PluginScaffoldFile] = Field(default_factory=list)
    findings: list[PluginScaffoldFinding] = Field(default_factory=list)
    mode: str = "template_planning_only"


class PluginScaffoldResult(ProcoreModel):
    """Result from creating or dry-running a local plugin scaffold."""

    schema_version: str = SCAFFOLD_SCHEMA_VERSION
    name: str
    output_dir: str
    dry_run: bool
    overwrite: bool
    files: list[PluginScaffoldFile] = Field(default_factory=list)
    findings: list[PluginScaffoldFinding] = Field(default_factory=list)
    written_count: int = 0
    skipped_count: int = 0
    planned_count: int = 0
    mode: str = "local_templates_only"


def validate_plugin_scaffold_request(
    request: PluginScaffoldRequest,
) -> list[PluginScaffoldFinding]:
    """Validate scaffold request metadata without touching the network."""
    findings: list[PluginScaffoldFinding] = []
    if not SAFE_PLUGIN_NAME_PATTERN.fullmatch(request.name):
        findings.append(
            PluginScaffoldFinding(
                severity="error",
                message="Scaffold name must be a safe lowercase plugin metadata identifier.",
            )
        )
    _validate_output_dir(request.output_dir, findings)
    if request.kind not in SAFE_SCAFFOLD_KINDS:
        findings.append(
            PluginScaffoldFinding(
                severity="error",
                message=f"Unsupported scaffold kind: {request.kind.value}.",
            )
        )
    if request.description:
        _scan_text(request.description, findings, path="description")
    return findings


def build_plugin_scaffold_plan(
    request: PluginScaffoldRequest,
) -> PluginScaffoldPlan:
    """Build a scaffold plan without writing files."""
    findings = validate_plugin_scaffold_request(request)
    files: list[PluginScaffoldFile] = []
    if any(finding.severity == "error" for finding in findings):
        return PluginScaffoldPlan(request=request, findings=findings)

    output_root = request.output_dir
    for relative_name, template_kind in _template_entries(request.kind):
        safe_relative = _safe_relative_path(relative_name)
        target = output_root / safe_relative
        content = render_template(
            template_kind,
            request.name,
            description=request.description,
        )
        _scan_text(content, findings, path=str(safe_relative))
        files.append(
            PluginScaffoldFile(
                path=str(target),
                template_kind=template_kind,
                content=content,
                exists=target.exists(),
                status="planned",
            )
        )
    return PluginScaffoldPlan(request=request, files=files, findings=findings)


def scaffold_plugin_pack(
    name: str,
    output_dir: Path | str,
    *,
    kind: PluginTemplateKind | str = PluginTemplateKind.FULL_PACK,
    description: str | None = None,
    overwrite: bool = False,
    dry_run: bool = True,
) -> PluginScaffoldResult:
    """Plan or create a local plugin scaffold.

    Args:
        name: Safe lowercase plugin metadata identifier.
        output_dir: Root directory selected by the developer.
        kind: Scaffold kind to render.
        description: Optional description for generated metadata.
        overwrite: Whether existing files may be replaced.
        dry_run: When true, return a plan without writing files.

    Returns:
        JSON-serializable scaffold result metadata.
    """
    request = PluginScaffoldRequest(
        name=name,
        output_dir=Path(output_dir),
        kind=PluginTemplateKind(kind),
        description=description,
        overwrite=overwrite,
        dry_run=dry_run,
    )
    plan = build_plugin_scaffold_plan(request)
    return write_scaffold_plan(plan) if not dry_run else _result_from_plan(plan)


def scaffold_extension_pack(
    name: str,
    output_dir: Path | str,
    *,
    overwrite: bool = False,
    dry_run: bool = True,
) -> PluginScaffoldResult:
    """Plan or create an extension-pack manifest scaffold."""
    return scaffold_plugin_pack(
        name,
        output_dir,
        kind=PluginTemplateKind.EXTENSION_PACK,
        overwrite=overwrite,
        dry_run=dry_run,
    )


def scaffold_plugin_config(
    name: str,
    output_dir: Path | str,
    *,
    overwrite: bool = False,
    dry_run: bool = True,
) -> PluginScaffoldResult:
    """Plan or create a plugin config scaffold."""
    return scaffold_plugin_pack(
        name,
        output_dir,
        kind=PluginTemplateKind.PLUGIN_CONFIG,
        overwrite=overwrite,
        dry_run=dry_run,
    )


def scaffold_hook_pack(
    name: str,
    output_dir: Path | str,
    *,
    overwrite: bool = False,
    dry_run: bool = True,
) -> PluginScaffoldResult:
    """Plan or create a hook-manifest scaffold."""
    return scaffold_plugin_pack(
        name,
        output_dir,
        kind=PluginTemplateKind.HOOK_MANIFEST,
        overwrite=overwrite,
        dry_run=dry_run,
    )


def write_scaffold_plan(plan: PluginScaffoldPlan) -> PluginScaffoldResult:
    """Write a scaffold plan to disk after validating output paths."""
    result = _result_from_plan(plan)
    if any(finding.severity == "error" for finding in result.findings):
        return result

    output_root = plan.request.output_dir.resolve()
    for file in result.files:
        target = Path(file.path)
        if not _is_relative_to(target.resolve(), output_root):
            file.status = "error"
            result.findings.append(
                PluginScaffoldFinding(
                    severity="error",
                    message="Scaffold target escaped the selected output directory.",
                    path=str(target),
                )
            )
            continue
        if target.exists() and not plan.request.overwrite:
            file.exists = True
            file.status = "skipped"
            result.skipped_count += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(file.content, encoding="utf-8")
        file.status = "written"
        file.exists = True
        result.written_count += 1
    result.planned_count = len(result.files)
    return result


def render_extension_pack_template(name: str) -> str:
    """Render an extension-pack scaffold template."""
    return render_template(PluginTemplateKind.EXTENSION_PACK, name)


def render_plugin_config_template(name: str) -> str:
    """Render a plugin config scaffold template."""
    return render_template(PluginTemplateKind.PLUGIN_CONFIG, name)


def render_hook_manifest_template(name: str) -> str:
    """Render a hook manifest scaffold template."""
    return render_template(PluginTemplateKind.HOOK_MANIFEST, name)


def export_plugin_scaffold_sample_plan() -> PluginScaffoldPlan:
    """Return a safe sample scaffold plan without writing files."""
    request = PluginScaffoldRequest(
        name="example_local_plugin",
        output_dir=Path("./plugin-scaffold-example"),
        kind=PluginTemplateKind.FULL_PACK,
        description="Metadata-only local plugin scaffold sample.",
        dry_run=True,
    )
    return build_plugin_scaffold_plan(request)


def _result_from_plan(plan: PluginScaffoldPlan) -> PluginScaffoldResult:
    """Convert a plan to a result object."""
    return PluginScaffoldResult(
        name=plan.request.name,
        output_dir=str(plan.request.output_dir),
        dry_run=plan.request.dry_run,
        overwrite=plan.request.overwrite,
        files=[file.model_copy() for file in plan.files],
        findings=list(plan.findings),
        planned_count=len(plan.files),
    )


def _template_entries(
    kind: PluginTemplateKind,
) -> Iterable[tuple[str, PluginTemplateKind]]:
    """Return file/template pairs for a scaffold kind."""
    return SAFE_SCAFFOLD_KINDS[kind]


def _safe_relative_path(value: str) -> Path:
    """Return a relative template path or raise for unsafe values."""
    path = Path(value)
    if path.is_absolute() or any(part == ".." for part in path.parts):
        raise ValidationError("Scaffold template file paths must stay relative.")
    return path


def _validate_output_dir(path: Path, findings: list[PluginScaffoldFinding]) -> None:
    """Validate output directory text without requiring it to exist."""
    path_text = str(path)
    if "://" in path_text or path_text.casefold().startswith(("http:", "https:")):
        findings.append(
            PluginScaffoldFinding(
                severity="error",
                message="Scaffold output must be a local filesystem path, not a URL.",
            )
        )
    if any(part == ".." for part in path.parts):
        findings.append(
            PluginScaffoldFinding(
                severity="error",
                message="Scaffold output paths must not contain path traversal.",
            )
        )
    _scan_text(path_text, findings, path="output_dir")


def _scan_text(
    text: str,
    findings: list[PluginScaffoldFinding],
    *,
    path: str | None = None,
) -> None:
    """Append findings for unsafe scaffold text."""
    lowered = text.casefold()
    for fragment in UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            findings.append(
                PluginScaffoldFinding(
                    severity="error",
                    message=redact_sensitive_text(
                        "Scaffold metadata contains unsafe text: " f"{fragment}."
                    ),
                    path=path,
                )
            )
    for word in UNSAFE_ACTION_WORDS:
        if word in lowered:
            findings.append(
                PluginScaffoldFinding(
                    severity="error",
                    message="Scaffold metadata must not include Procore write-action helpers.",
                    path=path,
                )
            )


def _is_relative_to(path: Path, parent: Path) -> bool:
    """Return whether path is inside parent on Python versions with Path.is_relative_to."""
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def scaffold_result_to_jsonable(result: PluginScaffoldResult) -> dict[str, Any]:
    """Return scaffold result metadata as a JSON-compatible dictionary."""
    return result.model_dump(mode="json")
