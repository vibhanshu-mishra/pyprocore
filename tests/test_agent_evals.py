"""Tests for the local deterministic PyProcore agent eval harness."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pyprocore import __version__, app
from pyprocore.agent import (
    AgentEvalResult,
    AgentEvalSeverity,
    AgentManifest,
    AgentTool,
    export_agent_eval_results_json,
    format_agent_eval_summary,
    get_agent_eval_suite,
    get_agent_tool,
    list_agent_eval_suites,
    run_agent_eval_suite,
    run_all_agent_eval_suites,
    write_agent_eval_results,
)
from pyprocore.agent.evals import BUILT_IN_AGENT_EVAL_SUITES

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AgentEvalsTestCase(unittest.TestCase):
    """Validate local agent eval suites, CLI wiring, docs, and examples."""

    def test_builtin_eval_suites_are_registered(self) -> None:
        """All requested built-in eval suites should be listed."""
        suites = list_agent_eval_suites()
        names = [suite.name for suite in suites]

        self.assertEqual(names, BUILT_IN_AGENT_EVAL_SUITES)
        self.assertIn("registry_safety", names)
        self.assertIn("schema_quality", names)
        self.assertIn("openapi_completeness", names)
        self.assertIn("mcp_discovery", names)
        self.assertIn("run_replay_safety", names)
        self.assertIn("redaction_safety", names)
        self.assertIn("execution_disabled", names)
        self.assertTrue(all(suite.cases for suite in suites))

    def test_get_agent_eval_suite_unknown_name_fails_clearly(self) -> None:
        """Unknown suite names should fail before any eval work starts."""
        with self.assertRaisesRegex(ValueError, "Unknown agent eval suite"):
            get_agent_eval_suite("missing")

    def test_all_eval_suites_run_without_credentials(self) -> None:
        """Eval suites should not load settings or require Procore credentials."""
        with patch("pyprocore.core.config.get_settings") as get_settings:
            results = run_all_agent_eval_suites()

        get_settings.assert_not_called()
        self.assertEqual(len(results), len(BUILT_IN_AGENT_EVAL_SUITES))
        self.assertTrue(all(result.passed for result in results))
        self.assertTrue(all(result.pyprocore_version == __version__ for result in results))

    def test_each_eval_suite_can_run_by_name(self) -> None:
        """Each suite should return a structured passing result."""
        for suite_name in BUILT_IN_AGENT_EVAL_SUITES:
            with self.subTest(suite_name=suite_name):
                result = run_agent_eval_suite(suite_name)

                self.assertIsInstance(result, AgentEvalResult)
                self.assertEqual(result.suite_name, suite_name)
                self.assertTrue(result.passed)
                self.assertEqual(result.failed_cases, 0)

    def test_eval_results_json_round_trip(self) -> None:
        """Eval results should serialize as stable JSON and validate back."""
        results = run_all_agent_eval_suites()
        payload = json.loads(export_agent_eval_results_json(results, pretty=True))
        parsed = [AgentEvalResult.model_validate(item) for item in payload]

        self.assertEqual([result.suite_name for result in parsed], BUILT_IN_AGENT_EVAL_SUITES)
        self.assertTrue(all(result.findings for result in parsed))

    def test_write_agent_eval_results_creates_parent_directory(self) -> None:
        """Result writing should create output folders for beginners."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "nested" / "agent-eval-results.json"
            written = write_agent_eval_results(run_agent_eval_suite("registry_safety"), output_path)

            self.assertEqual(written, output_path)
            self.assertTrue(output_path.exists())
            self.assertIn("registry_safety", output_path.read_text(encoding="utf-8"))

    def test_eval_summary_is_markdown(self) -> None:
        """The summary helper should produce a Markdown table."""
        summary = format_agent_eval_summary(run_all_agent_eval_suites())

        self.assertIn("# PyProcore Agent Eval Summary", summary)
        self.assertIn("| Suite | Passed | Cases | Warnings |", summary)
        self.assertIn("registry_safety", summary)

    def test_redaction_and_execution_disabled_suites_cover_safety(self) -> None:
        """Safety-focused suites should contain passing findings."""
        redaction = run_agent_eval_suite("redaction_safety")
        disabled = run_agent_eval_suite("execution_disabled")

        self.assertTrue(redaction.passed)
        self.assertTrue(disabled.passed)
        self.assertEqual(redaction.findings[0].severity, AgentEvalSeverity.PASS)
        self.assertIn("redacted", redaction.findings[0].message)
        self.assertIn("no execution", disabled.findings[0].message.casefold())

    def test_cli_parser_includes_agent_eval_commands(self) -> None:
        """The CLI parser should include agent eval commands."""
        parser = app.build_parser()
        args = parser.parse_args(["agent", "evals", "run", "registry_safety", "--fail-on-warning"])

        self.assertEqual(args.command, "agent")
        self.assertEqual(args.agent_command, "evals")
        self.assertEqual(args.agent_evals_command, "run")
        self.assertEqual(args.suite_name, "registry_safety")
        self.assertTrue(args.fail_on_warning)

    def test_run_command_agent_eval_branches(self) -> None:
        """Direct CLI dispatch should cover eval list, show, and run branches."""
        parser = app.build_parser()

        suites = app.run_command(parser.parse_args(["agent", "evals", "list"]))
        suite = app.run_command(parser.parse_args(["agent", "evals", "show", "registry_safety"]))
        result = app.run_command(parser.parse_args(["agent", "evals", "run", "registry_safety"]))
        all_results = app.run_command(parser.parse_args(["agent", "evals", "run"]))

        self.assertIsInstance(suites, list)
        self.assertEqual(suite.name, "registry_safety")
        self.assertTrue(result.passed)
        self.assertEqual(len(all_results), len(BUILT_IN_AGENT_EVAL_SUITES))

    def test_run_command_agent_eval_output_file(self) -> None:
        """CLI dispatch should write eval JSON when --output is provided."""
        parser = app.build_parser()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "evals.json"
            result = app.run_command(
                parser.parse_args(
                    [
                        "agent",
                        "evals",
                        "run",
                        "registry_safety",
                        "--output",
                        str(output_path),
                    ]
                )
            )

            self.assertTrue(result.passed)
            self.assertTrue(output_path.exists())
            self.assertIn("registry_safety", output_path.read_text(encoding="utf-8"))

    def test_run_command_agent_metadata_branches(self) -> None:
        """Direct CLI dispatch should cover adjacent agent metadata branches."""
        parser = app.build_parser()
        with tempfile.TemporaryDirectory() as temp_dir:
            openapi_path = Path(temp_dir) / "agent-openapi.json"
            schemas_path = Path(temp_dir) / "agent-schemas.json"

            manifest = app.run_command(parser.parse_args(["agent", "manifest"]))
            tools = app.run_command(parser.parse_args(["agent", "tools"]))
            tool = app.run_command(parser.parse_args(["agent", "tool", "procore.find_rfi"]))
            openapi_text = app.run_command(parser.parse_args(["agent", "openapi", "--pretty"]))
            openapi_written = app.run_command(
                parser.parse_args(["agent", "openapi", "--output", str(openapi_path)])
            )
            yaml_text = app.run_command(parser.parse_args(["agent", "openapi", "--yaml"]))
            schemas_written = app.run_command(
                parser.parse_args(["agent", "schemas", "--output", str(schemas_path)])
            )

        self.assertIsInstance(manifest, AgentManifest)
        self.assertIsInstance(tools, list)
        self.assertIsInstance(tool, AgentTool)
        self.assertIn("openapi", openapi_text)
        self.assertIn("openapi", yaml_text)
        self.assertEqual(openapi_written, openapi_path)
        self.assertEqual(schemas_written, schemas_path)

    def test_agent_format_helpers_cover_human_output(self) -> None:
        """Agent formatting helpers should produce readable summaries."""
        tool = get_agent_tool("procore.find_rfi")

        self.assertIn("metadata only", app.format_agent_manifest(app.build_agent_manifest()))
        self.assertIn("No agent tools", app.format_agent_tools([]))
        self.assertIn("procore.find_rfi", app.format_agent_tool(tool))
        self.assertIn("registry_safety", app.format_agent_eval_suites(list_agent_eval_suites()))
        self.assertIn(
            "Cases:", app.format_agent_eval_suite(get_agent_eval_suite("registry_safety"))
        )
        self.assertIn(
            "Mode: local deterministic",
            app.format_agent_eval_results(run_agent_eval_suite("registry_safety")),
        )

    def test_main_agent_eval_outputs_and_exit_code(self) -> None:
        """CLI main should print eval output and exit zero when suites pass."""
        with (
            patch.object(sys, "argv", ["procore-sdk", "agent", "evals", "run", "--json"]),
            patch("builtins.print") as print_mock,
        ):
            with self.assertRaises(SystemExit) as exit_context:
                app.main()

        self.assertEqual(exit_context.exception.code, 0)
        self.assertTrue(any("registry_safety" in str(call) for call in print_mock.call_args_list))

    def test_main_agent_eval_list_show_and_output_file(self) -> None:
        """CLI main should render eval list, show, and output-file branches."""
        with (
            patch.object(sys, "argv", ["procore-sdk", "agent", "evals", "list"]),
            patch("builtins.print") as print_mock,
        ):
            app.main()

        self.assertTrue(
            any("Built-in agent eval suites" in str(call) for call in print_mock.call_args_list)
        )

        with (
            patch.object(
                sys,
                "argv",
                ["procore-sdk", "agent", "evals", "show", "registry_safety", "--json"],
            ),
            patch("builtins.print") as print_mock,
        ):
            app.main()

        self.assertTrue(any("registry_safety" in str(call) for call in print_mock.call_args_list))

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "evals.json"
            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        "procore-sdk",
                        "agent",
                        "evals",
                        "run",
                        "--output",
                        str(output_path),
                    ],
                ),
                patch("builtins.print") as print_mock,
            ):
                with self.assertRaises(SystemExit) as exit_context:
                    app.main()

            self.assertEqual(exit_context.exception.code, 0)
            self.assertTrue(output_path.exists())
            self.assertTrue(
                any("Agent eval results written" in str(call) for call in print_mock.call_args_list)
            )

    def test_main_value_error_is_friendly(self) -> None:
        """CLI main should convert eval lookup ValueError into a friendly failure."""
        with (
            patch.object(sys, "argv", ["procore-sdk", "agent", "evals", "show", "missing"]),
            patch("builtins.print") as print_mock,
        ):
            with self.assertRaises(SystemExit) as exit_context:
                app.main()

        self.assertEqual(exit_context.exception.code, 1)
        self.assertTrue(
            any("PyProcore input is invalid" in str(call) for call in print_mock.call_args_list)
        )

    def test_agent_eval_exit_code_fail_on_warning(self) -> None:
        """The CLI exit helper should honor warning failures."""
        result = run_agent_eval_suite("registry_safety")
        result.warnings = 1

        self.assertEqual(app.agent_eval_exit_code(result), 0)
        self.assertEqual(app.agent_eval_exit_code(result, fail_on_warning=True), 1)

    def test_run_agent_evals_script_writes_reports(self) -> None:
        """The helper script should write JSON and Markdown reports."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_agent_evals.py",
                    "--output-dir",
                    temp_dir,
                ],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(temp_dir) / "agent-eval-results.json").exists())
            self.assertTrue((Path(temp_dir) / "agent-eval-summary.md").exists())
            self.assertIn("no Procore or AI calls", result.stdout)

    def test_examples_docs_and_mkdocs_entries_exist(self) -> None:
        """Phase 7F examples and docs should be present."""
        self.assertTrue((PROJECT_ROOT / "examples/62_run_agent_evals.py").exists())
        self.assertTrue((PROJECT_ROOT / "examples/63_inspect_agent_eval_results.py").exists())
        self.assertTrue((PROJECT_ROOT / "docs/recipes/run-agent-evals.md").exists())
        self.assertTrue((PROJECT_ROOT / "docs/recipes/inspect-agent-eval-results.md").exists())

        mkdocs = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn("run-agent-evals.md", mkdocs)
        self.assertIn("inspect-agent-eval-results.md", mkdocs)

    def test_no_live_procore_ai_or_tool_execution_in_eval_modules(self) -> None:
        """Eval modules should avoid HTTP clients, settings, and model APIs."""
        evals_source = (PROJECT_ROOT / "pyprocore/agent/evals.py").read_text(encoding="utf-8")
        script_source = (PROJECT_ROOT / "scripts/run_agent_evals.py").read_text(encoding="utf-8")
        combined = evals_source + script_source

        self.assertNotIn("requests.", combined)
        self.assertNotIn("get_settings(", combined)
        self.assertNotIn("TokenManager", combined)
        self.assertNotIn("openai", combined.casefold())
        self.assertNotIn("anthropic", combined.casefold())
        self.assertIn("execution_disabled", combined)

    def test_version_remains_210(self) -> None:
        """Phase 7F should use the released package version."""
        self.assertEqual(__version__, "2.2.0")


if __name__ == "__main__":
    unittest.main()
