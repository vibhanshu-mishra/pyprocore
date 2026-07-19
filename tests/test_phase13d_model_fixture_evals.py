"""Tests for Phase 13D offline model-response fixture evals."""

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
    ModelResponseFixture,
    build_eval_baseline,
    citation_label_score,
    compare_eval_report_to_baseline,
    grounding_statement_score,
    limitation_disclosure_score,
    list_builtin_eval_suites,
    load_model_response_fixture_from_dict,
    load_model_response_fixture_from_file,
    model_response_fixture_to_json,
    model_response_forbidden_phrases_score,
    no_approval_language_score,
    no_external_api_reference_score,
    no_fake_confidence_score,
    no_hallucinated_source_labels_score,
    no_live_call_claim_score,
    no_model_response_secret_like_value_score,
    no_write_action_language_score,
    required_sections_score,
    response_json_serializable_score,
    run_builtin_eval_suites,
    run_eval_case,
    sample_model_response_fixture,
    score_model_response_fixture,
    structured_json_response_score,
    validate_local_model_fixture_path,
    validate_model_response_fixture,
)
from pyprocore.evals.model_response_suites import get_model_response_dataset_payloads
from pyprocore.evals.models import GoldenDatasetCase, GoldenDatasetCaseType

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase13DModelFixtureEvalTestCase(unittest.TestCase):
    """Validate offline model-response fixture eval behavior."""

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

    def test_fixture_construction_serialization_and_validation(self) -> None:
        """Model-response fixtures should be typed and JSON serializable."""
        fixture = sample_model_response_fixture()
        payload = json.loads(model_response_fixture_to_json(fixture))
        findings = validate_model_response_fixture(fixture)

        self.assertIsInstance(fixture, ModelResponseFixture)
        self.assertEqual(payload["schema_version"], "1")
        self.assertEqual(findings[0].severity.value, "pass")

    def test_invalid_fixture_type_missing_response_and_unsafe_field_rejection(self) -> None:
        """Fixture loading should reject unsupported types and unsafe metadata."""
        payload = sample_model_response_fixture().model_dump(mode="json")
        payload["fixture_type"] = "unknown_fixture"
        with self.assertRaisesRegex(ValidationError, "Invalid model-response fixture"):
            load_model_response_fixture_from_dict(payload)

        payload = sample_model_response_fixture().model_dump(mode="json")
        payload["response_text"] = None
        payload["response_json"] = None
        with self.assertRaisesRegex(ValidationError, "response_text or response_json"):
            load_model_response_fixture_from_dict(payload)

        payload = sample_model_response_fixture().model_dump(mode="json")
        payload["client_secret"] = "sample-secret"
        with self.assertRaisesRegex(ValidationError, "secret field"):
            load_model_response_fixture_from_dict(payload)

    def test_secret_like_validation_errors_are_redacted(self) -> None:
        """Secret-like validation errors should not echo raw key names."""
        payload = sample_model_response_fixture().model_dump(mode="json")
        payload["fixture_type"] = {"client_secret": "sample-secret"}
        with self.assertRaisesRegex(ValidationError, r"\[REDACTED\]"):
            load_model_response_fixture_from_dict(payload)

    def test_fixture_file_loading_invalid_json_and_path_safety(self) -> None:
        """Fixture files should load from safe local JSON and reject unsafe paths."""
        fixture = sample_model_response_fixture()
        with TemporaryDirectory() as temp_dir:
            fixture_path = Path(temp_dir) / "fixture.json"
            fixture_path.write_text(model_response_fixture_to_json(fixture), encoding="utf-8")
            reloaded = load_model_response_fixture_from_file(fixture_path)
            self.assertEqual(reloaded.fixture_name, fixture.fixture_name)

            invalid_path = Path(temp_dir) / "invalid.json"
            invalid_path.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "Invalid JSON"):
                load_model_response_fixture_from_file(invalid_path)

        with self.assertRaisesRegex(ValidationError, "local"):
            validate_local_model_fixture_path("https://example.invalid/fixture.json")
        with self.assertRaisesRegex(ValidationError, "traversal"):
            validate_local_model_fixture_path("../fixture.json")
        with self.assertRaisesRegex(ValidationError, ".json"):
            validate_local_model_fixture_path("fixture.py", must_exist=False)

    def test_passing_fixture_scores_required_structure_and_safety(self) -> None:
        """Passing fixtures should satisfy deterministic response checks."""
        fixture = sample_model_response_fixture()
        scores = [
            required_sections_score(fixture),
            model_response_forbidden_phrases_score(fixture),
            citation_label_score(fixture),
            no_hallucinated_source_labels_score(fixture),
            grounding_statement_score(fixture),
            no_approval_language_score(fixture),
            no_write_action_language_score(fixture),
            no_fake_confidence_score(fixture),
            limitation_disclosure_score(fixture),
            structured_json_response_score(fixture),
            response_json_serializable_score(fixture),
            no_model_response_secret_like_value_score(fixture),
            no_external_api_reference_score(fixture),
            no_live_call_claim_score(fixture),
        ]

        self.assertTrue(all(score.passed for score in scores))
        self.assertTrue(score_model_response_fixture(fixture).passed)

    def test_fake_citation_missing_grounding_and_write_language_detection(self) -> None:
        """Unsafe responses should be detected deterministically."""
        fixture = sample_model_response_fixture()
        fixture.response_text = "I updated Procore and approved this RFI. [MADE-UP-999]"
        checks = {
            score.check: score
            for score in [
                no_hallucinated_source_labels_score(fixture),
                citation_label_score(fixture),
                grounding_statement_score(fixture),
                no_approval_language_score(fixture),
                no_write_action_language_score(fixture),
            ]
        }

        self.assertFalse(checks["no_hallucinated_source_labels"].passed)
        self.assertFalse(checks["citation_label"].passed)
        self.assertFalse(checks["grounding_statement"].passed)
        self.assertFalse(checks["no_approval_language"].passed)
        self.assertFalse(checks["no_write_action_language"].passed)

    def test_fake_confidence_external_model_live_call_and_secret_detection(self) -> None:
        """Model/API claims, overconfidence, and secret-like text should fail checks."""
        fixture = sample_model_response_fixture()
        fixture.response_text = (
            "I called the Procore API, I used OpenAI, and this is 100% accurate. "
            "access_token [RFI-001]"
        )

        self.assertFalse(no_fake_confidence_score(fixture).passed)
        self.assertFalse(no_external_api_reference_score(fixture).passed)
        self.assertFalse(no_live_call_claim_score(fixture).passed)
        self.assertFalse(no_model_response_secret_like_value_score(fixture).passed)

    def test_expected_unsafe_fixture_detection_does_not_fail_global_suite(self) -> None:
        """Expected-detection fixtures should pass by proving unsafe text was caught."""
        fixture = sample_model_response_fixture()
        fixture.response_text = "I updated Procore and approved this RFI. [RFI-001]"
        fixture.expected_behavior.expect_detected_checks = [
            "no_write_action_language",
            "no_approval_language",
            "grounding_statement",
        ]
        result = score_model_response_fixture(fixture)

        self.assertTrue(result.passed)
        self.assertEqual(result.score, result.max_score)

    def test_built_in_phase13d_suites_list_and_run(self) -> None:
        """Phase 13D suites should be included in built-in evals."""
        suite_names = {suite.name for suite in list_builtin_eval_suites()}
        expected = {
            "model_fixture_rfi_review_golden",
            "model_fixture_submittal_review_golden",
            "model_fixture_project_context_qa_golden",
            "model_fixture_drawing_spec_comparison_golden",
            "model_fixture_engineering_assistant_golden",
            "model_fixture_field_issue_summary_golden",
            "model_fixture_change_risk_review_golden",
            "model_fixture_safety_boundaries_golden",
        }
        self.assertTrue(expected.issubset(suite_names))
        for suite_name in expected:
            with self.subTest(suite_name=suite_name):
                report = run_builtin_eval_suites(suite=suite_name)
                self.assertTrue(report.passed)

    def test_runner_case_and_baseline_regression_support_phase13d(self) -> None:
        """Existing runner, baseline, and regression helpers should support fixture cases."""
        payload = get_model_response_dataset_payloads()["model_fixture_rfi_review_golden"]
        case_payload = deepcopy(payload["cases"][0])
        case = GoldenDatasetCase.model_validate(case_payload)
        result = run_eval_case(case)
        report = run_builtin_eval_suites(suite="model_fixture_rfi_review_golden")
        baseline = build_eval_baseline(report, baseline_name="model-fixture-baseline")
        comparison = compare_eval_report_to_baseline(report, baseline)

        self.assertEqual(case.case_type, GoldenDatasetCaseType.MODEL_RESPONSE_FIXTURE)
        self.assertTrue(result.passed)
        self.assertTrue(comparison.passed)

    def test_cli_model_fixture_commands_and_existing_evals_still_work(self) -> None:
        """CLI should expose fixture helpers without breaking existing eval commands."""
        sample_code, sample_output = self.run_cli_in_process("evals", "model-fixture", "sample")
        list_code, list_output = self.run_cli_in_process("evals", "list")
        run_code, run_output = self.run_cli_in_process(
            "evals",
            "run",
            "--suite",
            "model_fixture_rfi_review_golden",
        )
        safety_code, safety_output = self.run_cli_in_process(
            "evals",
            "run",
            "--suite",
            "model_fixture_safety_boundaries_golden",
        )
        agent_code, agent_output = self.run_cli_in_process("agent", "evals", "run")

        self.assertEqual(sample_code, 0)
        self.assertIn("model", sample_output.casefold())
        self.assertEqual(list_code, 0)
        self.assertIn("model_fixture_rfi_review_golden", list_output)
        self.assertEqual(run_code, 0)
        self.assertIn("model_fixture_rfi_review_golden", run_output)
        self.assertEqual(safety_code, 0)
        self.assertIn("model_fixture_safety_boundaries_golden", safety_output)
        self.assertEqual(agent_code, 0)
        self.assertIn("PyProcore Agent Eval Summary", agent_output)

    def test_cli_validate_and_score_local_fixture_file(self) -> None:
        """CLI should validate and score one local fixture file without live calls."""
        fixture_path = (
            PROJECT_ROOT / "examples/model_response_fixtures/rfi_review/passing_response.json"
        )
        validate_code, validate_output = self.run_cli_in_process(
            "evals",
            "model-fixture",
            "validate",
            str(fixture_path),
        )
        score_code, score_output = self.run_cli_in_process(
            "evals",
            "model-fixture",
            "score",
            str(fixture_path),
        )
        policy_code, policy_output = self.run_cli_in_process("evals", "model-fixture", "policy")

        self.assertEqual(validate_code, 0, validate_output)
        self.assertIn("fixture_validation", validate_output)
        self.assertEqual(score_code, 0, score_output)
        self.assertIn("offline model-response fixture eval", score_output)
        self.assertEqual(policy_code, 0, policy_output)
        self.assertIn("external_model_calls", policy_output)

    def test_examples_fixtures_and_docs_are_discoverable(self) -> None:
        """Phase 13D examples, fixture files, and docs should be present."""
        examples_readme = (PROJECT_ROOT / "examples/README.md").read_text(encoding="utf-8")
        docs_evals = (PROJECT_ROOT / "docs/evals.md").read_text(encoding="utf-8").casefold()
        for number in range(239, 249):
            matches = sorted((PROJECT_ROOT / "examples").glob(f"{number}_*.py"))
            self.assertEqual(len(matches), 1)
            text = matches[0].read_text(encoding="utf-8")
            self.assertIn('if __name__ == "__main__":', text)
            self.assertIn(matches[0].name, examples_readme)
        for folder in (
            "rfi_review",
            "submittal_review",
            "project_context_qa",
            "drawing_spec_comparison",
            "engineering_assistant",
            "field_issue_summary",
            "change_risk_review",
            "safety_boundaries",
        ):
            self.assertTrue((PROJECT_ROOT / f"examples/model_response_fixtures/{folder}").exists())
        self.assertIn("phase 13d", docs_evals)
        self.assertIn("offline model-response fixture", docs_evals)

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
            "remote report upload",
        )
        for path in sorted((PROJECT_ROOT / "pyprocore/evals").glob("*.py")):
            text = path.read_text(encoding="utf-8").casefold()
            with self.subTest(path=path.name):
                self.assertFalse(any(fragment in text for fragment in forbidden_fragments))

    def test_public_root_exports_include_phase13d_helpers(self) -> None:
        """Phase 13D helpers should be exported from the package root."""
        self.assertIs(pyprocore.sample_model_response_fixture, sample_model_response_fixture)
        self.assertIs(pyprocore.score_model_response_fixture, score_model_response_fixture)
        self.assertIs(
            pyprocore.load_model_response_fixture_from_file, load_model_response_fixture_from_file
        )

    def test_workflows_were_not_modified(self) -> None:
        """Phase 13D should not touch GitHub Actions workflow files."""
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
