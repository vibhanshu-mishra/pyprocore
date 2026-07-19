"""Tests for Phase 15A richer discovery-only MCP metadata."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from pyprocore import __version__, app
from pyprocore.agent import (
    build_mcp_capability_definitions,
    build_mcp_prompt_definitions,
    build_mcp_resource_definitions,
    build_mcp_safety_boundaries,
    build_mcp_stdio_discovery,
    build_mcp_tool_execution_disabled_response,
    export_mcp_capabilities_json,
    export_mcp_manifest_json,
    export_mcp_prompts_json,
    export_mcp_resources_json,
    export_mcp_safety_json,
    handle_mcp_jsonrpc_request,
    read_mcp_prompt,
)
from pyprocore.mcp import (
    McpPrompt,
    McpPromptKind,
    McpResource,
    McpResourceKind,
    build_mcp_capability_summary,
    build_mcp_discovery_manifest,
    disabled_mcp_execution_response,
    get_mcp_prompt,
    get_mcp_resource,
    list_mcp_prompts,
    list_mcp_resources,
    read_mcp_resource_payload,
    safe_mcp_prompt_not_found,
    safe_mcp_resource_not_found,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase15AMCPDiscoveryTestCase(unittest.TestCase):
    """Validate richer MCP discovery while keeping execution disabled."""

    def test_mcp_resource_model_construction(self) -> None:
        """Resource metadata should be typed and JSON-serializable."""
        resource = McpResource(
            uri="pyprocore://docs/index",
            name="Docs",
            description="Local docs metadata.",
            kind=McpResourceKind.DOCS_REFERENCE,
        )

        self.assertEqual(resource.kind, McpResourceKind.DOCS_REFERENCE)
        self.assertTrue(resource.safety.discovery_only)
        self.assertFalse(resource.safety.calls_live_procore_api)
        json.dumps(resource.model_dump(mode="json"))

    def test_mcp_prompt_model_construction(self) -> None:
        """Prompt metadata should be typed and JSON-serializable."""
        prompt = get_mcp_prompt("rfi_review_prompt")

        self.assertIsInstance(prompt, McpPrompt)
        self.assertEqual(prompt.kind, McpPromptKind.RFI_REVIEW)
        self.assertIn("Ground", prompt.template)
        json.dumps(prompt.model_dump(mode="json"))

    def test_capability_summary_construction(self) -> None:
        """Capability summaries should mark execution as disabled."""
        summary = build_mcp_capability_summary()

        self.assertEqual(summary.package_version, "2.2.0")
        self.assertGreater(summary.resource_count, 10)
        self.assertGreater(summary.prompt_count, 5)
        self.assertFalse(summary.safety.mcp_execution_enabled)
        self.assertFalse(summary.safety.procore_tool_execution_enabled)
        self.assertFalse(summary.safety.calls_live_procore_api)

    def test_list_and_read_known_resources(self) -> None:
        """Known resource reads should return local JSON text only."""
        resources = list_mcp_resources()
        uris = {resource.uri for resource in resources}

        self.assertIn("pyprocore://agent/manifest", uris)
        self.assertIn("pyprocore://evals/suites", uris)
        self.assertIn("pyprocore://plugins/manifest", uris)
        self.assertIn("pyprocore://async/capabilities", uris)
        self.assertIn("pyprocore://ai-workflows/templates", uris)
        self.assertIn("pyprocore://safety/boundaries", uris)

        resource = get_mcp_resource("pyprocore://evals/suites")
        text = resource["contents"][0]["text"]
        payload = json.loads(text)
        self.assertEqual(payload["payload"]["mode"], "local_deterministic")

    def test_unknown_resource_safe_not_found(self) -> None:
        """Unknown resources should have safe not-found metadata."""
        response = safe_mcp_resource_not_found("pyprocore://missing")

        self.assertTrue(response["isError"])
        self.assertEqual(response["error"], "resource_not_found")
        self.assertFalse(response["safety"]["mcp_execution_enabled"])
        with self.assertRaises(FileNotFoundError):
            read_mcp_resource_payload("pyprocore://missing")

    def test_list_and_read_known_prompts(self) -> None:
        """Prompt discovery should expose grounded templates."""
        prompts = list_mcp_prompts()
        names = {prompt.name for prompt in prompts}

        self.assertIn("rfi_review_prompt", names)
        self.assertIn("submittal_review_prompt", names)
        self.assertIn("engineering_assistant_prompt", names)

        prompt = read_mcp_prompt("rfi_review_prompt")
        self.assertIn("messages", prompt)
        self.assertIn("Ground", prompt["messages"][0]["content"]["text"])

    def test_unknown_prompt_safe_not_found(self) -> None:
        """Unknown prompts should have safe not-found metadata."""
        response = safe_mcp_prompt_not_found("missing_prompt")

        self.assertTrue(response["isError"])
        self.assertEqual(response["error"], "prompt_not_found")
        self.assertFalse(response["safety"]["mcp_execution_enabled"])
        with self.assertRaises(KeyError):
            get_mcp_prompt("missing_prompt")

    def test_prompt_templates_have_grounding_and_no_mutation_instructions(self) -> None:
        """Prompt templates should require grounding and avoid action instructions."""
        forbidden = [
            "approve",
            "submit",
            "upload",
            "update",
            "delete",
            "payment",
            "mutate",
        ]
        for prompt in list_mcp_prompts():
            lowered = prompt.template.lower()
            self.assertTrue(
                "ground" in lowered or "cite" in lowered or "source label" in lowered,
                prompt.name,
            )
            for phrase in forbidden:
                self.assertNotIn(phrase, lowered, prompt.name)

    def test_json_exports_are_serializable(self) -> None:
        """Resource, prompt, capability, safety, and manifest exports should parse."""
        self.assertIsInstance(json.loads(export_mcp_resources_json()), list)
        self.assertIsInstance(json.loads(export_mcp_prompts_json()), list)
        self.assertIsInstance(json.loads(export_mcp_capabilities_json()), dict)
        self.assertIsInstance(json.loads(export_mcp_safety_json()), dict)
        manifest = json.loads(export_mcp_manifest_json())
        self.assertEqual(manifest["server"]["version"], __version__)
        self.assertIn("capabilities", manifest)

    def test_stdio_discovery_output_includes_resources_prompts_capabilities(self) -> None:
        """Stdio discovery should include richer Phase 15A metadata."""
        initialize = handle_mcp_jsonrpc_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        discovery = handle_mcp_jsonrpc_request(
            {"jsonrpc": "2.0", "id": 2, "method": "discovery/get"}
        )
        capabilities = handle_mcp_jsonrpc_request(
            {"jsonrpc": "2.0", "id": 3, "method": "capabilities/get"}
        )
        prompt = handle_mcp_jsonrpc_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "prompts/get",
                "params": {"name": "rfi_review_prompt"},
            }
        )

        self.assertIn("resources", initialize["result"])
        self.assertIn("prompts", initialize["result"])
        self.assertIn("capabilitySummary", initialize["result"])
        self.assertIn("resources", discovery["result"])
        self.assertFalse(capabilities["result"]["safety"]["mcp_execution_enabled"])
        self.assertIn("messages", prompt["result"])

    def test_execution_requests_still_disabled(self) -> None:
        """MCP and Procore tool execution must remain disabled."""
        direct = disabled_mcp_execution_response("procore.find_rfi")
        tool_call = build_mcp_tool_execution_disabled_response("procore.find_rfi")
        stdio = handle_mcp_jsonrpc_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "procore.find_rfi", "arguments": {"project_id": 1}},
            }
        )

        self.assertTrue(direct["isError"])
        self.assertFalse(direct["safety"]["mcp_execution_enabled"])
        self.assertTrue(tool_call["isError"])
        self.assertFalse(tool_call["metadata"]["execution_enabled"])
        self.assertTrue(stdio["result"]["isError"])
        self.assertFalse(stdio["result"]["metadata"]["mcp_execution_enabled"])

    def test_cli_mcp_commands(self) -> None:
        """Top-level MCP CLI commands should return local metadata."""
        parser = app.build_parser()

        manifest = app.run_command(parser.parse_args(["mcp", "manifest"]))
        resources = app.run_command(parser.parse_args(["mcp", "resources"]))
        prompts = app.run_command(parser.parse_args(["mcp", "prompts"]))
        capabilities = app.run_command(parser.parse_args(["mcp", "capabilities"]))
        safety = app.run_command(parser.parse_args(["mcp", "safety"]))
        resource = app.run_command(
            parser.parse_args(["mcp", "resource", "pyprocore://agent/manifest"])
        )
        prompt = app.run_command(parser.parse_args(["mcp", "prompt", "rfi_review_prompt"]))

        self.assertIn("pyprocore-agent-mcp", str(manifest))
        self.assertIn("pyprocore://agent/manifest", str(resources))
        self.assertIn("rfi_review_prompt", str(prompts))
        self.assertIn("mcp_execution_enabled", str(capabilities))
        self.assertIn("discovery_only", str(safety))
        self.assertIn("contents", resource)
        self.assertIn("messages", prompt)

    def test_existing_agent_and_eval_commands_still_work(self) -> None:
        """Existing agent and eval commands should remain backward compatible."""
        parser = app.build_parser()

        agent_tools = app.run_command(parser.parse_args(["agent", "tools"]))
        agent_mcp = app.run_command(parser.parse_args(["agent", "mcp", "manifest"]))
        eval_suites = app.run_command(parser.parse_args(["evals", "list"]))

        self.assertGreater(len(agent_tools), 0)
        self.assertIn("pyprocore-agent-mcp", str(agent_mcp))
        self.assertGreater(len(eval_suites), 0)

    def test_examples_docs_and_mkdocs_entries_exist(self) -> None:
        """Phase 15A examples and docs should be visible."""
        for number in range(249, 259):
            matches = list((PROJECT_ROOT / "examples").glob(f"{number}_*.py"))
            self.assertEqual(len(matches), 1, number)

        examples_readme = (PROJECT_ROOT / "examples/README.md").read_text(encoding="utf-8")
        docs_mcp = (PROJECT_ROOT / "docs/mcp.md").read_text(encoding="utf-8")
        mkdocs = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")

        self.assertIn("249_mcp_resources_quickstart.py", examples_readme)
        self.assertIn("258_phase15a_mcp_discovery_summary.py", examples_readme)
        self.assertIn("Phase 15A", docs_mcp)
        self.assertIn("mcp.md", mkdocs)

    def test_no_live_api_model_plugin_or_dynamic_execution_in_mcp_package(self) -> None:
        """MCP package should stay local and deterministic."""
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (PROJECT_ROOT / "pyprocore/mcp").glob("*.py")
        )
        forbidden = [
            "requests.",
            "httpx.",
            "subprocess",
            "importlib",
            "pip install",
            "eval(",
            "exec(",
            "TokenManager",
            "get_settings(",
            "run_exporter_hook(",
            "run_formatter_hook(",
            "run_validator_hook(",
            "run_record_transformer_hook(",
        ]
        for phrase in forbidden:
            self.assertNotIn(phrase, source)
        for method_name in ["def create_", "def update_", "def delete_", "def upload_"]:
            self.assertNotIn(method_name, source)

    def test_no_raw_secrets_in_mcp_outputs(self) -> None:
        """MCP outputs should not expose token or secret field names."""
        combined = "\n".join(
            [
                export_mcp_manifest_json(),
                json.dumps(build_mcp_stdio_discovery()),
                json.dumps(build_mcp_resource_definitions()),
                json.dumps(build_mcp_prompt_definitions()),
                json.dumps(build_mcp_capability_definitions()),
                json.dumps(build_mcp_safety_boundaries()),
            ]
        ).lower()

        for secret_name in ["access_token", "refresh_token", "client_secret", "authorization:"]:
            self.assertNotIn(secret_name, combined)

    def test_manifest_typed_builder(self) -> None:
        """Typed discovery manifest should include all Phase 15A sections."""
        manifest = build_mcp_discovery_manifest()

        self.assertEqual(manifest.server.version, "2.2.0")
        self.assertGreater(len(manifest.tools), 0)
        self.assertGreater(len(manifest.resources), 10)
        self.assertGreater(len(manifest.prompts), 5)
        self.assertFalse(manifest.capabilities.safety.mcp_execution_enabled)


if __name__ == "__main__":
    unittest.main()
