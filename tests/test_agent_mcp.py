"""Tests for the discovery-only PyProcore MCP adapter."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from pyprocore import __version__, app
from pyprocore.agent import (
    build_mcp_prompt_definitions,
    build_mcp_resource_definitions,
    build_mcp_server_info,
    build_mcp_tool_definitions,
    build_mcp_tool_execution_disabled_response,
    export_mcp_manifest_json,
    export_mcp_prompts_json,
    export_mcp_resources_json,
    export_mcp_tools_json,
    handle_mcp_jsonrpc_request,
    read_mcp_resource,
    run_mcp_stdio_server,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AgentMCPTestCase(unittest.TestCase):
    """Validate MCP discovery metadata and disabled execution behavior."""

    def test_mcp_module_exports_tools_without_credentials(self) -> None:
        """MCP tool definitions should build without loading SDK settings."""
        with patch("pyprocore.core.config.get_settings") as get_settings:
            tools = build_mcp_tool_definitions()

        get_settings.assert_not_called()
        self.assertGreater(len(tools), 0)
        self.assertTrue(any(tool["name"] == "procore.find_rfi" for tool in tools))

    def test_mcp_tools_are_sorted_and_include_metadata(self) -> None:
        """Tool definitions should be deterministic and include safety metadata."""
        tools = build_mcp_tool_definitions()
        names = [tool["name"] for tool in tools]
        find_rfi = next(tool for tool in tools if tool["name"] == "procore.find_rfi")

        self.assertEqual(names, sorted(names))
        self.assertIn("inputSchema", find_rfi)
        self.assertEqual(find_rfi["metadata"]["category"], "search")
        self.assertTrue(find_rfi["metadata"]["requires_auth"])
        self.assertTrue(find_rfi["metadata"]["calls_live_api"])
        self.assertFalse(find_rfi["metadata"]["execution_enabled"])
        self.assertTrue(find_rfi["metadata"]["discovery_only"])
        self.assertEqual(find_rfi["metadata"]["version_added"], "2.2.0")

    def test_mcp_resources_include_expected_local_documents(self) -> None:
        """Resource definitions should include local manifest, OpenAPI, and schemas."""
        resources = build_mcp_resource_definitions()
        uris = {resource["uri"] for resource in resources}

        self.assertIn("pyprocore://agent/manifest", uris)
        self.assertIn("pyprocore://agent/openapi", uris)
        self.assertIn("pyprocore://agent/schemas", uris)

    def test_mcp_prompts_export_works(self) -> None:
        """Prompt definitions should export as local discovery metadata."""
        prompts = build_mcp_prompt_definitions()

        self.assertGreaterEqual(len(prompts), 1)
        self.assertTrue(prompts[0]["metadata"]["discovery_only"])

    def test_disabled_tool_call_response_never_executes(self) -> None:
        """Disabled call responses should clearly say no Procore call was made."""
        response = build_mcp_tool_execution_disabled_response("procore.find_rfi")

        self.assertTrue(response["isError"])
        self.assertFalse(response["metadata"]["execution_enabled"])
        self.assertFalse(response["metadata"]["calls_live_api"])
        self.assertIn("no Procore API call was made", response["content"][0]["text"])

    def test_mcp_json_exports_are_serializable(self) -> None:
        """All MCP JSON exports should parse back into JSON values."""
        self.assertIsInstance(json.loads(export_mcp_tools_json()), list)
        self.assertIsInstance(json.loads(export_mcp_resources_json()), list)
        self.assertIsInstance(json.loads(export_mcp_prompts_json()), list)
        manifest = json.loads(export_mcp_manifest_json())
        self.assertEqual(manifest["server"]["version"], __version__)

    def test_read_mcp_resource_returns_local_metadata(self) -> None:
        """Local MCP resources should be readable without credentials."""
        manifest = read_mcp_resource("pyprocore://agent/manifest")
        openapi = read_mcp_resource("pyprocore://agent/openapi")
        schemas = read_mcp_resource("pyprocore://agent/schemas")
        text = manifest["contents"][0]["text"]

        self.assertIn("pyprocore-agent-mcp", text)
        self.assertIn("openapi", openapi["contents"][0]["text"])
        self.assertIn("AgentTool", schemas["contents"][0]["text"])
        with self.assertRaises(FileNotFoundError):
            read_mcp_resource("pyprocore://agent/missing")

    def test_cli_parser_includes_agent_mcp_commands(self) -> None:
        """The CLI parser should include agent MCP commands."""
        parser = app.build_parser()
        args = parser.parse_args(["agent", "mcp", "tools", "--pretty"])

        self.assertEqual(args.command, "agent")
        self.assertEqual(args.agent_command, "mcp")
        self.assertEqual(args.agent_mcp_command, "tools")
        self.assertTrue(args.pretty)

    def test_run_command_agent_mcp_branches(self) -> None:
        """Direct CLI dispatch should cover MCP metadata commands."""
        parser = app.build_parser()

        tools = app.run_command(parser.parse_args(["agent", "mcp", "tools"]))
        resources = app.run_command(parser.parse_args(["agent", "mcp", "resources"]))
        prompts = app.run_command(parser.parse_args(["agent", "mcp", "prompts"]))
        manifest = app.run_command(parser.parse_args(["agent", "mcp", "manifest"]))

        self.assertIn("procore.find_rfi", str(tools))
        self.assertIn("pyprocore://agent/manifest", str(resources))
        self.assertIn("pyprocore.discovery_summary", str(prompts))
        self.assertIn("pyprocore-agent-mcp", str(manifest))

    def test_run_command_agent_mcp_output_file(self) -> None:
        """CLI dispatch should write MCP metadata when --output is provided."""
        parser = app.build_parser()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "mcp-tools.json"
            result = app.run_command(
                parser.parse_args(["agent", "mcp", "tools", "--output", str(output_path)])
            )

            self.assertEqual(result, output_path)
            self.assertTrue(output_path.exists())
            self.assertIn("procore.find_rfi", output_path.read_text(encoding="utf-8"))

    def test_mcp_stdio_handler_supported_methods(self) -> None:
        """The stdio handler should support discovery methods without subprocesses."""
        initialize = handle_mcp_jsonrpc_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        tools = handle_mcp_jsonrpc_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        call = handle_mcp_jsonrpc_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "procore.find_rfi", "arguments": {"project_id": 1}},
            }
        )
        missing = handle_mcp_jsonrpc_request(
            {"jsonrpc": "2.0", "id": 4, "method": "unknown/method"}
        )

        self.assertIsNotNone(initialize)
        self.assertEqual(initialize["result"]["serverInfo"]["name"], "pyprocore-agent-mcp")
        self.assertIsNotNone(tools)
        self.assertTrue(
            any(tool["name"] == "procore.find_rfi" for tool in tools["result"]["tools"])
        )
        self.assertIsNotNone(call)
        self.assertTrue(call["result"]["isError"])
        self.assertIsNotNone(missing)
        self.assertEqual(missing["error"]["code"], -32601)

    def test_mcp_stdio_handler_error_branches(self) -> None:
        """The stdio handler should return safe JSON-RPC errors."""
        notification = handle_mcp_jsonrpc_request(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}
        )
        invalid = handle_mcp_jsonrpc_request({"jsonrpc": "2.0", "id": 1})
        missing_name = handle_mcp_jsonrpc_request(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {}}
        )
        missing_uri = handle_mcp_jsonrpc_request(
            {"jsonrpc": "2.0", "id": 3, "method": "resources/read", "params": {}}
        )
        unknown_resource = handle_mcp_jsonrpc_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {"uri": "pyprocore://agent/missing"},
            }
        )
        ping = handle_mcp_jsonrpc_request({"jsonrpc": "2.0", "id": 5, "method": "ping"})

        self.assertIsNone(notification)
        self.assertEqual(invalid["error"]["code"], -32600)
        self.assertEqual(missing_name["error"]["code"], -32602)
        self.assertEqual(missing_uri["error"]["code"], -32602)
        self.assertEqual(unknown_resource["error"]["code"], -32004)
        self.assertEqual(ping["result"], {})

    def test_mcp_stdio_loop_handles_lines_without_hanging(self) -> None:
        """The stdio loop should process line-delimited JSON and stop at EOF."""
        input_stream = StringIO(
            "\n".join(
                [
                    "",
                    "not-json",
                    "[]",
                    '{"jsonrpc":"2.0","method":"notifications/initialized"}',
                    '{"jsonrpc":"2.0","id":1,"method":"ping"}',
                ]
            )
        )
        output_stream = StringIO()

        run_mcp_stdio_server(input_stream=input_stream, output_stream=output_stream)
        lines = [json.loads(line) for line in output_stream.getvalue().splitlines()]

        self.assertEqual(lines[0]["error"]["code"], -32700)
        self.assertEqual(lines[1]["error"]["code"], -32600)
        self.assertEqual(lines[2]["result"], {})

    def test_main_agent_mcp_output_branches(self) -> None:
        """CLI main should print MCP metadata and file-output messages."""
        with (
            patch.object(
                sys,
                "argv",
                ["procore-sdk", "agent", "mcp", "tools"],
            ),
            patch("builtins.print") as print_mock,
        ):
            app.main()

        self.assertTrue(any("procore.find_rfi" in str(call) for call in print_mock.call_args_list))

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "manifest.json"
            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        "procore-sdk",
                        "agent",
                        "mcp",
                        "manifest",
                        "--output",
                        str(output_path),
                    ],
                ),
                patch("builtins.print") as print_mock,
            ):
                app.main()

            self.assertTrue(output_path.exists())
            self.assertTrue(
                any("MCP metadata written" in str(call) for call in print_mock.call_args_list)
            )

    def test_mcp_stdio_resource_and_prompt_methods(self) -> None:
        """The stdio handler should expose resource and prompt discovery."""
        resources = handle_mcp_jsonrpc_request(
            {"jsonrpc": "2.0", "id": 1, "method": "resources/list"}
        )
        read = handle_mcp_jsonrpc_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "resources/read",
                "params": {"uri": "pyprocore://agent/manifest"},
            }
        )
        prompts = handle_mcp_jsonrpc_request({"jsonrpc": "2.0", "id": 3, "method": "prompts/list"})

        self.assertIsNotNone(resources)
        self.assertIn("resources", resources["result"])
        self.assertIsNotNone(read)
        self.assertIn("contents", read["result"])
        self.assertIsNotNone(prompts)
        self.assertIn("prompts", prompts["result"])

    def test_export_agent_mcp_script_writes_expected_files(self) -> None:
        """The export script should write all MCP metadata files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/export_agent_mcp.py",
                    "--output-dir",
                    temp_dir,
                    "--pretty",
                ],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(temp_dir) / "mcp-tools.json").exists())
            self.assertTrue((Path(temp_dir) / "mcp-resources.json").exists())
            self.assertTrue((Path(temp_dir) / "mcp-prompts.json").exists())
            self.assertTrue((Path(temp_dir) / "mcp-manifest.json").exists())
            self.assertIn("no Procore API calls", result.stdout)

    def test_examples_docs_and_mkdocs_entries_exist(self) -> None:
        """Phase 7E examples and docs should be present."""
        self.assertTrue((PROJECT_ROOT / "examples/60_export_agent_mcp.py").exists())
        self.assertTrue((PROJECT_ROOT / "examples/61_mcp_discovery_only.py").exists())
        self.assertTrue((PROJECT_ROOT / "docs/recipes/export-agent-mcp-tools.md").exists())
        self.assertTrue((PROJECT_ROOT / "docs/recipes/run-mcp-discovery-adapter.md").exists())

        mkdocs = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn("export-agent-mcp-tools.md", mkdocs)
        self.assertIn("run-mcp-discovery-adapter.md", mkdocs)

    def test_no_live_procore_api_or_execution_in_mcp_modules(self) -> None:
        """MCP modules should remain discovery-only and avoid HTTP clients."""
        mcp_source = (PROJECT_ROOT / "pyprocore/agent/mcp.py").read_text(encoding="utf-8")
        stdio_source = (PROJECT_ROOT / "pyprocore/agent/mcp_stdio.py").read_text(encoding="utf-8")

        combined = mcp_source + stdio_source
        self.assertNotIn("requests.", combined)
        self.assertNotIn("get_settings(", combined)
        self.assertNotIn("TokenManager", combined)
        self.assertIn("execution_enabled", combined)
        self.assertIn("False", combined)

    def test_version_remains_210(self) -> None:
        """Phase 7E should use the released package version."""
        self.assertEqual(__version__, "2.3.0")

    def test_mcp_server_info_is_discovery_only(self) -> None:
        """Server info should state discovery-only safety."""
        info = build_mcp_server_info()

        self.assertEqual(info["version"], "2.3.0")
        self.assertFalse(info["safety"]["tool_execution_enabled"])
        self.assertFalse(info["safety"]["calls_live_procore_api"])
        self.assertFalse(info["safety"]["requires_credentials"])


if __name__ == "__main__":
    unittest.main()
