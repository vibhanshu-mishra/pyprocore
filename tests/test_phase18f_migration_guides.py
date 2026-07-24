"""Tests for Phase 18F local deprecation and migration guides."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pyprocore.app import build_parser, run_command
from pyprocore.core.exceptions import ValidationError
from pyprocore.maintenance import (
    MigrationGuide,
    MigrationGuideArtifact,
    MigrationGuideReport,
    build_migration_guide,
    deprecation_summary_to_markdown,
    migration_guide_report_to_json,
    migration_guide_report_to_markdown,
    migration_guide_to_json,
    migration_guide_to_markdown,
    migration_test_plan_to_markdown,
    upgrade_checklist_to_markdown,
    write_migration_guide_artifacts,
)
from pyprocore.maintenance.migration_guide_reports import (
    build_migration_guide_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
MAINTENANCE = ROOT / "examples" / "maintenance"
OLD_CONTRACT = MAINTENANCE / "contracts" / "old_pyprocore_compatibility_contract.json"
NEW_CONTRACT = MAINTENANCE / "contracts" / "new_pyprocore_compatibility_contract.json"
FAKE_CODEBASE = MAINTENANCE / "customer_codebase"


def _hash_tree(root: Path) -> dict[str, str]:
    """Hash regular fixture files without executing or importing them."""
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


class MigrationGuideBuilderTests(unittest.TestCase):
    """Exercise general, contract, and codebase-specific guides."""

    def test_builds_without_contracts(self) -> None:
        """A general current-version guide should not require credentials."""
        guide = build_migration_guide()

        self.assertIsInstance(guide, MigrationGuide)
        self.assertEqual(guide.to_version, "2.4.0")
        self.assertFalse(guide.comparison_provided)
        self.assertIn("no previous/target", guide.summary)

    def test_contract_guide_includes_all_change_categories(self) -> None:
        """Fixture diff should produce additions, deprecations, gaps, and CLI notes."""
        guide = build_migration_guide(OLD_CONTRACT, NEW_CONTRACT)

        self.assertEqual([row.name for row in guide.feature_additions], ["photos"])
        self.assertEqual(
            [row.helper for row in guide.deprecations],
            ["build_project_context_package"],
        )
        self.assertIn("transmittals", {row.family for row in guide.known_gaps})
        section_titles = {section.title for section in guide.sections}
        self.assertIn("CLI changes", section_titles)
        self.assertIn("Safety boundary changes", section_titles)
        self.assertEqual(guide.overall_risk, "medium")

    def test_added_read_only_capability_is_low_or_informational(self) -> None:
        """Read-only fixture additions must not be framed as automatic breaking changes."""
        guide = build_migration_guide(OLD_CONTRACT, NEW_CONTRACT)

        self.assertIn(guide.feature_additions[0].risk_level, {"low", "informational"})
        photo_risks = [row.level for row in guide.risks if row.subject == "photos"]
        self.assertEqual(photo_risks, ["low"])

    def test_removed_resources_and_cli_are_breaking(self) -> None:
        """Reversing fixtures exposes removed capabilities as breaking review."""
        guide = build_migration_guide(NEW_CONTRACT, OLD_CONTRACT)

        subjects = {row.subject for row in guide.breaking_changes}
        self.assertIn("photos", subjects)
        self.assertIn("catalog", subjects)
        self.assertEqual(guide.overall_risk, "breaking")

    def test_codebase_impact_and_dynamic_usage_require_manual_review(self) -> None:
        """Dynamic fixture usage should be surfaced without editing the codebase."""
        before = _hash_tree(FAKE_CODEBASE)
        guide = build_migration_guide(
            OLD_CONTRACT,
            NEW_CONTRACT,
            FAKE_CODEBASE,
        )

        self.assertIsNotNone(guide.codebase_impact)
        self.assertIn("Codebase-specific impact", {row.title for row in guide.sections})
        self.assertIn("manual_review", {row.level for row in guide.risks})
        self.assertTrue(
            any("dynamic" in row.lower() for row in guide.manual_verification_checklist)
        )
        self.assertEqual(before, _hash_tree(FAKE_CODEBASE))
        self.assertFalse(guide.customer_files_modified)
        self.assertFalse(guide.patches_applied)

    def test_partial_contract_arguments_and_uncontracted_scan_are_rejected(self) -> None:
        """Ambiguous comparisons should fail with actionable validation."""
        with self.assertRaises(ValidationError):
            build_migration_guide(from_contract_path=OLD_CONTRACT)
        with self.assertRaises(ValidationError):
            build_migration_guide(codebase_path=FAKE_CODEBASE)


class MigrationGuideReportTests(unittest.TestCase):
    """Verify all machine- and human-readable reports."""

    def setUp(self) -> None:
        """Build one deterministic fixture guide."""
        self.guide = build_migration_guide(OLD_CONTRACT, NEW_CONTRACT)

    def test_json_and_markdown_render(self) -> None:
        """Primary reports should include versions, changes, and safety truth."""
        self.assertIn('"to_version": "2.3.0"', migration_guide_to_json(self.guide))
        markdown = migration_guide_to_markdown(self.guide)
        self.assertIn("New capabilities", markdown)
        self.assertIn("no Procore call", markdown)
        self.assertIn("Human review is required", markdown)

    def test_focused_reports_render(self) -> None:
        """Checklist, test-plan, and deprecation views should remain local-only."""
        self.assertIn("- [ ]", upgrade_checklist_to_markdown(self.guide))
        test_plan = migration_test_plan_to_markdown(self.guide)
        self.assertIn("mocked transports", test_plan)
        self.assertNotIn("smoke-", test_plan)
        self.assertIn(
            "build_project_context_package",
            deprecation_summary_to_markdown(self.guide),
        )

    def test_artifact_builder_has_fixed_safe_files(self) -> None:
        """The writer input should contain only the documented six files."""
        artifacts = build_migration_guide_artifacts(self.guide)

        self.assertEqual(
            {row.relative_path for row in artifacts},
            {
                "migration_guide.md",
                "migration_guide.json",
                "upgrade_checklist.md",
                "test_plan.md",
                "deprecation_summary.md",
                "metadata.json",
            },
        )

    def test_dry_run_lists_files_without_writing(self) -> None:
        """Dry-run must validate paths but leave the destination absent."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "guide"
            report = write_migration_guide_artifacts(self.guide, output)

            self.assertTrue(report.dry_run)
            self.assertEqual(len(report.planned_files), 6)
            self.assertFalse(output.exists())
            self.assertIn('"dry_run": true', migration_guide_report_to_json(report, pretty=True))
            self.assertIn("Dry-run: yes", migration_guide_report_to_markdown(report))

    def test_write_is_bounded_and_overwrite_requires_opt_in(self) -> None:
        """Artifacts may only be replaced with explicit permission."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "guide"
            report = write_migration_guide_artifacts(
                self.guide,
                output,
                dry_run=False,
            )

            self.assertEqual(len(report.written_files), 6)
            self.assertTrue(
                all(Path(path).is_relative_to(output.resolve()) for path in report.written_files)
            )
            with self.assertRaisesRegex(ValidationError, "--overwrite"):
                write_migration_guide_artifacts(self.guide, output, dry_run=False)
            replaced = write_migration_guide_artifacts(
                self.guide,
                output,
                dry_run=False,
                overwrite=True,
            )
            self.assertEqual(len(replaced.written_files), 6)

    def test_path_traversal_is_blocked(self) -> None:
        """An unsafe artifact name must never escape the selected directory."""
        unsafe = MigrationGuideArtifact(
            relative_path="../outside.md",
            purpose="unsafe test fixture",
            content="blocked",
        )
        with (
            tempfile.TemporaryDirectory() as directory,
            patch(
                "pyprocore.maintenance.migration_guide_reports.build_migration_guide_artifacts",
                return_value=[unsafe],
            ),
        ):
            with self.assertRaisesRegex(ValidationError, "Unsafe"):
                write_migration_guide_artifacts(self.guide, Path(directory) / "output")


class MigrationGuideCliAndSafetyTests(unittest.TestCase):
    """Exercise credential-free CLI commands and source safety."""

    def test_cli_commands_work_without_credentials(self) -> None:
        """Both guide commands should operate only on local fixtures."""
        parser = build_parser()
        guide = run_command(
            parser.parse_args(
                [
                    "maintenance",
                    "migration-guide",
                    "--from-contract",
                    str(OLD_CONTRACT),
                    "--to-contract",
                    str(NEW_CONTRACT),
                ]
            )
        )
        self.assertIsInstance(guide, MigrationGuide)

        with tempfile.TemporaryDirectory() as directory:
            report = run_command(
                parser.parse_args(
                    [
                        "maintenance",
                        "migration-guide-artifacts",
                        "--from-contract",
                        str(OLD_CONTRACT),
                        "--to-contract",
                        str(NEW_CONTRACT),
                        "--output-dir",
                        str(Path(directory) / "guide"),
                        "--dry-run",
                    ]
                )
            )
            self.assertIsInstance(report, MigrationGuideReport)
            self.assertTrue(report.dry_run)

    def test_source_contains_no_remote_or_execution_integrations(self) -> None:
        """Phase 18F modules should remain standard-library report generation."""
        source = (
            (ROOT / "pyprocore" / "maintenance" / "migration_guides.py").read_text()
            + (ROOT / "pyprocore" / "maintenance" / "migration_guide_reports.py").read_text()
        ).lower()

        for forbidden in [
            "import requests",
            "from requests",
            "import httpx",
            "subprocess",
            "github.",
            "gitpython",
            "open_pull_request",
            "apply_patch(",
        ]:
            self.assertNotIn(forbidden, source)
