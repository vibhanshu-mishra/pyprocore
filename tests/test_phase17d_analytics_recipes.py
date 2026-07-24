"""Tests for Phase 17D local project health analytics recipes."""

from __future__ import annotations

import contextlib
import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pyprocore
from pyprocore import app as cli_app
from pyprocore.analytics import (
    ProjectHealthInput,
    analytics_result_to_json,
    analytics_result_to_markdown,
    analytics_result_to_summary_dict,
    analyze_change_exposure,
    analyze_daily_log_completeness,
    analyze_rfi_aging,
    analyze_submittal_delay,
    build_project_health_report,
    load_csv_records,
    load_json_records,
    load_jsonl_records,
    load_records,
    load_records_from_path,
    run_change_exposure_recipe,
    run_daily_log_completeness_recipe,
    run_project_health_recipe,
    run_rfi_aging_recipe,
    run_submittal_delay_recipe,
    sample_analytics_data,
    write_analytics_summary_csv,
    write_sample_analytics_data,
)
from pyprocore.core.exceptions import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase17DAnalyticsRecipeTests(unittest.TestCase):
    """Validate deterministic local analytics behavior."""

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run the local CLI without credentials."""
        env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        return subprocess.run(
            [sys.executable, "-m", "pyprocore.app", *args],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_loaders_support_json_jsonl_csv_and_redact_secrets(self) -> None:
        """Local loaders should parse common export formats and redact secrets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            json_path = temp_path / "records.json"
            jsonl_path = temp_path / "records.jsonl"
            csv_path = temp_path / "records.csv"
            json_path.write_text(
                json.dumps({"records": [{"id": 1, "access_token": "secret"}]}),
                encoding="utf-8",
            )
            jsonl_path.write_text(
                json.dumps({"id": 2, "note": "Bearer abc def"}) + "\n",
                encoding="utf-8",
            )
            with csv_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["id", "client_secret"])
                writer.writeheader()
                writer.writerow({"id": "3", "client_secret": "secret"})

            self.assertEqual(load_json_records(json_path)[0]["access_token"], "[REDACTED]")
            self.assertEqual(load_jsonl_records(jsonl_path)[0]["note"], "Bearer [REDACTED] def")
            self.assertEqual(load_csv_records(csv_path)[0]["client_secret"], "[REDACTED]")
            self.assertEqual(load_records({"id": 4})[0]["id"], 4)
            self.assertEqual(load_records_from_path(csv_path)[0]["id"], "3")
            with self.assertRaisesRegex(ValidationError, "Unsupported analytics file type"):
                load_records_from_path(temp_path / "records.txt")

    def test_rfi_aging_recipe_scores_overdue_open_items(self) -> None:
        """RFI aging should produce review findings for overdue open RFIs."""
        summary = analyze_rfi_aging(
            [
                {
                    "id": 1,
                    "number": "15",
                    "status": "Open",
                    "created_at": "2026-01-01",
                    "due_date": "2026-01-15",
                },
                {"id": 2, "status": "Closed", "created_at": "2026-01-10"},
            ],
            today=date(2026, 2, 15),
        )

        self.assertEqual(summary.open_count, 1)
        self.assertEqual(summary.overdue_count, 1)
        self.assertGreater(summary.risk_score, 50)
        self.assertTrue(any("RFI 15" in finding.title for finding in summary.findings))

    def test_submittal_delay_recipe_scores_overdue_and_due_soon(self) -> None:
        """Submittal delay should identify overdue and due-soon pending records."""
        summary = analyze_submittal_delay(
            [
                {"id": 1, "number": "27", "status": "Pending", "due_date": "2026-02-01"},
                {"id": 2, "number": "28", "status": "Open", "due_date": "2026-02-20"},
                {"id": 3, "number": "29", "status": "Approved", "due_date": "2026-02-02"},
            ],
            today=date(2026, 2, 15),
        )

        self.assertEqual(summary.pending_count, 2)
        self.assertEqual(summary.overdue_count, 1)
        self.assertEqual(summary.due_soon_count, 1)
        self.assertGreater(summary.average_days_overdue, 0)

    def test_change_exposure_recipe_summarizes_status_buckets(self) -> None:
        """Change exposure should separate open, approved, and rejected values."""
        summary = analyze_change_exposure(
            [
                {"id": 1, "status": "Open", "estimated_exposure": "$42,000.00"},
                {"id": 2, "status": "Approved", "amount": 18000},
                {"id": 3, "status": "Rejected", "amount": 5000},
            ]
        )

        self.assertEqual(summary.total_estimated_exposure, 65000)
        self.assertEqual(summary.open_exposure, 42000)
        self.assertEqual(summary.approved_exposure, 18000)
        self.assertEqual(summary.rejected_or_void_exposure, 5000)
        self.assertEqual(summary.count_by_status["open"], 1)

    def test_daily_log_completeness_recipe_finds_missing_days(self) -> None:
        """Daily log completeness should compare records to an expected date range."""
        summary = analyze_daily_log_completeness(
            [{"date": "2026-06-01"}, {"log_date": "2026-06-03"}],
            start_date="2026-06-01",
            end_date="2026-06-04",
        )

        self.assertEqual(summary.expected_date_count, 4)
        self.assertEqual(summary.days_with_logs, 2)
        self.assertEqual(summary.missing_days, ["2026-06-02", "2026-06-04"])
        self.assertEqual(summary.completeness_percentage, 50)

    def test_combined_project_health_normalizes_missing_components(self) -> None:
        """Combined health scoring should normalize weights across available inputs."""
        report = build_project_health_report(
            ProjectHealthInput(
                rfis=[
                    {
                        "id": 1,
                        "status": "Open",
                        "created_at": "2026-01-01",
                        "due_date": "2026-01-10",
                    }
                ],
                changes=[{"id": 2, "status": "Open", "estimated_exposure": 10000}],
            ),
            today=date(2026, 2, 15),
        )

        self.assertEqual(set(report.component_scores), {"rfi_aging", "change_exposure"})
        self.assertAlmostEqual(sum(report.component_weights.values()), 1.0, places=3)
        self.assertGreater(report.overall_score, 0)
        self.assertFalse(report.procore_api_call_required)
        self.assertFalse(report.external_ai_call_required)
        self.assertFalse(report.write_actions_enabled)

    def test_reports_render_json_markdown_summary_and_csv(self) -> None:
        """Analytics reports should serialize without live services."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "rfis.json"
            csv_path = Path(temp_dir) / "summary.csv"
            data_path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "status": "Open",
                            "created_at": "2026-01-01",
                            "due_date": "2026-01-10",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            result = run_rfi_aging_recipe(data_path)
            payload = json.loads(analytics_result_to_json(result, pretty=True))
            markdown = analytics_result_to_markdown(result)
            compact = analytics_result_to_summary_dict(result)
            written = write_analytics_summary_csv([result], csv_path)

            self.assertEqual(payload["recipe"], "rfi_aging")
            self.assertIn("Procore API calls made: false", markdown)
            self.assertEqual(compact["recipe"], "rfi_aging")
            self.assertTrue(written.exists())

    def test_all_recipe_markdown_branches_render(self) -> None:
        """Every analytics recipe summary type should have a Markdown branch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = write_sample_analytics_data(temp_dir)
            path_by_name = {path.name: path for path in paths}
            results = [
                run_submittal_delay_recipe(path_by_name["fake_submittals.json"]),
                run_change_exposure_recipe(path_by_name["fake_changes.json"]),
                run_daily_log_completeness_recipe(
                    path_by_name["fake_daily_logs.json"],
                    start_date="2026-06-01",
                    end_date="2026-06-05",
                ),
                run_project_health_recipe(
                    rfis_path=path_by_name["fake_rfis.json"],
                    submittals_path=path_by_name["fake_submittals.json"],
                    changes_path=path_by_name["fake_changes.json"],
                    daily_logs_path=path_by_name["fake_daily_logs.json"],
                    start_date="2026-06-01",
                    end_date="2026-06-05",
                ),
            ]
            markdown = "\n".join(analytics_result_to_markdown(result) for result in results)

            self.assertIn("Pending submittals", markdown)
            self.assertIn("Total estimated exposure", markdown)
            self.assertIn("Completeness percentage", markdown)
            self.assertIn("Component Scores", markdown)
            self.assertIn("Recommended Next Reviews", markdown)
            self.assertIn("Procore write actions performed: false", markdown)
            self.assertIn("rfis", sample_analytics_data())

    def test_project_health_recipe_loads_local_files(self) -> None:
        """Combined recipe should load local files and remain read-only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = write_sample_analytics_data(temp_dir)
            path_by_name = {path.name: path for path in paths}
            result = run_project_health_recipe(
                rfis_path=path_by_name["fake_rfis.json"],
                submittals_path=path_by_name["fake_submittals.json"],
                changes_path=path_by_name["fake_changes.json"],
                daily_logs_path=path_by_name["fake_daily_logs.json"],
                start_date="2026-06-01",
                end_date="2026-06-05",
            )

            self.assertEqual(result.recipe, "project_health")
            self.assertIn("rfi_aging", result.summary.component_scores)
            self.assertFalse(result.procore_api_call_required)

    def test_cli_analytics_commands_work_without_credentials(self) -> None:
        """Analytics CLI commands should run against local fake files only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sample_result = self.run_cli(
                "analytics", "sample-data", "--output-dir", temp_dir, "--json"
            )
            self.assertEqual(sample_result.returncode, 0, sample_result.stderr)
            payload = json.loads(sample_result.stdout)
            self.assertFalse(payload["procore_api_call_required"])
            data_dir = Path(temp_dir)
            commands = [
                ("analytics", "rfi-aging", str(data_dir / "fake_rfis.json"), "--format", "json"),
                (
                    "analytics",
                    "submittal-delay",
                    str(data_dir / "fake_submittals.json"),
                    "--format",
                    "json",
                ),
                (
                    "analytics",
                    "change-exposure",
                    str(data_dir / "fake_changes.json"),
                    "--format",
                    "json",
                ),
                (
                    "analytics",
                    "daily-log-completeness",
                    str(data_dir / "fake_daily_logs.json"),
                    "--start-date",
                    "2026-06-01",
                    "--end-date",
                    "2026-06-05",
                    "--format",
                    "json",
                ),
                (
                    "analytics",
                    "project-health",
                    "--rfis",
                    str(data_dir / "fake_rfis.json"),
                    "--submittals",
                    str(data_dir / "fake_submittals.json"),
                    "--changes",
                    str(data_dir / "fake_changes.json"),
                    "--daily-logs",
                    str(data_dir / "fake_daily_logs.json"),
                    "--start-date",
                    "2026-06-01",
                    "--end-date",
                    "2026-06-05",
                    "--format",
                    "json",
                ),
            ]
            results = [self.run_cli(*command) for command in commands]

            for completed in results:
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertFalse(json.loads(completed.stdout)["procore_api_call_required"])

    def test_cli_main_analytics_commands_render_in_process(self) -> None:
        """Analytics CLI commands should render in-process without credentials."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            sample_output = self.run_main(
                "analytics",
                "sample-data",
                "--output-dir",
                str(data_dir),
            )
            self.assertIn("Analytics sample data written", sample_output)
            command_outputs = [
                self.run_main(
                    "analytics",
                    "rfi-aging",
                    str(data_dir / "fake_rfis.json"),
                    "--format",
                    "markdown",
                ),
                self.run_main(
                    "analytics",
                    "submittal-delay",
                    str(data_dir / "fake_submittals.json"),
                    "--format",
                    "json",
                ),
                self.run_main(
                    "analytics",
                    "change-exposure",
                    str(data_dir / "fake_changes.json"),
                    "--format",
                    "markdown",
                ),
                self.run_main(
                    "analytics",
                    "daily-log-completeness",
                    str(data_dir / "fake_daily_logs.json"),
                    "--start-date",
                    "2026-06-01",
                    "--end-date",
                    "2026-06-05",
                    "--json",
                ),
                self.run_main(
                    "analytics",
                    "project-health",
                    "--rfis",
                    str(data_dir / "fake_rfis.json"),
                    "--submittals",
                    str(data_dir / "fake_submittals.json"),
                    "--changes",
                    str(data_dir / "fake_changes.json"),
                    "--daily-logs",
                    str(data_dir / "fake_daily_logs.json"),
                    "--start-date",
                    "2026-06-01",
                    "--end-date",
                    "2026-06-05",
                    "--format",
                    "markdown",
                ),
            ]

            joined = "\n".join(command_outputs)
            self.assertIn("Rfi Aging Analytics Report", joined)
            self.assertIn('"recipe": "submittal_delay"', joined)
            self.assertIn("Change Exposure Analytics Report", joined)
            self.assertIn('"recipe": "daily_log_completeness"', joined)
            self.assertIn("Project Health Analytics Report", joined)

    def run_main(self, *args: str) -> str:
        """Run the CLI main function in-process and capture stdout."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            with patch.object(sys, "argv", ["procore-sdk", *args]):
                cli_app.main()
        return output.getvalue()

    def test_root_exports_and_source_safety_boundaries(self) -> None:
        """Analytics package should not include network, DB, AI, MCP, or write execution."""
        self.assertTrue(hasattr(pyprocore, "run_project_health_recipe"))
        analytics_files = sorted((PROJECT_ROOT / "pyprocore" / "analytics").glob("*.py"))
        forbidden_snippets = [
            "import requests",
            "from requests",
            "import httpx",
            "from httpx",
            "import urllib.request",
            "from urllib",
            "api.procore.com",
            "procore.com/rest",
            "openai",
            "anthropic",
            "sklearn",
            "pandas",
            "numpy",
            "matplotlib",
            "plotly",
            "fastapi",
            "flask",
            "django",
            "sqlalchemy",
            "psycopg",
            "redis",
            "mcp",
            "subprocess",
            "exec(",
            "eval(",
            ".post(",
            ".put(",
            ".delete(",
        ]
        for path in analytics_files:
            source = path.read_text(encoding="utf-8").casefold()
            for snippet in forbidden_snippets:
                self.assertNotIn(snippet.casefold(), source, f"{snippet} found in {path}")

    def test_docs_and_examples_describe_local_only_phase17d(self) -> None:
        """Docs and examples should advertise analytics without weakening safety boundaries."""
        expected_examples = [
            "296_project_health_sample_data.py",
            "297_rfi_aging_risk_report.py",
            "298_submittal_delay_report.py",
            "299_change_exposure_summary.py",
            "300_combined_project_health_report.py",
        ]
        for example_name in expected_examples:
            self.assertTrue((PROJECT_ROOT / "examples" / example_name).exists())

        docs = (PROJECT_ROOT / "docs" / "analytics-recipes.md").read_text(encoding="utf-8")
        cli_docs = (PROJECT_ROOT / "docs" / "cli.md").read_text(encoding="utf-8")
        examples = (PROJECT_ROOT / "examples" / "README.md").read_text(encoding="utf-8")
        mkdocs = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        joined = "\n".join([docs, cli_docs, examples])

        self.assertIn("analytics-recipes.md", mkdocs)
        self.assertIn("Phase 17D", joined)
        self.assertIn("local project health analytics", joined)
        self.assertIn("No Procore API calls", docs)
        self.assertIn("No external AI/model calls", docs)
        self.assertIn("No MCP execution", docs)
        self.assertIn("No Procore tool execution", docs)
        self.assertIn("No hosted dashboard", docs)
        self.assertIn("No pandas", docs)
        self.assertIn("No create, update, delete, upload, approve, submit, payment", docs)
        self.assertIn("Examples `296` through `300`", examples)


if __name__ == "__main__":
    unittest.main()
