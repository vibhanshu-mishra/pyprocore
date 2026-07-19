"""Tests for Phase 15B discovery-only MCP metadata deepening."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from pyprocore import app
from pyprocore.agent import (
    build_mcp_prompt_definitions,
    build_mcp_resource_definitions,
    build_mcp_stdio_discovery,
    build_mcp_tool_execution_disabled_response,
    export_mcp_prompts_json,
    export_mcp_resources_json,
    handle_mcp_jsonrpc_request,
)
from pyprocore.mcp import (
    McpPromptKind,
    McpResourceKind,
    build_mcp_capability_summary,
    list_mcp_prompts,
    list_mcp_resources,
    read_mcp_resource_payload,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase15BMCPMetadataTestCase(unittest.TestCase):
    """Validate deeper local MCP metadata without enabling execution."""

    def test_phase15b_resource_uris_are_registered(self) -> None:
        """Phase 15B resources should be present in local discovery."""
        uris = {resource.uri for resource in list_mcp_resources()}

        expected_uris = {
            "pyprocore://evals/baseline-template",
            "pyprocore://evals/regression-template",
            "pyprocore://evals/history-template",
            "pyprocore://evals/model-fixtures",
            "pyprocore://evals/safety-boundaries",
            "pyprocore://plugins/extension-pack-template",
            "pyprocore://plugins/scaffold-template",
            "pyprocore://plugins/safety-boundaries",
            "pyprocore://plugins/capabilities",
            "pyprocore://async/resources",
            "pyprocore://async/exports",
            "pyprocore://async/batch",
            "pyprocore://async/download-patterns",
            "pyprocore://async/safety-boundaries",
            "pyprocore://async/read-only-coverage",
            "pyprocore://ai-workflows/rfi-review",
            "pyprocore://ai-workflows/project-context-qa",
            "pyprocore://ai-workflows/vector-export-pattern",
            "pyprocore://ai-workflows/model-fixture-evals",
            "pyprocore://ai-workflows/safety-boundaries",
        }

        self.assertTrue(expected_uris.issubset(uris))

    def test_dynamic_eval_and_fixture_resources_are_readable(self) -> None:
        """Per-suite eval and model fixture resources should be local JSON."""
        suite_payload = read_mcp_resource_payload(
            "pyprocore://evals/suites/golden_agent_manifest_basic"
        )
        fixture_payload = read_mcp_resource_payload(
            "pyprocore://evals/model-fixtures/model_fixture_rfi_review_golden"
        )

        self.assertEqual(suite_payload["payload"]["suite_name"], "golden_agent_manifest_basic")
        self.assertFalse(suite_payload["payload"]["execution_enabled"])
        self.assertEqual(
            fixture_payload["payload"]["fixture_suite"],
            "model_fixture_rfi_review_golden",
        )
        self.assertFalse(fixture_payload["payload"]["external_model_calls"])

    def test_resource_kind_filtering(self) -> None:
        """MCP resources should support typed and string kind filters."""
        typed = list_mcp_resources(kind=McpResourceKind.MODEL_FIXTURE)
        string = build_mcp_resource_definitions(kind="model_fixture")
        exported = json.loads(export_mcp_resources_json(kind="model_fixture"))

        self.assertGreaterEqual(len(typed), 2)
        self.assertEqual(len(string), len(exported))
        self.assertTrue(all(item["metadata"]["kind"] == "model_fixture" for item in exported))

    def test_prompt_kind_filtering(self) -> None:
        """MCP prompts should support typed and string kind filters."""
        typed = list_mcp_prompts(kind=McpPromptKind.EVAL_REPORT_REVIEW)
        string = build_mcp_prompt_definitions(kind="eval_report_review")
        exported = json.loads(export_mcp_prompts_json(kind="eval_report_review"))

        self.assertEqual([prompt.name for prompt in typed], ["eval_report_review_prompt"])
        self.assertEqual(len(string), 1)
        self.assertEqual(exported[0]["name"], "eval_report_review_prompt")

    def test_phase15b_prompts_are_registered_and_grounded(self) -> None:
        """New artifact-review prompts should be present and grounded."""
        prompts = {prompt.name: prompt for prompt in list_mcp_prompts()}
        expected_names = {
            "eval_regression_review_prompt",
            "model_fixture_review_prompt",
            "plugin_config_review_prompt",
            "extension_pack_review_prompt",
            "async_batch_plan_review_prompt",
            "async_export_manifest_review_prompt",
            "ai_workflow_package_review_prompt",
            "mcp_safety_review_prompt",
            "release_readiness_review_prompt",
        }

        self.assertTrue(expected_names.issubset(prompts))
        for name in expected_names:
            lowered = prompts[name].template.lower()
            self.assertTrue("ground" in lowered or "cite" in lowered or "source label" in lowered)
            self.assertIn("phase15b", prompts[name].tags)

    def test_capability_summary_has_phase15b_sections(self) -> None:
        """Capability summary should expose deeper Phase 15B metadata."""
        summary = build_mcp_capability_summary()

        self.assertTrue(summary.mcp_resource_metadata["supports_kind_filtering"])
        self.assertTrue(summary.mcp_prompt_metadata["supports_kind_filtering"])
        self.assertIn("baseline templates", summary.baseline_regression_metadata)
        self.assertIn("offline model-response fixture suites", summary.model_fixture_metadata)
        self.assertIn("extension pack templates", summary.plugin_scaffold_metadata)
        self.assertIn("async batch planning metadata", summary.async_metadata)
        self.assertIn("vector export patterns", summary.ai_workflow_metadata)
        self.assertFalse(summary.disabled_execution_status["mcp_tool_calls"])

    def test_stdio_discovery_includes_richer_metadata(self) -> None:
        """Stdio discovery should expose kind counts and safety summaries."""
        discovery = build_mcp_stdio_discovery()
        initialize = handle_mcp_jsonrpc_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})

        self.assertIn("resourceKindCounts", discovery)
        self.assertIn("promptKindCounts", discovery)
        self.assertIn("disabledExecutionStatus", discovery)
        self.assertIn("unsupportedActions", discovery)
        self.assertIn("model_fixture", discovery["resourceKindCounts"])
        self.assertIn("eval_regression_review", discovery["promptKindCounts"])
        self.assertFalse(
            initialize["result"]["capabilitySummary"]["safety"]["mcp_execution_enabled"]
        )

    def test_cli_kind_filters(self) -> None:
        """CLI MCP list commands should accept kind filters."""
        parser = app.build_parser()

        resources = app.run_command(parser.parse_args(["mcp", "resources", "--kind", "eval_suite"]))
        prompts = app.run_command(
            parser.parse_args(["mcp", "prompts", "--kind", "eval_report_review"])
        )
        agent_resources = app.run_command(
            parser.parse_args(["agent", "mcp", "resources", "--kind", "model_fixture"])
        )

        self.assertIn("pyprocore://evals/suites", str(resources))
        self.assertIn("eval_report_review_prompt", str(prompts))
        self.assertIn("pyprocore://evals/model-fixtures", str(agent_resources))

    def test_execution_still_disabled(self) -> None:
        """Phase 15B must not enable MCP or Procore tool execution."""
        response = build_mcp_tool_execution_disabled_response("procore.find_rfi")

        self.assertTrue(response["isError"])
        self.assertFalse(response["metadata"]["execution_enabled"])
        self.assertFalse(response["metadata"]["mcp_execution_enabled"])
        self.assertIn("no Procore API call was made", response["content"][0]["text"])

    def test_examples_docs_and_changelog_exist(self) -> None:
        """Phase 15B docs and examples should be present."""
        for number in range(259, 269):
            matches = list((PROJECT_ROOT / "examples").glob(f"{number}_*.py"))
            self.assertEqual(len(matches), 1, number)

        examples_readme = (PROJECT_ROOT / "examples/README.md").read_text(encoding="utf-8")
        docs_mcp = (PROJECT_ROOT / "docs/mcp.md").read_text(encoding="utf-8")
        changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn("259_mcp_eval_metadata_resources.py", examples_readme)
        self.assertIn("268_phase15b_mcp_metadata_summary.py", examples_readme)
        self.assertIn("Phase 15B", docs_mcp)
        self.assertIn("Phase 15B", changelog)


if __name__ == "__main__":
    unittest.main()
