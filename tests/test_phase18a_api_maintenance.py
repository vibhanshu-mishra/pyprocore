"""Tests for the Phase 18A local API maintenance assistant."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pyprocore.app import build_parser, run_command
from pyprocore.catalog import CatalogEndpointSafety
from pyprocore.core.exceptions import ValidationError
from pyprocore.maintenance import (
    ApiCoverageGapReport,
    ApiDriftReport,
    ApiMaintenancePlan,
    ApiScaffoldCopyResult,
    ApiScaffoldFile,
    analyze_pyprocore_coverage_gaps,
    build_api_maintenance_plan,
    compare_oas_catalogs,
    copy_read_only_endpoint_scaffold,
    coverage_gap_report_to_markdown,
    drift_report_to_markdown,
    maintenance_plan_to_markdown,
    maintenance_report_to_json,
    plan_read_only_endpoint_scaffold,
    scaffold_copy_result_to_markdown,
    scaffold_plan_to_markdown,
)

ROOT = Path(__file__).resolve().parents[1]
OLD_OAS = ROOT / "examples" / "maintenance" / "old_fake_procore_oas.json"
NEW_OAS = ROOT / "examples" / "maintenance" / "new_fake_procore_oas.json"
SAFE_PATH = "/rest/v1.0/projects/{project_id}/readiness_checks"
RISKY_PATH = "/rest/v1.0/projects/{project_id}/document_uploads"


class ApiMaintenanceDriftTests(unittest.TestCase):
    """Exercise deterministic local OAS drift and gap analysis."""

    def test_drift_detects_added_removed_parameter_and_operation_id_changes(self) -> None:
        """The fake catalogs should expose all requested drift categories."""
        report = compare_oas_catalogs(OLD_OAS, NEW_OAS)

        self.assertIsInstance(report, ApiDriftReport)
        self.assertIn(SAFE_PATH, {change.path for change in report.added_endpoints})
        self.assertIn(
            "/rest/v1.0/projects/{project_id}/legacy_notes",
            {change.path for change in report.removed_endpoints},
        )
        self.assertIn(
            "/rest/v1.0/projects/{project_id}/safety_reviews",
            {change.path for change in report.changed_parameters},
        )
        self.assertEqual(
            report.changed_operation_ids[0].operation_id_after,
            "findSafetyReviews",
        )
        self.assertFalse(report.remote_fetch_enabled)
        self.assertFalse(report.procore_calls_enabled)
        self.assertTrue(report.human_review_required)

    def test_drift_detects_changed_methods_and_risky_changes(self) -> None:
        """GET-to-POST method drift and risky terms must be highlighted."""
        report = compare_oas_catalogs(OLD_OAS, NEW_OAS)

        self.assertIn(
            "/rest/v1.0/projects/{project_id}/review_queue",
            {change.path for change in report.changed_methods},
        )
        risky_paths = {change.path for change in report.risky_changes}
        self.assertIn(RISKY_PATH, risky_paths)
        self.assertIn(
            "/rest/v1.0/projects/{project_id}/payment_approvals",
            risky_paths,
        )

    def test_coverage_gaps_separate_safe_and_deferred_endpoints(self) -> None:
        """Unsupported GET coverage is recommended while risky rows are deferred."""
        report = analyze_pyprocore_coverage_gaps(NEW_OAS)

        self.assertIsInstance(report, ApiCoverageGapReport)
        self.assertIn(SAFE_PATH, {gap.endpoint.path for gap in report.unsupported_read_only})
        self.assertIn(
            RISKY_PATH,
            {gap.endpoint.path for gap in report.unsupported_risky_write},
        )
        self.assertTrue(all(gap.deferred for gap in report.deferred_candidates))

    def test_maintenance_plan_groups_safe_and_risky_tasks(self) -> None:
        """Plan categories should keep risky endpoints out of safe work."""
        plan = build_api_maintenance_plan(NEW_OAS)

        self.assertIsInstance(plan, ApiMaintenancePlan)
        self.assertIn(
            SAFE_PATH,
            {task.endpoint_path for task in plan.safe_read_only_candidates},
        )
        self.assertIn(
            RISKY_PATH,
            {task.endpoint_path for task in plan.risky_write_deferred},
        )
        self.assertTrue(
            all(task.warning for task in plan.risky_write_deferred),
        )


class ApiMaintenanceScaffoldTests(unittest.TestCase):
    """Verify safe draft scaffold planning and local copying."""

    def test_scaffold_plan_allows_safe_get_and_marks_drafts(self) -> None:
        """A safe GET produces draft files with execution disabled."""
        plan = plan_read_only_endpoint_scaffold(NEW_OAS, SAFE_PATH)

        self.assertTrue(plan.allowed)
        self.assertEqual(plan.safety_classification, CatalogEndpointSafety.READ_ONLY)
        self.assertFalse(plan.generated_tools)
        self.assertTrue(plan.files)
        self.assertTrue(all(item.draft for item in plan.files))
        self.assertIn("NotImplementedError", plan.files[0].content)

    def test_scaffold_plan_refuses_write_methods(self) -> None:
        """POST/PATCH/PUT/DELETE operations are never scaffolded."""
        for path, method in [
            ("/rest/v1.0/projects/{project_id}/review_queue", "POST"),
            (SAFE_PATH, "PATCH"),
            (SAFE_PATH, "PUT"),
            (SAFE_PATH, "DELETE"),
        ]:
            with self.subTest(method=method):
                with self.assertRaises(ValidationError):
                    plan_read_only_endpoint_scaffold(NEW_OAS, path, method)

    def test_scaffold_plan_refuses_risky_get_path(self) -> None:
        """Risk-oriented path naming overrides GET classification."""
        with self.assertRaisesRegex(ValidationError, "refuses risky"):
            plan_read_only_endpoint_scaffold(NEW_OAS, RISKY_PATH)

    def test_dry_run_does_not_write(self) -> None:
        """Dry-run validates destinations without creating output."""
        plan = plan_read_only_endpoint_scaffold(NEW_OAS, SAFE_PATH)
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "draft"
            result = copy_read_only_endpoint_scaffold(plan, output, dry_run=True)

            self.assertIsInstance(result, ApiScaffoldCopyResult)
            self.assertTrue(result.dry_run)
            self.assertFalse(output.exists())
            self.assertEqual(len(result.skipped_files), len(plan.files))

    def test_copy_writes_only_under_temp_output_and_refuses_overwrite(self) -> None:
        """Explicit copy stays inside output and existing files require opt-in."""
        plan = plan_read_only_endpoint_scaffold(NEW_OAS, SAFE_PATH)
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "draft"
            result = copy_read_only_endpoint_scaffold(plan, output)

            self.assertEqual(len(result.written_files), len(plan.files))
            self.assertTrue(
                all(
                    Path(path).resolve().is_relative_to(output.resolve())
                    for path in result.written_files
                )
            )
            with self.assertRaisesRegex(ValidationError, "--overwrite"):
                copy_read_only_endpoint_scaffold(plan, output)

    def test_copy_blocks_path_traversal(self) -> None:
        """Manipulated scaffold paths cannot escape the output directory."""
        plan = plan_read_only_endpoint_scaffold(NEW_OAS, SAFE_PATH)
        unsafe_file = ApiScaffoldFile(
            relative_path="../outside.py",
            purpose="unsafe test",
            content="# unsafe",
        )
        unsafe_plan = plan.model_copy(update={"files": [unsafe_file]})
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(ValidationError, "Unsafe scaffold"):
                copy_read_only_endpoint_scaffold(unsafe_plan, temp_dir)


class ApiMaintenanceReportAndCliTests(unittest.TestCase):
    """Check report rendering and credential-free CLI dispatch."""

    def test_json_and_markdown_reports_render_safety_boundaries(self) -> None:
        """Every report type should render locally with human-review language."""
        drift = compare_oas_catalogs(OLD_OAS, NEW_OAS)
        gaps = analyze_pyprocore_coverage_gaps(NEW_OAS)
        plan = build_api_maintenance_plan(NEW_OAS)
        scaffold = plan_read_only_endpoint_scaffold(NEW_OAS, SAFE_PATH)
        with tempfile.TemporaryDirectory() as temp_dir:
            copied = copy_read_only_endpoint_scaffold(scaffold, temp_dir, dry_run=True)

        self.assertIn(
            '"human_review_required": true', maintenance_report_to_json(drift, pretty=True)
        )
        for rendered in [
            drift_report_to_markdown(drift),
            coverage_gap_report_to_markdown(gaps),
            maintenance_plan_to_markdown(plan),
            scaffold_plan_to_markdown(scaffold),
            scaffold_copy_result_to_markdown(copied),
        ]:
            self.assertIn("Human review", rendered)
            self.assertIn("No remote fetch", rendered)

    def test_cli_commands_run_without_credentials_or_procore_calls(self) -> None:
        """All maintenance commands should dispatch from local paths only."""
        parser = build_parser()
        command_rows = [
            ["maintenance", "drift", str(OLD_OAS), str(NEW_OAS)],
            ["maintenance", "coverage-gaps", str(NEW_OAS)],
            ["maintenance", "plan", str(NEW_OAS)],
            [
                "maintenance",
                "scaffold-plan",
                str(NEW_OAS),
                "--path",
                SAFE_PATH,
            ],
        ]
        with patch("requests.Session.request") as request:
            results = [run_command(parser.parse_args(row)) for row in command_rows]

        request.assert_not_called()
        self.assertIsInstance(results[0], ApiDriftReport)
        self.assertIsInstance(results[1], ApiCoverageGapReport)
        self.assertIsInstance(results[2], ApiMaintenancePlan)

    def test_cli_scaffold_dry_run_writes_nothing(self) -> None:
        """The CLI dry-run path should not create its output directory."""
        parser = build_parser()
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "draft"
            args = parser.parse_args(
                [
                    "maintenance",
                    "scaffold-read-endpoint",
                    str(NEW_OAS),
                    "--path",
                    SAFE_PATH,
                    "--output-dir",
                    str(output),
                    "--dry-run",
                ]
            )
            result = run_command(args)

            self.assertIsInstance(result, ApiScaffoldCopyResult)
            self.assertFalse(output.exists())

    def test_maintenance_sources_exclude_remote_and_execution_integrations(self) -> None:
        """Maintenance implementation must stay local and metadata-only."""
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / "pyprocore" / "maintenance").glob("*.py"))
        )
        for forbidden in [
            "import requests",
            "from requests",
            "import httpx",
            "from httpx",
            "import urllib",
            "import subprocess",
            "import importlib",
            "git commit",
            "git push",
            "import openai",
            "from openai",
        ]:
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
