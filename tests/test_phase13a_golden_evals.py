"""Tests for Phase 13A local deterministic golden evals."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pyprocore
from pyprocore import app
from pyprocore.core.exceptions import ValidationError
from pyprocore.evals import (
    DATASET_SCHEMA_VERSION,
    EvalReport,
    EvalSeverity,
    EvalStatus,
    GoldenDataset,
    GoldenDatasetCaseType,
    contains_text_score,
    does_not_contain_text_score,
    eval_report_to_json,
    eval_report_to_markdown,
    exact_match_score,
    forbidden_keys_score,
    get_builtin_dataset,
    golden_dataset_to_json,
    json_serializable_score,
    list_builtin_dataset_names,
    list_builtin_eval_suites,
    load_golden_dataset_from_dict,
    load_golden_dataset_from_file,
    manifest_integrity_score,
    redaction_score,
    required_keys_score,
    required_values_score,
    row_count_score,
    run_builtin_eval_suites,
    run_eval_case,
    run_golden_dataset_file,
    safety_boundary_score,
    sample_eval_report,
    sample_golden_dataset,
    schema_shape_score,
    validate_golden_dataset,
    write_eval_report_json,
    write_eval_report_markdown,
)
from pyprocore.evals.datasets import _validate_local_json_path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase13AGoldenEvalsTestCase(unittest.TestCase):
    """Validate golden datasets, scoring, reports, CLI wiring, and safety."""

    def run_cli_in_process(self, *args: str) -> tuple[int, str]:
        """Run the CLI in-process so output branches count in coverage."""
        output = StringIO()
        with patch.object(sys, "argv", ["procore-sdk", *args]), redirect_stdout(output):
            try:
                app.main()
            except SystemExit as exc:
                code = int(exc.code) if isinstance(exc.code, int) else 1
            else:
                code = 0
        return code, output.getvalue()

    def write_dataset(self, directory: Path, name: str, payload: dict[str, object]) -> Path:
        """Write one JSON dataset under a temporary directory."""
        path = directory / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_dataset_models_construct_and_serialize(self) -> None:
        """Golden dataset models should be typed and JSON-serializable."""
        dataset = sample_golden_dataset()
        payload = json.loads(golden_dataset_to_json(dataset))

        self.assertIsInstance(dataset, GoldenDataset)
        self.assertEqual(dataset.schema_version, DATASET_SCHEMA_VERSION)
        self.assertEqual(dataset.cases[0].case_type, GoldenDatasetCaseType.EXPORT_ROWS)
        self.assertEqual(payload["schema_version"], "1")
        self.assertEqual(pyprocore.GoldenDataset, GoldenDataset)

    def test_invalid_version_case_type_and_empty_cases_are_rejected(self) -> None:
        """Dataset loading should reject unsupported schema, case types, and empty suites."""
        valid = sample_golden_dataset().model_dump(mode="json")
        invalid_version = {**valid, "schema_version": "2"}
        invalid_case_type = json.loads(json.dumps(valid))
        invalid_case_type["cases"][0]["case_type"] = "unsafe_case_type"
        empty_cases = {**valid, "cases": []}

        with self.assertRaisesRegex(ValidationError, "Invalid golden dataset"):
            load_golden_dataset_from_dict(invalid_version)
        with self.assertRaisesRegex(ValidationError, "Invalid golden dataset"):
            load_golden_dataset_from_dict(invalid_case_type)
        with self.assertRaisesRegex(ValidationError, "at least one case"):
            load_golden_dataset_from_dict(empty_cases)

    def test_unsafe_dataset_text_is_rejected_and_redacted(self) -> None:
        """Unsafe or secret-like dataset values should fail without leaking raw values."""
        payload = sample_golden_dataset().model_dump(mode="json")
        payload["cases"][0]["description"] = "client_secret=super-secret-value"

        with self.assertRaises(ValidationError) as context:
            load_golden_dataset_from_dict(payload)

        message = str(context.exception)
        self.assertIn("[REDACTED]", message)
        self.assertNotIn("super-secret-value", message)

    def test_local_json_loading_and_invalid_json_handling(self) -> None:
        """Dataset file loading should accept local JSON and reject invalid JSON."""
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            good_path = self.write_dataset(
                directory,
                "dataset.json",
                sample_golden_dataset().model_dump(mode="json"),
            )
            bad_path = directory / "bad.json"
            bad_path.write_text("{not json", encoding="utf-8")

            loaded = load_golden_dataset_from_file(good_path)

            self.assertEqual(loaded.metadata.name, "sample_golden_dataset")
            with self.assertRaisesRegex(ValidationError, "Invalid JSON"):
                load_golden_dataset_from_file(bad_path)

    def test_dataset_path_safety_rejects_remote_traversal_and_non_json(self) -> None:
        """Dataset loading should only accept safe local JSON files."""
        with self.assertRaisesRegex(ValidationError, "local JSON file"):
            _validate_local_json_path("https://example.invalid/dataset.json")
        with self.assertRaisesRegex(ValidationError, "path traversal"):
            _validate_local_json_path("../dataset.json")
        with tempfile.TemporaryDirectory() as raw_directory:
            txt_path = Path(raw_directory) / "dataset.txt"
            txt_path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "end with .json"):
                load_golden_dataset_from_file(txt_path)

    def test_scoring_helpers_cover_success_and_failure_cases(self) -> None:
        """Deterministic scoring helpers should pass and fail predictably."""
        artifact = {"id": "sample-1", "nested": {"name": "RFI"}, "rows": [{"id": "a"}]}

        self.assertTrue(exact_match_score(artifact["id"], "sample-1").passed)
        self.assertFalse(exact_match_score(artifact["id"], "sample-2").passed)
        self.assertTrue(required_keys_score(artifact, ["id", "nested.name"]).passed)
        self.assertFalse(required_keys_score(artifact, ["missing"]).passed)
        self.assertTrue(schema_shape_score(artifact, ["rows.0.id"]).passed)
        self.assertTrue(forbidden_keys_score(artifact, ["token"]).passed)
        self.assertFalse(forbidden_keys_score({"token": "x"}, ["token"]).passed)
        self.assertTrue(contains_text_score("local deterministic", ["deterministic"]).passed)
        self.assertFalse(contains_text_score("local deterministic", ["remote"]).passed)
        self.assertTrue(does_not_contain_text_score("safe text", ["secret"]).passed)
        self.assertFalse(does_not_contain_text_score("unsafe secret", ["secret"]).passed)
        self.assertTrue(json_serializable_score(artifact).passed)
        self.assertFalse(json_serializable_score({"bad": object()}).passed)
        self.assertTrue(redaction_score({"value": "placeholder"}).passed)
        self.assertFalse(redaction_score({"access_token": "placeholder"}).passed)
        self.assertTrue(row_count_score([{"id": 1}], 1).passed)
        self.assertFalse(row_count_score({"id": 1}, 1).passed)
        self.assertTrue(manifest_integrity_score({"name": "x", "version": "1"}, ["version"]).passed)
        self.assertFalse(manifest_integrity_score({"version": "1"}, ["version"]).passed)
        self.assertTrue(
            required_values_score({"safety": {"enabled": False}}, {"safety.enabled": False}).passed
        )
        self.assertFalse(
            required_values_score({"safety": {"enabled": True}}, {"safety.enabled": False}).passed
        )

    def test_safety_boundary_score_redacts_secret_like_fragments(self) -> None:
        """Safety boundary findings should redact unsafe secret-like fragments."""
        score = safety_boundary_score({"client_secret": "raw-value"})
        details = score.findings[0].details

        self.assertFalse(score.passed)
        self.assertIn("[REDACTED]", details["unsafe_fragments"])
        self.assertNotIn("raw-value", json.dumps(details))

    def test_builtin_dataset_listing_and_running(self) -> None:
        """Built-in suites should run locally with deterministic totals."""
        names = list_builtin_dataset_names()
        suites = list_builtin_eval_suites()
        report = run_builtin_eval_suites()
        single = run_builtin_eval_suites("golden_export_rows_basic")

        self.assertGreaterEqual(len(names), 7)
        self.assertIn("golden_export_rows_basic", names)
        self.assertEqual([suite.name for suite in suites], names)
        self.assertTrue(report.passed)
        self.assertEqual(report.status, EvalStatus.PASS)
        self.assertGreaterEqual(report.total_suites, 7)
        self.assertGreaterEqual(report.total_cases, 7)
        self.assertEqual(report.score, report.max_score)
        self.assertEqual(single.total_suites, 1)
        self.assertEqual(single.suites[0].suite_name, "golden_export_rows_basic")
        with self.assertRaisesRegex(ValueError, "Unknown built-in"):
            get_builtin_dataset("missing")

    def test_eval_case_failure_counts_are_reported(self) -> None:
        """A failing case should produce a failed result and useful findings."""
        dataset = load_golden_dataset_from_dict(
            {
                "schema_version": "1",
                "metadata": {
                    "name": "failing_dataset",
                    "description": "Intentional local failure.",
                },
                "cases": [
                    {
                        "id": "missing_required_key",
                        "case_type": "export_rows",
                        "description": "Fail when required key is absent.",
                        "input": {"artifact": [{"id": "sample"}]},
                        "expected": {"required_keys": ["0.title"]},
                    }
                ],
            }
        )

        case_result = run_eval_case(dataset.cases[0])
        report = run_golden_dataset_file(self._write_temp_dataset(dataset))

        self.assertFalse(case_result.passed)
        self.assertEqual(case_result.status, EvalStatus.FAIL)
        self.assertTrue(
            any(finding.severity == EvalSeverity.FAILURE for finding in case_result.findings)
        )
        self.assertFalse(report.passed)
        self.assertEqual(report.failed_cases, 1)

    def test_report_json_markdown_and_output_path_safety(self) -> None:
        """Reports should serialize and write only to safe local paths."""
        report = sample_eval_report()

        json_payload = json.loads(eval_report_to_json(report))
        markdown = eval_report_to_markdown(report)

        self.assertIsInstance(report, EvalReport)
        self.assertEqual(json_payload["mode"], "local_deterministic")
        self.assertIn("# PyProcore Golden Eval Report", markdown)
        self.assertIn("no Procore, model, plugin, MCP, or tool execution", markdown)

        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            json_path = write_eval_report_json(report, directory / "report.json")
            md_path = write_eval_report_markdown(report, directory / "report.md")
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

        with self.assertRaisesRegex(ValidationError, "local"):
            write_eval_report_json(report, "https://example.invalid/report.json")
        with self.assertRaisesRegex(ValidationError, "path traversal"):
            write_eval_report_markdown(report, "../report.md")
        with self.assertRaisesRegex(ValidationError, "end with .json"):
            write_eval_report_json(report, "report.md")

    def test_cli_parser_and_run_command_cover_eval_branches(self) -> None:
        """Direct CLI dispatch should cover eval list/run/report/sample branches."""
        parser = app.build_parser()
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            dataset_path = self.write_dataset(
                directory,
                "dataset.json",
                sample_golden_dataset().model_dump(mode="json"),
            )
            json_output = directory / "report.json"
            md_output = directory / "report.md"

            suites = app.run_command(parser.parse_args(["evals", "list"]))
            report = app.run_command(parser.parse_args(["evals", "run"]))
            suite_report = app.run_command(
                parser.parse_args(["evals", "run", "--suite", "golden_export_rows_basic"])
            )
            dataset_report = app.run_command(
                parser.parse_args(["evals", "run", "--dataset", str(dataset_path)])
            )
            findings = app.run_command(
                parser.parse_args(["evals", "validate-dataset", str(dataset_path)])
            )
            written_json_report = app.run_command(
                parser.parse_args(
                    [
                        "evals",
                        "report",
                        "--suite",
                        "golden_export_rows_basic",
                        "--format",
                        "json",
                        "--output",
                        str(json_output),
                    ]
                )
            )
            written_md_report = app.run_command(
                parser.parse_args(
                    [
                        "evals",
                        "run",
                        "--suite",
                        "golden_export_rows_basic",
                        "--format",
                        "markdown",
                        "--output",
                        str(md_output),
                    ]
                )
            )
            sample_dataset = app.run_command(parser.parse_args(["evals", "sample-dataset"]))
            sample_report = app.run_command(parser.parse_args(["evals", "sample-report"]))

            if isinstance(written_json_report, EvalReport):
                write_eval_report_json(written_json_report, json_output)
            if isinstance(written_md_report, EvalReport):
                write_eval_report_markdown(written_md_report, md_output)

            self.assertIsInstance(suites, list)
            self.assertTrue(report.passed)
            self.assertEqual(suite_report.total_suites, 1)
            self.assertTrue(dataset_report.passed)
            self.assertTrue(any(finding.severity == EvalSeverity.PASS for finding in findings))
            self.assertIsInstance(sample_dataset, GoldenDataset)
            self.assertIsInstance(sample_report, EvalReport)
            self.assertTrue(json_output.exists())
            self.assertTrue(md_output.exists())

    def test_cli_main_eval_commands_render_without_credentials(self) -> None:
        """CLI main should render eval commands and preserve agent eval behavior."""
        commands = [
            ("evals", "list"),
            ("evals", "run"),
            ("evals", "sample-dataset"),
            ("evals", "sample-report"),
            ("agent", "evals", "run", "registry_safety"),
        ]
        for command in commands:
            with self.subTest(command=command):
                code, output = self.run_cli_in_process(*command)
                self.assertEqual(code, 0, output)
                self.assertNotIn("Traceback", output)

    def test_cli_main_validate_dataset_and_report_outputs(self) -> None:
        """CLI main should validate local datasets and write explicit reports."""
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            dataset_path = self.write_dataset(
                directory,
                "dataset.json",
                sample_golden_dataset().model_dump(mode="json"),
            )
            output_path = directory / "report.json"

            validate_code, validate_output = self.run_cli_in_process(
                "evals", "validate-dataset", str(dataset_path)
            )
            report_code, report_output = self.run_cli_in_process(
                "evals",
                "report",
                "--dataset",
                str(dataset_path),
                "--format",
                "json",
                "--output",
                str(output_path),
            )

            self.assertEqual(validate_code, 0, validate_output)
            self.assertIn("Golden dataset is valid", validate_output)
            self.assertEqual(report_code, 0, report_output)
            self.assertTrue(output_path.exists())

    def test_builtin_evals_do_not_load_settings_or_live_clients(self) -> None:
        """Built-in evals should not load Procore config or make live calls."""
        with patch("pyprocore.core.config.get_settings") as get_settings:
            report = run_builtin_eval_suites()

        get_settings.assert_not_called()
        self.assertTrue(report.passed)

    def test_examples_and_golden_dataset_files_are_discoverable(self) -> None:
        """Phase 13A examples and sample datasets should be documented and safe."""
        examples_readme = (PROJECT_ROOT / "examples" / "README.md").read_text(encoding="utf-8")
        dataset_dir = PROJECT_ROOT / "examples" / "golden_datasets"

        self.assertIn("Examples `209` through `218`", examples_readme)
        self.assertIn("examples/golden_datasets", examples_readme)
        for number in range(209, 219):
            matches = sorted((PROJECT_ROOT / "examples").glob(f"{number}_*.py"))
            self.assertEqual(len(matches), 1, f"Missing example {number}")
            source = matches[0].read_text(encoding="utf-8")
            self.assertIn('if __name__ == "__main__":', source)

        for dataset_file in sorted(dataset_dir.glob("*.json")):
            with self.subTest(dataset_file=dataset_file.name):
                dataset = load_golden_dataset_from_file(dataset_file)
                self.assertTrue(validate_golden_dataset(dataset))

    def test_docs_and_package_exports_cover_phase13a(self) -> None:
        """Docs and root package exports should mention Phase 13A evals."""
        docs = "\n".join(
            [
                (PROJECT_ROOT / "README.md").read_text(encoding="utf-8"),
                (PROJECT_ROOT / "docs" / "evals.md").read_text(encoding="utf-8"),
                (PROJECT_ROOT / "docs" / "cli.md").read_text(encoding="utf-8"),
                (PROJECT_ROOT / "docs" / "roadmap.md").read_text(encoding="utf-8"),
                (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
            ]
        )

        self.assertIn("Phase 13A", docs)
        self.assertIn("procore-sdk evals run", docs)
        self.assertIn("Golden Evals", (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
        self.assertTrue(callable(pyprocore.run_builtin_eval_suites))
        self.assertEqual(pyprocore.__version__, "2.2.0")

    def test_phase13a_safety_boundaries_remain_closed(self) -> None:
        """Eval implementation should not add unsafe execution or workflow changes."""
        eval_sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((PROJECT_ROOT / "pyprocore" / "evals").glob("*.py"))
        ).casefold()

        for fragment in ("subprocess", "importlib", "eval(", "exec(", "pip install"):
            self.assertNotIn(fragment, eval_sources)
        self.assertIn(
            '"tool_execution_enabled": False',
            (PROJECT_ROOT / "pyprocore" / "agent" / "openapi.py").read_text(encoding="utf-8"),
        )

    def _write_temp_dataset(self, dataset: GoldenDataset) -> Path:
        """Write a dataset to a named temporary file and return its path."""
        temp_file = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        with temp_file:
            temp_file.write(golden_dataset_to_json(dataset))
        self.addCleanup(lambda: Path(temp_file.name).unlink(missing_ok=True))
        return Path(temp_file.name)


if __name__ == "__main__":
    unittest.main()
