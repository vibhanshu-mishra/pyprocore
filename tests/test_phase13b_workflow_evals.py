"""Tests for Phase 13B workflow-specific golden eval suites."""

from __future__ import annotations

import json
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pyprocore
from pyprocore import app
from pyprocore.evals import (
    eval_report_to_json,
    eval_report_to_markdown,
    get_builtin_dataset,
    list_builtin_dataset_names,
    list_builtin_eval_suites,
    load_golden_dataset_from_file,
    run_builtin_eval_suites,
)
from pyprocore.evals.workflow_scoring import (
    allowed_capability_score,
    allowed_hook_type_score,
    expected_field_set_score,
    forbidden_phrase_score,
    manifest_status_score,
    no_mutation_instruction_score,
    no_secret_like_value_score,
    path_within_output_dir_score,
    placeholder_only_score,
    required_phrase_score,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase13BWorkflowEvalsTestCase(unittest.TestCase):
    """Validate workflow-specific deterministic eval suites."""

    workflow_suite_names = {
        "rfi_workflow_golden",
        "submittal_workflow_golden",
        "async_export_golden",
        "async_batch_golden",
        "ai_workflow_package_golden",
        "plugin_metadata_golden",
        "plugin_config_golden",
        "safety_boundaries_golden",
    }

    def run_cli_in_process(self, *args: str) -> tuple[int, str]:
        """Run the CLI in-process for deterministic command tests."""
        output = StringIO()
        with patch.object(sys, "argv", ["procore-sdk", *args]), redirect_stdout(output):
            try:
                app.main()
            except SystemExit as exc:
                code = int(exc.code) if isinstance(exc.code, int) else 1
            else:
                code = 0
        return code, output.getvalue()

    def test_workflow_suite_listing_includes_phase13b_suites(self) -> None:
        """Built-in eval listing should include all workflow-specific suites."""
        names = set(list_builtin_dataset_names())
        suites = {suite.name: suite for suite in list_builtin_eval_suites()}

        self.assertTrue(self.workflow_suite_names.issubset(names))
        self.assertTrue(self.workflow_suite_names.issubset(suites))
        for suite_name in self.workflow_suite_names:
            self.assertGreater(suites[suite_name].case_count, 0)

    def test_each_workflow_suite_passes_locally(self) -> None:
        """Each Phase 13B workflow suite should pass with deterministic fixtures."""
        for suite_name in sorted(self.workflow_suite_names):
            with self.subTest(suite=suite_name):
                report = run_builtin_eval_suites(suite=suite_name)
                self.assertTrue(report.passed)
                self.assertEqual(report.total_suites, 1)
                self.assertEqual(report.failed_cases, 0)
                self.assertEqual(report.score, report.max_score)

    def test_all_builtins_include_phase13a_and_phase13b_suites(self) -> None:
        """Running all built-ins should preserve Phase 13A and add Phase 13B."""
        report = run_builtin_eval_suites()
        suite_names = {suite.suite_name for suite in report.suites}

        self.assertTrue(report.passed)
        self.assertEqual(report.total_suites, 15)
        self.assertIn("golden_export_rows_basic", suite_names)
        self.assertTrue(self.workflow_suite_names.issubset(suite_names))

    def test_suite_filtering_and_unknown_suite_rejection(self) -> None:
        """Suite filtering should run one suite and reject unknown names."""
        report = run_builtin_eval_suites(suite="rfi_workflow_golden")

        self.assertEqual(report.total_suites, 1)
        self.assertEqual(report.suites[0].suite_name, "rfi_workflow_golden")
        with self.assertRaisesRegex(ValueError, "Unknown built-in"):
            get_builtin_dataset("missing_workflow_suite")

    def test_workflow_reports_render_json_and_markdown(self) -> None:
        """Workflow eval reports should serialize as JSON and Markdown."""
        report = run_builtin_eval_suites(suite="async_batch_golden")
        json_payload = json.loads(eval_report_to_json(report))
        markdown = eval_report_to_markdown(report)

        self.assertEqual(json_payload["suites"][0]["suite_name"], "async_batch_golden")
        self.assertIn("async_batch_golden", markdown)
        self.assertIn("local deterministic fixtures only", markdown)

    def test_workflow_scoring_helpers_pass_and_fail_predictably(self) -> None:
        """Workflow-specific scoring helpers should be deterministic."""
        row = [{"id": "sample-1", "title": "Sample item", "status": "open"}]
        manifest = {
            "name": "sample_manifest",
            "status": "success",
            "capabilities": ["exporter"],
            "hooks": [{"type": "metadata"}],
        }

        self.assertTrue(expected_field_set_score(row, ["id", "title"]).passed)
        self.assertFalse(expected_field_set_score(row, ["missing"]).passed)
        self.assertTrue(required_phrase_score("Do not invent facts.", ["invent facts"]).passed)
        self.assertFalse(required_phrase_score("Use context.", ["invent facts"]).passed)
        self.assertTrue(forbidden_phrase_score("Use context.", ["make up facts"]).passed)
        self.assertFalse(forbidden_phrase_score("make up facts", ["make up facts"]).passed)
        self.assertTrue(
            path_within_output_dir_score("./exports/sample", ["./exports/sample/rfis.jsonl"]).passed
        )
        self.assertFalse(
            path_within_output_dir_score("./exports/sample", ["./exports/other/rfis.jsonl"]).passed
        )
        self.assertTrue(manifest_status_score(manifest, "success").passed)
        self.assertFalse(manifest_status_score(manifest, "failed").passed)
        self.assertTrue(no_mutation_instruction_score("read-only sample context").passed)
        self.assertFalse(no_mutation_instruction_score("approve submittal automatically").passed)
        self.assertTrue(no_secret_like_value_score({"value": "sample"}).passed)
        self.assertFalse(no_secret_like_value_score({"access_token": "sample"}).passed)
        self.assertTrue(placeholder_only_score({"name": "sample local fixture"}).passed)
        self.assertFalse(placeholder_only_score({"name": "real-company"}).passed)
        self.assertTrue(allowed_capability_score(manifest, ["exporter"]).passed)
        self.assertFalse(allowed_capability_score(manifest, ["validator"]).passed)
        self.assertTrue(allowed_hook_type_score(manifest, ["metadata"]).passed)
        self.assertFalse(allowed_hook_type_score(manifest, ["remote"]).passed)

    def test_sample_workflow_dataset_files_are_valid_and_safe(self) -> None:
        """Workflow sample datasets should load and contain safe placeholder data."""
        dataset_paths = sorted((PROJECT_ROOT / "examples/golden_datasets").glob("*/*.json"))
        self.assertGreaterEqual(len(dataset_paths), 8)

        unsafe_fragments = (
            "bearer ",
            "authorization:",
            "client_secret",
            "refresh_token",
            "access_token",
            "pip install",
            "curl ",
            "wget ",
        )
        for path in dataset_paths:
            with self.subTest(path=path):
                dataset = load_golden_dataset_from_file(path)
                payload_text = json.dumps(dataset.model_dump(mode="json")).casefold()
                self.assertIn("placeholder", payload_text)
                self.assertFalse(any(fragment in payload_text for fragment in unsafe_fragments))

    def test_phase13b_examples_are_documented_and_have_main_guards(self) -> None:
        """Examples 219-228 should be present, documented, and runnable as scripts."""
        examples_readme = (PROJECT_ROOT / "examples/README.md").read_text(encoding="utf-8")
        for number in range(219, 229):
            matches = sorted((PROJECT_ROOT / "examples").glob(f"{number}_*.py"))
            self.assertEqual(len(matches), 1)
            text = matches[0].read_text(encoding="utf-8")
            self.assertIn('if __name__ == "__main__":', text)
            self.assertIn(matches[0].name, examples_readme)

    def test_cli_list_run_and_report_include_workflow_suites(self) -> None:
        """CLI eval commands should expose workflow suite filtering and reporting."""
        list_code, list_output = self.run_cli_in_process("evals", "list")
        run_code, run_output = self.run_cli_in_process(
            "evals",
            "run",
            "--suite",
            "rfi_workflow_golden",
        )
        report_code, report_output = self.run_cli_in_process(
            "evals",
            "report",
            "--suite",
            "safety_boundaries_golden",
            "--format",
            "json",
        )

        self.assertEqual(list_code, 0)
        self.assertIn("rfi_workflow_golden", list_output)
        self.assertEqual(run_code, 0)
        self.assertIn("rfi_workflow_golden", run_output)
        self.assertEqual(report_code, 0)
        self.assertIn("safety_boundaries_golden", report_output)

    def test_existing_agent_evals_command_still_works(self) -> None:
        """Phase 13B should not break the existing agent eval command."""
        code, output = self.run_cli_in_process("agent", "evals", "run")

        self.assertEqual(code, 0)
        self.assertIn("PyProcore Agent Eval Summary", output)

    def test_eval_source_contains_no_disallowed_runtime_loading(self) -> None:
        """Eval source should avoid runtime loading, shelling out, and package installs."""
        forbidden_fragments = (
            "subprocess",
            "importlib",
            "eval(",
            "exec(",
            "pip install",
        )
        for path in sorted((PROJECT_ROOT / "pyprocore/evals").glob("*.py")):
            text = path.read_text(encoding="utf-8").casefold()
            with self.subTest(path=path.name):
                self.assertFalse(any(fragment in text for fragment in forbidden_fragments))

    def test_public_exports_include_workflow_scoring_helpers(self) -> None:
        """Workflow scoring helpers should be available from the package root."""
        self.assertIs(pyprocore.expected_field_set_score, expected_field_set_score)
        self.assertIs(pyprocore.path_within_output_dir_score, path_within_output_dir_score)
        self.assertIs(pyprocore.allowed_capability_score, allowed_capability_score)


if __name__ == "__main__":
    unittest.main()
