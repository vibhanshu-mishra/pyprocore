"""Safe local planning and copying of draft read-only endpoint scaffolds."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from pyprocore.catalog import CatalogEndpoint, CatalogEndpointSafety, load_oas_catalog
from pyprocore.core.exceptions import ValidationError
from pyprocore.maintenance.models import (
    ApiMaintenanceFinding,
    ApiScaffoldCopyResult,
    ApiScaffoldFile,
    ApiScaffoldPlan,
)


def plan_read_only_endpoint_scaffold(
    oas_path: str | Path,
    endpoint_path: str,
    method: str = "GET",
) -> ApiScaffoldPlan:
    """Plan draft files for one safe read-only endpoint.

    Args:
        oas_path: Local OAS JSON file path.
        endpoint_path: Exact endpoint path in the local catalog.
        method: HTTP method, restricted to likely read-only methods.

    Returns:
        Draft scaffold plan requiring human review.

    Raises:
        ValidationError: If the endpoint is missing or is not safely read-only.
    """
    normalized_method = method.upper()
    catalog = load_oas_catalog(oas_path)
    endpoint = next(
        (
            candidate
            for candidate in catalog.endpoints
            if candidate.path == endpoint_path and candidate.method == normalized_method
        ),
        None,
    )
    if endpoint is None:
        raise ValidationError(
            f"Endpoint was not found in the local OAS catalog: {normalized_method} {endpoint_path}"
        )
    _validate_scaffold_endpoint(endpoint)
    module_name = _safe_identifier(endpoint.path_area)
    model_name = "".join(part.title() for part in module_name.split("_")) or "Resource"
    files = _draft_files(endpoint, module_name, model_name)
    return ApiScaffoldPlan(
        source_path=str(oas_path),
        endpoint_path=endpoint.path,
        method=endpoint.method,
        safety_classification=endpoint.safety,
        allowed=True,
        files=files,
        findings=[
            ApiMaintenanceFinding(
                severity="warning",
                code="draft_human_review_required",
                message=(
                    "Draft scaffold only. Verify endpoint semantics, models, pagination, "
                    "permissions, tests, and documentation before manual integration."
                ),
            )
        ],
    )


def copy_read_only_endpoint_scaffold(
    plan: ApiScaffoldPlan,
    output_dir: str | Path,
    *,
    dry_run: bool = False,
    overwrite: bool = False,
) -> ApiScaffoldCopyResult:
    """Copy planned draft files beneath an explicit local output directory.

    Args:
        plan: Valid read-only scaffold plan.
        output_dir: Local directory that will contain draft files.
        dry_run: When true, validate destinations without writing.
        overwrite: Whether existing files may be replaced.

    Returns:
        Copy or dry-run result.

    Raises:
        ValidationError: If the plan is unsafe, traversal is detected, or a
            destination already exists without explicit overwrite permission.
    """
    if not plan.allowed or plan.safety_classification != CatalogEndpointSafety.READ_ONLY:
        raise ValidationError("Only allowed read-only scaffold plans may be copied.")
    root = Path(output_dir).expanduser().resolve()
    destinations: list[tuple[ApiScaffoldFile, Path]] = []
    for scaffold_file in plan.files:
        relative_path = _validate_relative_scaffold_path(scaffold_file.relative_path)
        destination = (root / relative_path).resolve()
        if not destination.is_relative_to(root):
            raise ValidationError(
                f"Scaffold path must remain inside the output directory: {relative_path}"
            )
        if destination.exists() and not overwrite:
            raise ValidationError(
                f"Scaffold destination already exists; use --overwrite explicitly: {destination}"
            )
        destinations.append((scaffold_file, destination))
    if dry_run:
        return ApiScaffoldCopyResult(
            plan=plan,
            output_dir=str(root),
            dry_run=True,
            skipped_files=[str(destination) for _, destination in destinations],
            findings=[
                ApiMaintenanceFinding(
                    severity="info",
                    code="dry_run",
                    message="Dry-run completed; no files were written.",
                )
            ],
        )
    written: list[str] = []
    for scaffold_file, destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(scaffold_file.content, encoding="utf-8")
        written.append(str(destination))
    return ApiScaffoldCopyResult(
        plan=plan,
        output_dir=str(root),
        dry_run=False,
        written_files=written,
        findings=[
            ApiMaintenanceFinding(
                severity="warning",
                code="draft_files_written",
                message="Draft files were copied locally. Human review is required.",
            )
        ],
    )


def _validate_scaffold_endpoint(endpoint: CatalogEndpoint) -> None:
    """Refuse methods or naming that are not safely read-only."""
    if endpoint.method not in {"GET", "HEAD", "OPTIONS"}:
        raise ValidationError(
            f"Scaffolding refuses write/mutation method {endpoint.method}: {endpoint.path}"
        )
    if endpoint.safety != CatalogEndpointSafety.READ_ONLY:
        reasons = "; ".join(endpoint.safety_reasons)
        raise ValidationError(
            f"Scaffolding refuses risky or unknown endpoint {endpoint.method} "
            f"{endpoint.path}: {reasons}"
        )


def _validate_relative_scaffold_path(value: str) -> Path:
    """Validate one portable relative scaffold path."""
    pure_path = PurePosixPath(value)
    if pure_path.is_absolute() or ".." in pure_path.parts or not pure_path.parts:
        raise ValidationError(f"Unsafe scaffold relative path: {value}")
    if any(part in {"", "."} for part in pure_path.parts):
        raise ValidationError(f"Unsafe scaffold relative path: {value}")
    return Path(*pure_path.parts)


def _safe_identifier(value: str) -> str:
    """Create a conservative Python identifier from an endpoint area."""
    normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    if not normalized or normalized[0].isdigit():
        return f"resource_{normalized}" if normalized else "resource"
    return normalized


def _draft_files(
    endpoint: CatalogEndpoint,
    module_name: str,
    model_name: str,
) -> list[ApiScaffoldFile]:
    """Build clearly marked draft content for one read-only endpoint."""
    endpoint_literal = repr(endpoint.path)
    service = f'''"""DRAFT read-only service scaffold; human review required."""

from __future__ import annotations


def list_{module_name}() -> list[dict[str, object]]:
    """DRAFT: retrieve {module_name}; verify endpoint shape before integration."""
    raise NotImplementedError(
        "Draft only: verify {endpoint.method} {endpoint.path} before implementation."
    )
'''
    model = f'''"""DRAFT typed model scaffold; human review required."""

from __future__ import annotations

from pyprocore.models.base import ProcoreModel


class {model_name}(ProcoreModel):
    """DRAFT flexible model; replace fields after reviewing fake payload fixtures."""

    id: int | None = None
'''
    test = f'''"""DRAFT mocked tests for the {module_name} read-only scaffold."""

import unittest
from unittest.mock import Mock


class {model_name}ServiceTests(unittest.TestCase):
    """DRAFT tests; no live Procore access."""

    def test_list_uses_expected_path(self) -> None:
        """DRAFT: verify the service uses the reviewed GET path."""
        client = Mock()
        client.get_all.return_value = []
        self.assertEqual(client.get_all({endpoint_literal}), [])
'''
    example = f'''"""DRAFT local example for {module_name}; human review required."""


def main() -> None:
    """Explain the draft without making a live Procore call."""
    print("Draft endpoint: {endpoint.method} {endpoint.path}")
    print("Review and integrate this scaffold before using it.")


if __name__ == "__main__":
    main()
'''
    docs = f"""# DRAFT: {model_name}

Human review is required before integration.

- Proposed endpoint: `{endpoint.method} {endpoint.path}`
- Safety classification: `{endpoint.safety.value}`
- This draft does not enable tool execution or Procore writes.
- Verify context IDs, pagination, permissions, payload shape, and official docs.
"""
    return [
        ApiScaffoldFile(
            relative_path=f"pyprocore/services/{module_name}.py",
            purpose="Draft read-only service skeleton",
            content=service,
        ),
        ApiScaffoldFile(
            relative_path=f"pyprocore/models/{module_name}.py",
            purpose="Draft flexible model skeleton",
            content=model,
        ),
        ApiScaffoldFile(
            relative_path=f"tests/test_{module_name}.py",
            purpose="Draft mocked test skeleton",
            content=test,
        ),
        ApiScaffoldFile(
            relative_path=f"examples/draft_{module_name}.py",
            purpose="Draft local-only example skeleton",
            content=example,
        ),
        ApiScaffoldFile(
            relative_path=f"docs/drafts/{module_name}.md",
            purpose="Draft documentation stub",
            content=docs,
        ),
    ]
