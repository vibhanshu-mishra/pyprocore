"""Tests for scheduled automation examples and templates."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from pyprocore.workflows import load_workflow_plan, validate_workflow_plan

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PLANS = ROOT / "examples" / "workflow_plans"
SCHEDULED = ROOT / "examples" / "scheduled"
GITHUB_ACTIONS = ROOT / "examples" / "github-actions"


class ScheduledExamplesTestCase(unittest.TestCase):
    """Validate scheduled automation examples without executing them."""

    def test_scheduled_workflow_plan_json_files_parse_and_validate(self) -> None:
        """Scheduled example plans are valid JSON workflow plans."""
        expected_files = [
            "nightly_project_context.json",
            "weekly_ai_export.json",
            "rfi_submittal_sync.json",
            "lightweight_daily_logs_export.json",
        ]

        for filename in expected_files:
            with self.subTest(filename=filename):
                path = WORKFLOW_PLANS / filename
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertIn("name", payload)
                plan = validate_workflow_plan(load_workflow_plan(path))
                self.assertTrue(plan.steps)

    def test_shell_scripts_exist_and_call_workflow_plan_run(self) -> None:
        """Local scheduled runner scripts call the workflow-plan runner."""
        scripts = [
            SCHEDULED / "run_workflow_plan.sh",
            SCHEDULED / "run_workflow_plan.command",
            SCHEDULED / "run_workflow_plan.ps1",
        ]

        for script in scripts:
            with self.subTest(script=script.name):
                content = script.read_text(encoding="utf-8")
                self.assertIn("workflow-plan run", content)
                self.assertNotIn("PROCORE_CLIENT_SECRET=", content)

    def test_github_actions_template_contains_expected_keys(self) -> None:
        """GitHub Actions template documents schedule, secrets, and artifact upload."""
        content = (GITHUB_ACTIONS / "pyprocore-scheduled-workflow.yml").read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch", content)
        self.assertIn("schedule:", content)
        self.assertIn("PROCORE_CLIENT_ID", content)
        self.assertIn("PROCORE_CLIENT_SECRET", content)
        self.assertIn("workflow-plan validate", content)
        self.assertIn("workflow-plan run", content)
        self.assertIn("actions/upload-artifact", content)
        self.assertIn("token-store strategy", content)

    def test_launchd_plist_contains_expected_label_and_arguments(self) -> None:
        """launchd template contains label, program arguments, and logs."""
        content = (SCHEDULED / "com.pyprocore.nightly-project-context.plist").read_text(
            encoding="utf-8"
        )

        self.assertIn("com.pyprocore.nightly-project-context", content)
        self.assertIn("ProgramArguments", content)
        self.assertIn("run_workflow_plan.sh", content)
        self.assertIn("nightly_project_context.json", content)
        self.assertIn("StandardOutPath", content)
        self.assertIn("StandardErrorPath", content)


if __name__ == "__main__":
    unittest.main()
