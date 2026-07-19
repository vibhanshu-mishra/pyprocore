"""Tests for Phase 13C eval baselines, regressions, and history."""

from __future__ import annotations

import json
import sys
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pyprocore
from pyprocore import app
from pyprocore.core.exceptions import ValidationError
from pyprocore.evals import (
    EvalStatus,
    append_eval_history_snapshot,
    build_eval_baseline,
    build_eval_history_markdown,
    build_eval_history_snapshot,
    build_regression_report_json,
    build_regression_report_markdown,
    compare_eval_report_to_baseline,
    default_eval_threshold_policy,
    eval_baseline_to_json,
    load_eval_baseline_from_dict,
    load_eval_baseline_from_file,
    load_eval_history_file,
    run_builtin_eval_suites,
    strict_eval_threshold_policy,
    summarize_eval_history,
    validate_eval_baseline,
    validate_local_eval_json_path,
    write_eval_baseline_json,
    write_regression_report_json,
    write_regression_report_markdown,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase13CEvalRegressionTestCase(unittest.TestCase):
    """Validate local deterministic eval regression helpers."""

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

    def test_baseline_construction_serialization_and_validation(self) -> None:
        """Baselines should snapshot deterministic eval report scores."""
        report = run_builtin_eval_suites(suite="rfi_workflow_golden")
        baseline = build_eval_baseline(report, baseline_name="unit-rfi-baseline")
        payload = json.loads(eval_baseline_to_json(baseline))
        findings = validate_eval_baseline(baseline)

        self.assertEqual(baseline.metadata.baseline_name, "unit-rfi-baseline")
        self.assertEqual(payload["schema_version"], "1")
        self.assertEqual(payload["metadata"]["suite_count"], 1)
        self.assertEqual(findings[0].severity.value, "pass")

    def test_baseline_file_loading_and_invalid_rejection(self) -> None:
        """Baseline files should load from safe local JSON and reject bad payloads."""
        report = run_builtin_eval_suites(suite="submittal_workflow_golden")
        baseline = build_eval_baseline(report, baseline_name="unit-submittal-baseline")
        with TemporaryDirectory() as temp_dir:
            baseline_path = Path(temp_dir) / "baseline.json"
            write_eval_baseline_json(baseline, baseline_path)
            reloaded = load_eval_baseline_from_file(baseline_path)
            self.assertEqual(reloaded.metadata.baseline_name, "unit-submittal-baseline")

            invalid_path = Path(temp_dir) / "invalid.json"
            invalid_path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "must be an object"):
                load_eval_baseline_from_file(invalid_path)

    def test_baseline_path_safety_rejects_remote_traversal_and_executable(self) -> None:
        """Baseline path validation should reject remote and unsafe paths."""
        with self.assertRaisesRegex(ValidationError, "local"):
            validate_local_eval_json_path("https://example.invalid/baseline.json", must_exist=False)
        with self.assertRaisesRegex(ValidationError, "traversal"):
            validate_local_eval_json_path("../baseline.json", must_exist=False)
        with self.assertRaisesRegex(ValidationError, "executable"):
            validate_local_eval_json_path("baseline.py", must_exist=False)

    def test_baseline_secret_redaction(self) -> None:
        """Baseline loading errors should redact secret-like text."""
        data = {
            "schema_version": "1",
            "metadata": {
                "baseline_name": "contains-access_token",
                "created_at": "2026-07-19T00:00:00Z",
                "pyprocore_version": "2.2.0",
                "suite_count": 0,
                "case_count": 0,
                "total_score": 0,
                "max_score": 0,
                "pass_count": 0,
                "fail_count": 0,
                "warning_count": 0,
            },
            "suites": [],
        }
        with self.assertRaisesRegex(ValidationError, r"\[REDACTED\]"):
            load_eval_baseline_from_dict(data)

    def test_equal_report_to_baseline_passes(self) -> None:
        """A report compared to its own baseline should pass."""
        report = run_builtin_eval_suites(suite="async_export_golden")
        baseline = build_eval_baseline(report, baseline_name="unit-async-baseline")
        result = compare_eval_report_to_baseline(report, baseline)

        self.assertTrue(result.passed)
        self.assertEqual(result.status, EvalStatus.PASS)

    def test_score_drop_and_pass_to_fail_regressions_are_detected(self) -> None:
        """Case score drops and pass-to-fail changes should fail comparison."""
        baseline_report = run_builtin_eval_suites(suite="rfi_workflow_golden")
        current_report = deepcopy(baseline_report)
        current_case = current_report.suites[0].cases[0]
        current_case.status = EvalStatus.FAIL
        current_case.passed = False
        current_case.score -= 1
        current_report.suites[0].score -= 1
        current_report.score -= 1
        current_report.suites[0].failed_cases = 1
        current_report.failed_cases = 1
        baseline = build_eval_baseline(baseline_report, baseline_name="unit-regression-baseline")

        result = compare_eval_report_to_baseline(current_report, baseline)
        checks = {finding.check for finding in result.findings}

        self.assertFalse(result.passed)
        self.assertIn("case_pass_to_fail", checks)
        self.assertIn("case_score_drop", checks)

    def test_new_warning_missing_suite_missing_case_and_new_suite_findings(self) -> None:
        """Comparison should detect warnings, missing items, and new suites."""
        baseline_report = run_builtin_eval_suites(suite="rfi_workflow_golden")
        current_report = run_builtin_eval_suites()
        baseline = build_eval_baseline(baseline_report, baseline_name="unit-finding-baseline")
        baseline.suites.append(deepcopy(baseline.suites[0]))
        baseline.suites[-1].suite_name = "missing_suite"
        baseline.suites[0].cases.append(deepcopy(baseline.suites[0].cases[0]))
        baseline.suites[0].cases[-1].case_id = "missing_case"

        result = compare_eval_report_to_baseline(current_report, baseline)
        checks = {finding.check for finding in result.findings}

        self.assertIn("missing_suite", checks)
        self.assertIn("missing_case", checks)
        self.assertIn("new_suite", checks)

    def test_threshold_policy_default_and_strict_behavior(self) -> None:
        """Threshold policies should provide default and strict local behavior."""
        report = run_builtin_eval_suites(suite="safety_boundaries_golden")
        baseline = build_eval_baseline(report, baseline_name="unit-policy-baseline")
        default_result = compare_eval_report_to_baseline(
            report,
            baseline,
            policy=default_eval_threshold_policy(),
        )
        strict_result = compare_eval_report_to_baseline(
            report,
            baseline,
            policy=strict_eval_threshold_policy(),
        )

        self.assertTrue(default_result.passed)
        self.assertTrue(strict_result.passed)

        failing_policy = default_eval_threshold_policy()
        failing_policy.minimum_total_score = report.score + 1
        failing_result = compare_eval_report_to_baseline(report, baseline, policy=failing_policy)
        self.assertFalse(failing_result.passed)

    def test_regression_report_json_markdown_and_output_paths(self) -> None:
        """Regression reports should render and write safe JSON and Markdown files."""
        report = run_builtin_eval_suites(suite="plugin_config_golden")
        baseline = build_eval_baseline(report, baseline_name="unit-report-baseline")
        result = compare_eval_report_to_baseline(report, baseline)
        json_payload = json.loads(build_regression_report_json(result))
        markdown = build_regression_report_markdown(result)

        self.assertEqual(json_payload["baseline_name"], "unit-report-baseline")
        self.assertIn("PyProcore Eval Regression Report", markdown)
        with TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "regression.json"
            markdown_path = Path(temp_dir) / "regression.md"
            write_regression_report_json(result, json_path)
            write_regression_report_markdown(result, markdown_path)
            self.assertTrue(json_path.exists())
            self.assertTrue(markdown_path.exists())

    def test_history_snapshot_append_load_and_summary(self) -> None:
        """History helpers should append and summarize local snapshots."""
        report = run_builtin_eval_suites(suite="ai_workflow_package_golden")
        snapshot = build_eval_history_snapshot(report, label="unit-history")
        with TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "history.json"
            append_eval_history_snapshot(history_path, snapshot)
            snapshots = load_eval_history_file(history_path)
            summary = summarize_eval_history(snapshots)
            markdown = build_eval_history_markdown(summary)

        self.assertEqual(summary.snapshot_count, 1)
        self.assertIn("unit-history", markdown)

    def test_cli_baseline_compare_regression_and_history_commands(self) -> None:
        """CLI should expose Phase 13C baseline, comparison, and history commands."""
        sample_code, sample_output = self.run_cli_in_process("evals", "baseline", "sample")
        history_sample_code, history_sample_output = self.run_cli_in_process(
            "evals",
            "history",
            "sample",
        )
        self.assertEqual(sample_code, 0)
        self.assertIn("eval baseline", sample_output.casefold())
        self.assertEqual(history_sample_code, 0)
        self.assertIn("eval history", history_sample_output.casefold())

        with TemporaryDirectory() as temp_dir:
            baseline_path = Path(temp_dir) / "baseline.json"
            history_path = Path(temp_dir) / "history.json"
            create_code, create_output = self.run_cli_in_process(
                "evals",
                "baseline",
                "create",
                "--suite",
                "rfi_workflow_golden",
                "--output",
                str(baseline_path),
            )
            validate_code, validate_output = self.run_cli_in_process(
                "evals",
                "baseline",
                "validate",
                str(baseline_path),
            )
            compare_code, compare_output = self.run_cli_in_process(
                "evals",
                "compare",
                "--baseline",
                str(baseline_path),
                "--suite",
                "rfi_workflow_golden",
            )
            report_code, report_output = self.run_cli_in_process(
                "evals",
                "regression-report",
                "--baseline",
                str(baseline_path),
                "--suite",
                "rfi_workflow_golden",
                "--format",
                "markdown",
            )
            append_code, append_output = self.run_cli_in_process(
                "evals",
                "history",
                "append",
                "--suite",
                "rfi_workflow_golden",
                "--output",
                str(history_path),
            )
            summary_code, summary_output = self.run_cli_in_process(
                "evals",
                "history",
                "summary",
                str(history_path),
            )

        self.assertEqual(create_code, 0, create_output)
        self.assertEqual(validate_code, 0, validate_output)
        self.assertEqual(compare_code, 0, compare_output)
        self.assertEqual(report_code, 0, report_output)
        self.assertEqual(append_code, 0, append_output)
        self.assertEqual(summary_code, 0, summary_output)
        self.assertIn("baseline written", create_output.casefold())
        self.assertIn("baseline", validate_output.casefold())
        self.assertIn("regression comparison", compare_output.casefold())
        self.assertIn("Eval Regression Report", report_output)
        self.assertIn("snapshot appended", append_output.casefold())
        self.assertIn("Eval History", summary_output)

    def test_examples_sample_files_and_docs_are_present(self) -> None:
        """Phase 13C examples, sample files, and docs should be discoverable."""
        examples_readme = (PROJECT_ROOT / "examples/README.md").read_text(encoding="utf-8")
        docs_evals = (PROJECT_ROOT / "docs/evals.md").read_text(encoding="utf-8").casefold()
        for number in range(229, 239):
            matches = sorted((PROJECT_ROOT / "examples").glob(f"{number}_*.py"))
            self.assertEqual(len(matches), 1)
            text = matches[0].read_text(encoding="utf-8")
            self.assertIn('if __name__ == "__main__":', text)
            self.assertIn(matches[0].name, examples_readme)
        self.assertTrue(
            (PROJECT_ROOT / "examples/eval_baselines/sample_eval_baseline.json").exists()
        )
        self.assertTrue(
            (PROJECT_ROOT / "examples/eval_reports/sample_regression_report.json").exists()
        )
        self.assertTrue(
            (PROJECT_ROOT / "examples/eval_reports/sample_regression_report.md").exists()
        )
        self.assertTrue((PROJECT_ROOT / "examples/eval_reports/sample_eval_history.json").exists())
        self.assertIn("phase 13c", docs_evals)
        self.assertIn("baseline", docs_evals)
        self.assertIn("regression", docs_evals)

    def test_existing_eval_and_agent_eval_commands_still_work(self) -> None:
        """Phase 13C should not break existing eval or agent eval commands."""
        eval_code, eval_output = self.run_cli_in_process(
            "evals", "run", "--suite", "rfi_workflow_golden"
        )
        agent_code, agent_output = self.run_cli_in_process("agent", "evals", "run")

        self.assertEqual(eval_code, 0)
        self.assertIn("rfi_workflow_golden", eval_output)
        self.assertEqual(agent_code, 0)
        self.assertIn("PyProcore Agent Eval Summary", agent_output)

    def test_eval_source_safety_boundaries_remain_local_only(self) -> None:
        """Eval source should not add remote fetching or runtime loading behavior."""
        forbidden_fragments = (
            "subprocess",
            "importlib",
            "eval(",
            "exec(",
            "pip install",
            "requests.",
            "httpx.",
            "create_procore",
            "update_procore",
            "delete_procore",
        )
        for path in sorted((PROJECT_ROOT / "pyprocore/evals").glob("*.py")):
            text = path.read_text(encoding="utf-8").casefold()
            with self.subTest(path=path.name):
                self.assertFalse(any(fragment in text for fragment in forbidden_fragments))

    def test_public_root_exports_include_phase13c_helpers(self) -> None:
        """Phase 13C helpers should be exported from the package root."""
        self.assertIs(pyprocore.build_eval_baseline, build_eval_baseline)
        self.assertIs(pyprocore.compare_eval_report_to_baseline, compare_eval_report_to_baseline)
        self.assertIs(pyprocore.append_eval_history_snapshot, append_eval_history_snapshot)

    def test_workflows_were_not_modified(self) -> None:
        """Phase 13C should not touch GitHub Actions workflow files."""
        workflow_status = self.run_git_status_for_workflows()
        self.assertEqual(workflow_status, "")

    @staticmethod
    def run_git_status_for_workflows() -> str:
        """Return porcelain status for workflow files without shelling out in eval code."""
        from subprocess import run

        result = run(
            ["git", "status", "--short", ".github/workflows"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            check=True,
            text=True,
        )
        return result.stdout.strip()


if __name__ == "__main__":
    unittest.main()
