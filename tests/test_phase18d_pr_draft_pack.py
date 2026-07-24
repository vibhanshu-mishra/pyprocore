"""Tests for the Phase 18D local pull-request draft pack."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from pyprocore.app import build_parser, run_command
from pyprocore.core.exceptions import ValidationError
from pyprocore.maintenance import (
    PullRequestDraftArtifact,
    PullRequestDraftPack,
    PullRequestDraftReport,
    build_pr_draft_pack,
    pr_draft_pack_to_json,
    pr_draft_pack_to_markdown,
    pr_draft_report_to_json,
    pr_draft_report_to_markdown,
    pr_review_checklist_to_markdown,
    pr_risk_summary_to_markdown,
    pr_test_plan_to_markdown,
    write_pr_draft_pack,
)

ROOT = Path(__file__).resolve().parents[1]
MAINTENANCE_EXAMPLES = ROOT / "examples" / "maintenance"
FAKE_CODEBASE = MAINTENANCE_EXAMPLES / "customer_codebase"
OLD_OAS = MAINTENANCE_EXAMPLES / "old_fake_procore_oas.json"
NEW_OAS = MAINTENANCE_EXAMPLES / "new_fake_procore_oas.json"
EXPECTED_ARTIFACTS = {
    "title.txt",
    "body.md",
    "review_checklist.md",
    "test_plan.md",
    "risk_summary.md",
    "impacted_files.json",
    "suggested_changes.diff",
    "migration_report.md",
    "metadata.json",
}


def _digest_tree(root: Path) -> dict[str, str]:
    """Return hashes for regular fixture files."""
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


class PullRequestDraftBuilderTests(unittest.TestCase):
    """Exercise conservative PR draft content generation."""

    def test_build_without_oas_is_general_and_safe(self) -> None:
        """A no-OAS draft should remain useful without claiming drift knowledge."""
        pack = build_pr_draft_pack(FAKE_CODEBASE)

        self.assertIsInstance(pack, PullRequestDraftPack)
        self.assertFalse(pack.migration_plan.impact_report.oas_comparison_provided)
        self.assertIn("No old/new local OAS comparison", pack.body)
        self.assertFalse(pack.customer_files_modified)
        self.assertFalse(pack.patches_applied)
        self.assertFalse(pack.pull_request_opened)

    def test_build_with_oas_includes_drift_summary(self) -> None:
        """Local old/new OAS files should add bounded drift context."""
        pack = build_pr_draft_pack(FAKE_CODEBASE, OLD_OAS, NEW_OAS)

        self.assertTrue(pack.migration_plan.impact_report.oas_comparison_provided)
        self.assertIn("Local OAS comparison found", pack.body)
        self.assertIn("parameter-change records", pack.body)

    def test_title_is_conservative(self) -> None:
        """Generated titles should request review and never claim applied fixes."""
        title = build_pr_draft_pack(FAKE_CODEBASE, OLD_OAS, NEW_OAS).title.lower()

        self.assertIn("review", title)
        self.assertNotIn("fixed", title)
        self.assertNotIn("applied", title)
        self.assertNotIn("automatic", title)

    def test_body_includes_usage_and_safety_boundaries(self) -> None:
        """The body should expose detected usage and every critical boundary."""
        body = build_pr_draft_pack(FAKE_CODEBASE).body

        self.assertIn("Detected PyProcore usage", body)
        self.assertIn("No customer files were modified", body)
        self.assertIn("No patches were applied", body)
        self.assertIn("No GitHub PR was opened", body)
        self.assertIn("No git commands were run", body)
        self.assertIn("No GitHub API", body)
        self.assertIn("No GitHub API, Procore API", body)
        self.assertIn("Human review is required", body)

    def test_checklist_covers_dynamic_and_manual_application(self) -> None:
        """Dynamic access and suggested changes must remain manual review items."""
        checklist = build_pr_draft_pack(FAKE_CODEBASE).review_checklist
        text = "\n".join(item.text for item in checklist)

        self.assertIn("Review dynamic PyProcore usage manually", text)
        self.assertIn("Apply suggested patches manually only after human review", text)

    def test_test_plan_avoids_live_procore_commands(self) -> None:
        """Default test guidance should use local or mocked data only."""
        test_plan = "\n".join(build_pr_draft_pack(FAKE_CODEBASE).test_plan)

        self.assertIn("mocked or sandbox fixture data only", test_plan)
        self.assertNotIn("procore-sdk companies", test_plan)
        self.assertNotIn("smoke-", test_plan)

    def test_risk_summary_groups_all_requested_priorities(self) -> None:
        """Risk metadata should expose high, medium, low, and manual buckets."""
        risk = build_pr_draft_pack(FAKE_CODEBASE, OLD_OAS, NEW_OAS).risk_summary

        self.assertTrue(risk.high)
        self.assertTrue(risk.medium)
        self.assertTrue(risk.low)
        self.assertTrue(risk.unknown_manual_review)

    def test_fixed_artifact_set_is_complete(self) -> None:
        """Every requested PR draft artifact should be represented."""
        pack = build_pr_draft_pack(FAKE_CODEBASE)

        self.assertEqual(
            {artifact.relative_path for artifact in pack.artifacts},
            EXPECTED_ARTIFACTS,
        )

    def test_json_and_markdown_reports_render(self) -> None:
        """Pack and component reports should serialize locally."""
        pack = build_pr_draft_pack(FAKE_CODEBASE)

        self.assertIn('"pull_request_opened": false', pr_draft_pack_to_json(pack, pretty=True))
        self.assertIn("Local Pull Request Draft Pack", pr_draft_pack_to_markdown(pack))
        self.assertIn("[ ] Review dynamic", pr_review_checklist_to_markdown(pack))
        self.assertIn("mocked or sandbox", pr_test_plan_to_markdown(pack))
        self.assertIn("Unknown / Manual Review", pr_risk_summary_to_markdown(pack.risk_summary))


class PullRequestDraftArtifactTests(unittest.TestCase):
    """Verify contained, opt-in artifact writing behavior."""

    def test_dry_run_lists_nine_files_without_writing(self) -> None:
        """Dry-run should return destinations without creating output."""
        pack = build_pr_draft_pack(FAKE_CODEBASE)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "draft"
            report = write_pr_draft_pack(pack, output)

            self.assertTrue(report.dry_run)
            self.assertEqual(len(report.planned_files), 9)
            self.assertFalse(output.exists())

    def test_explicit_write_stays_inside_output_and_preserves_customer_files(self) -> None:
        """Written artifacts must stay contained and leave fixtures unchanged."""
        before = _digest_tree(FAKE_CODEBASE)
        pack = build_pr_draft_pack(FAKE_CODEBASE)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "draft"
            report = write_pr_draft_pack(pack, output, dry_run=False)

            self.assertEqual(len(report.written_files), 9)
            self.assertTrue(
                all(Path(path).is_relative_to(output.resolve()) for path in report.written_files)
            )
            self.assertEqual(
                {path.name for path in output.iterdir()},
                EXPECTED_ARTIFACTS,
            )
        self.assertEqual(before, _digest_tree(FAKE_CODEBASE))

    def test_overwrite_requires_explicit_permission(self) -> None:
        """Existing artifacts should remain protected by default."""
        pack = build_pr_draft_pack(FAKE_CODEBASE)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "draft"
            write_pr_draft_pack(pack, output, dry_run=False)

            with self.assertRaises(ValidationError):
                write_pr_draft_pack(pack, output, dry_run=False)
            report = write_pr_draft_pack(
                pack,
                output,
                dry_run=False,
                overwrite=True,
            )
            self.assertEqual(len(report.written_files), 9)

    def test_path_traversal_is_blocked(self) -> None:
        """Manipulated artifact metadata cannot escape the output directory."""
        pack = build_pr_draft_pack(FAKE_CODEBASE)
        malicious = PullRequestDraftArtifact(
            relative_path="../outside.txt",
            purpose="invalid",
            content="invalid",
        )
        pack = pack.model_copy(update={"artifacts": [malicious]})
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValidationError):
                write_pr_draft_pack(pack, Path(directory) / "draft")

    def test_dry_run_report_serializes(self) -> None:
        """Dry-run reports should render in JSON and Markdown."""
        pack = build_pr_draft_pack(FAKE_CODEBASE)
        with tempfile.TemporaryDirectory() as directory:
            report = write_pr_draft_pack(pack, directory)

        self.assertIsInstance(report, PullRequestDraftReport)
        self.assertIn('"dry_run": true', pr_draft_report_to_json(report, pretty=True))
        self.assertIn("Dry-run: yes", pr_draft_report_to_markdown(report))


class PullRequestDraftCliAndSafetyTests(unittest.TestCase):
    """Exercise credential-free CLI dispatch and implementation boundaries."""

    def test_cli_commands_work_without_credentials(self) -> None:
        """Both commands should use local paths and typed reports only."""
        parser = build_parser()
        draft_args = parser.parse_args(
            ["maintenance", "pr-draft", str(FAKE_CODEBASE), "--format", "json"]
        )
        with tempfile.TemporaryDirectory() as directory:
            pack_args = parser.parse_args(
                [
                    "maintenance",
                    "pr-draft-pack",
                    str(FAKE_CODEBASE),
                    "--output-dir",
                    directory,
                    "--dry-run",
                    "--format",
                    "markdown",
                ]
            )
            report = run_command(pack_args)

        self.assertIsInstance(run_command(draft_args), PullRequestDraftPack)
        self.assertIsInstance(report, PullRequestDraftReport)
        self.assertTrue(report.dry_run)

    def test_cli_with_local_oas_reports_drift(self) -> None:
        """The CLI should accept paired local OAS paths without credentials."""
        args = build_parser().parse_args(
            [
                "maintenance",
                "pr-draft",
                str(FAKE_CODEBASE),
                "--old-oas",
                str(OLD_OAS),
                "--new-oas",
                str(NEW_OAS),
            ]
        )

        result = run_command(args)

        self.assertIsInstance(result, PullRequestDraftPack)
        self.assertTrue(result.migration_plan.impact_report.oas_comparison_provided)

    def test_sources_exclude_git_github_network_and_execution_integrations(self) -> None:
        """Phase 18D implementation must remain local and non-executing."""
        source = "\n".join(
            (ROOT / "pyprocore" / "maintenance" / name).read_text(encoding="utf-8")
            for name in ["pr_draft.py", "pr_reports.py"]
        )

        for forbidden in [
            "subprocess",
            "requests",
            "urllib",
            "httpx",
            "gitpython",
            "pygithub",
            "os.system",
            "mcp.execute",
        ]:
            self.assertNotIn(forbidden, source.lower())
        self.assertNotIn("api.github.com", source)


if __name__ == "__main__":
    unittest.main()
