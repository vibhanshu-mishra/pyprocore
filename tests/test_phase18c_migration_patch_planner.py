"""Tests for the Phase 18C local migration patch planner."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pyprocore.app import build_parser, run_command
from pyprocore.core.exceptions import ValidationError
from pyprocore.maintenance import (
    MigrationPatchArtifact,
    MigrationPatchPlan,
    MigrationPatchPlanOptions,
    MigrationPatchReport,
    build_migration_patch_plan,
    manual_review_checklist_to_markdown,
    migration_patch_plan_to_json,
    migration_patch_plan_to_markdown,
    migration_patch_report_to_json,
    migration_patch_report_to_markdown,
    render_unified_diff_suggestion,
    write_migration_patch_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
MAINTENANCE_EXAMPLES = ROOT / "examples" / "maintenance"
FAKE_CODEBASE = MAINTENANCE_EXAMPLES / "customer_codebase"
OLD_OAS = MAINTENANCE_EXAMPLES / "old_fake_procore_oas.json"
NEW_OAS = MAINTENANCE_EXAMPLES / "new_fake_procore_oas.json"


def _digest_tree(root: Path) -> dict[str, str]:
    """Return content hashes for regular non-cache fixture files."""
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


def _write_rfi_oas(
    path: Path,
    *,
    include_rfi: bool = True,
    optional_parameter: bool = False,
) -> None:
    """Write a tiny fake local OAS document for migration tests."""
    parameters: list[dict[str, object]] = [
        {
            "name": "project_id",
            "in": "path",
            "required": True,
            "schema": {"type": "integer"},
        }
    ]
    if optional_parameter:
        parameters.append(
            {
                "name": "per_page",
                "in": "query",
                "required": False,
                "schema": {"type": "integer"},
            }
        )
    paths = (
        {
            "/rest/v1.1/projects/{project_id}/rfis": {
                "get": {
                    "operationId": "listRfis",
                    "parameters": parameters,
                }
            }
        }
        if include_rfi
        else {}
    )
    path.write_text(
        json.dumps(
            {
                "openapi": "3.0.3",
                "info": {"title": "Fake migration OAS", "version": "1"},
                "paths": paths,
            }
        ),
        encoding="utf-8",
    )


class MigrationPatchPlannerTests(unittest.TestCase):
    """Exercise conservative suggestion planning."""

    def test_plan_without_oas_builds_general_readiness_report(self) -> None:
        """A no-OAS scan should be valid and clearly mark impact unknown."""
        plan = build_migration_patch_plan(FAKE_CODEBASE)

        self.assertIsInstance(plan, MigrationPatchPlan)
        self.assertFalse(plan.impact_report.oas_comparison_provided)
        self.assertIn("manual_review_required", {item.category for item in plan.suggestions})
        self.assertFalse(plan.customer_files_modified)
        self.assertFalse(plan.patches_applied)
        self.assertFalse(plan.git_operations_enabled)

    def test_plan_with_fake_oas_detects_changed_parameters(self) -> None:
        """Direct RFI use should inherit changed-parameter review guidance."""
        plan = build_migration_patch_plan(FAKE_CODEBASE, OLD_OAS, NEW_OAS)
        changed = [
            item for item in plan.suggestions if item.category == "review_changed_parameters"
        ]

        self.assertTrue(plan.impact_report.oas_comparison_provided)
        self.assertTrue(changed)
        self.assertTrue(any(item.capability_family == "rfis" for item in changed))

    def test_removed_rfi_endpoint_produces_high_priority_review(self) -> None:
        """Removed related endpoint metadata should never produce an automatic rewrite."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_oas = root / "old.json"
            new_oas = root / "new.json"
            _write_rfi_oas(old_oas)
            _write_rfi_oas(new_oas, include_rfi=False)

            plan = build_migration_patch_plan(FAKE_CODEBASE, old_oas, new_oas)

        removed = [
            item for item in plan.suggestions if item.category == "review_removed_endpoint_usage"
        ]
        self.assertTrue(removed)
        self.assertTrue(all(item.severity == "high" for item in removed))
        self.assertTrue(all(item.manual_review_only for item in removed))
        self.assertTrue(all(item.hunk is None for item in removed))

    def test_new_optional_parameter_gets_specific_category(self) -> None:
        """A purely additive optional parameter should be distinguished."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_oas = root / "old.json"
            new_oas = root / "new.json"
            _write_rfi_oas(old_oas)
            _write_rfi_oas(new_oas, optional_parameter=True)

            plan = build_migration_patch_plan(FAKE_CODEBASE, old_oas, new_oas)

        self.assertIn(
            "review_new_optional_parameters",
            {item.category for item in plan.suggestions},
        )

    def test_dynamic_usage_is_manual_review_only(self) -> None:
        """Dynamic getattr access must never receive a suggested diff."""
        plan = build_migration_patch_plan(FAKE_CODEBASE, OLD_OAS, NEW_OAS)
        dynamic = [item for item in plan.suggestions if item.category == "review_dynamic_usage"]

        self.assertTrue(dynamic)
        self.assertTrue(all(item.manual_review_only for item in dynamic))
        self.assertTrue(all(item.hunk is None for item in dynamic))

    def test_local_analytics_is_low_and_needs_no_api_change(self) -> None:
        """Exported-data analytics should remain separate from endpoint migration."""
        plan = build_migration_patch_plan(FAKE_CODEBASE, OLD_OAS, NEW_OAS)
        analytics = [
            item
            for item in plan.suggestions
            if item.category == "local_analytics_no_api_change_needed"
        ]

        self.assertTrue(analytics)
        self.assertTrue(all(item.severity == "low" for item in analytics))

    def test_cli_docs_can_receive_safe_non_applied_diff(self) -> None:
        """Only a static non-Python CLI reference may receive a review hunk."""
        plan = build_migration_patch_plan(FAKE_CODEBASE, OLD_OAS, NEW_OAS)
        cli = [item for item in plan.suggestions if item.category == "update_cli_command_docs"]

        self.assertTrue(cli)
        self.assertIsNotNone(cli[0].hunk)
        self.assertIn("REVIEW", cli[0].hunk.unified_diff if cli[0].hunk else "")
        self.assertFalse(cli[0].hunk.applied if cli[0].hunk else True)

    def test_ambiguous_or_python_usage_never_gets_code_diff(self) -> None:
        """Imports, calls, and dynamic access should have no generated code hunks."""
        plan = build_migration_patch_plan(FAKE_CODEBASE, OLD_OAS, NEW_OAS)

        for item in plan.suggestions:
            if item.file_path.endswith(".py"):
                self.assertIsNone(item.hunk)
                self.assertIsNone(render_unified_diff_suggestion(item))

    def test_secret_looking_snippets_remain_redacted(self) -> None:
        """Reports must never reintroduce fake secret values from Phase 18B."""
        plan = build_migration_patch_plan(FAKE_CODEBASE)
        serialized = migration_patch_plan_to_json(plan)

        self.assertIn("[REDACTED]", serialized)
        self.assertNotIn("fake-secret-for-redaction-tests", serialized)

    def test_options_can_omit_no_action_and_diff_suggestions(self) -> None:
        """Planner options should only reduce generated review metadata."""
        plan = build_migration_patch_plan(
            FAKE_CODEBASE,
            OLD_OAS,
            NEW_OAS,
            options=MigrationPatchPlanOptions(
                include_suggested_diffs=False,
                include_no_action_suggestions=False,
            ),
        )

        self.assertNotIn("no_action_recommended", {item.category for item in plan.suggestions})
        self.assertTrue(all(item.hunk is None for item in plan.suggestions))

    def test_json_markdown_and_checklist_reports_render(self) -> None:
        """All plan report forms should state their safety boundaries."""
        plan = build_migration_patch_plan(FAKE_CODEBASE, OLD_OAS, NEW_OAS)

        self.assertEqual(
            json.loads(migration_patch_plan_to_json(plan))["mode"],
            "local_migration_patch_plan",
        )
        markdown = migration_patch_plan_to_markdown(plan)
        self.assertIn("no patches are applied", markdown)
        self.assertIn("Human review is required", markdown)
        self.assertIn("Manual Review Checklist", manual_review_checklist_to_markdown(plan))


class MigrationPatchArtifactTests(unittest.TestCase):
    """Verify bounded optional artifact output behavior."""

    def setUp(self) -> None:
        """Build one deterministic fake local plan."""
        self.plan = build_migration_patch_plan(FAKE_CODEBASE, OLD_OAS, NEW_OAS)

    def test_dry_run_lists_expected_files_without_writing(self) -> None:
        """Dry-run must not create the selected output directory."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "review"
            report = write_migration_patch_artifacts(self.plan, output, dry_run=True)

            self.assertFalse(output.exists())
            self.assertEqual(len(report.planned_files), 5)
            self.assertEqual(
                {Path(path).name for path in report.planned_files},
                {
                    "migration_report.md",
                    "migration_report.json",
                    "suggested_changes.diff",
                    "impacted_files.json",
                    "manual_review_checklist.md",
                },
            )

    def test_write_stays_inside_output_and_preserves_customer_files(self) -> None:
        """Artifact writing must never modify the scanned customer fixture."""
        before = _digest_tree(FAKE_CODEBASE)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "review"
            report = write_migration_patch_artifacts(
                self.plan,
                output,
                dry_run=False,
            )

            self.assertEqual(len(report.written_files), 5)
            self.assertTrue(
                all(Path(path).is_relative_to(output.resolve()) for path in report.written_files)
            )
            self.assertTrue(all(Path(path).exists() for path in report.written_files))
        self.assertEqual(_digest_tree(FAKE_CODEBASE), before)

    def test_overwrite_is_refused_then_requires_explicit_opt_in(self) -> None:
        """Existing artifacts should remain protected by default."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "review"
            write_migration_patch_artifacts(self.plan, output, dry_run=False)

            with self.assertRaisesRegex(ValidationError, "use --overwrite"):
                write_migration_patch_artifacts(self.plan, output, dry_run=False)
            report = write_migration_patch_artifacts(
                self.plan,
                output,
                dry_run=False,
                overwrite=True,
            )

        self.assertEqual(len(report.written_files), 5)

    def test_artifact_path_traversal_is_blocked(self) -> None:
        """A manipulated artifact path cannot escape the output directory."""
        unsafe = MigrationPatchArtifact(
            relative_path="../escape.md",
            content="unsafe",
            purpose="test",
        )
        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "pyprocore.maintenance.patch_reports.build_migration_patch_artifacts",
                return_value=[unsafe],
            ):
                with self.assertRaisesRegex(ValidationError, "Unsafe patch artifact"):
                    write_migration_patch_artifacts(
                        self.plan,
                        Path(directory) / "review",
                        dry_run=False,
                    )

    def test_artifact_report_json_and_markdown_render(self) -> None:
        """Dry-run reports should serialize without writing."""
        with tempfile.TemporaryDirectory() as directory:
            report = write_migration_patch_artifacts(
                self.plan,
                Path(directory) / "review",
                dry_run=True,
            )

        self.assertIsInstance(report, MigrationPatchReport)
        self.assertTrue(json.loads(migration_patch_report_to_json(report))["dry_run"])
        self.assertIn("Dry-run: yes", migration_patch_report_to_markdown(report))
        self.assertFalse(report.customer_files_modified)
        self.assertFalse(report.patches_applied)


class MigrationPatchCliAndSafetyTests(unittest.TestCase):
    """Verify CLI dispatch and source-level safety boundaries."""

    def test_cli_plan_commands_work_without_credentials(self) -> None:
        """Migration and patch plan aliases should return typed local plans."""
        parser = build_parser()
        for command in ("migration-plan", "patch-plan"):
            args = parser.parse_args(
                [
                    "maintenance",
                    command,
                    str(FAKE_CODEBASE),
                    "--old-oas",
                    str(OLD_OAS),
                    "--new-oas",
                    str(NEW_OAS),
                ]
            )
            self.assertIsInstance(run_command(args), MigrationPatchPlan)

    def test_cli_patch_artifacts_dry_run_writes_nothing(self) -> None:
        """CLI artifact dry-run should return a report without creating output."""
        parser = build_parser()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "review"
            args = parser.parse_args(
                [
                    "maintenance",
                    "patch-artifacts",
                    str(FAKE_CODEBASE),
                    "--old-oas",
                    str(OLD_OAS),
                    "--new-oas",
                    str(NEW_OAS),
                    "--output-dir",
                    str(output),
                    "--dry-run",
                ]
            )
            report = run_command(args)

            self.assertIsInstance(report, MigrationPatchReport)
            self.assertFalse(output.exists())

    def test_phase18c_sources_exclude_remote_git_and_execution_integrations(self) -> None:
        """Planner source must remain standard-library, local, and non-executing."""
        sources = "\n".join(
            (ROOT / "pyprocore" / "maintenance" / name).read_text(encoding="utf-8")
            for name in ["migration.py", "patch_plan.py", "patch_reports.py"]
        ).lower()

        for forbidden in [
            "requests.",
            "subprocess.",
            "git clone",
            "git commit",
            "git push",
            "github",
            "openai",
            "anthropic",
            "subprocess.run",
            "os.system",
            "apply_patch",
        ]:
            self.assertNotIn(forbidden, sources)


if __name__ == "__main__":
    unittest.main()
