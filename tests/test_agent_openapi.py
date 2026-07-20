"""Tests for Agent API OpenAPI and JSON Schema exports."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pyprocore
from pyprocore.agent import (
    build_agent_openapi_spec,
    build_agent_tool_schemas,
    export_agent_openapi_json,
    export_agent_openapi_yaml,
    export_agent_tool_schemas_json,
)
from pyprocore.agent.server import create_agent_api_handler

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def dispatch_handler(
    path: str,
    *,
    method: str = "GET",
) -> tuple[int, dict[str, str], dict[str, Any] | list[Any]]:
    """Dispatch the local handler without opening a socket."""
    handler_cls = create_agent_api_handler()
    handler = handler_cls.__new__(handler_cls)
    handler.path = path
    handler.wfile = BytesIO()

    captured_status = 0
    captured_headers: dict[str, str] = {}

    def send_response(status: int) -> None:
        nonlocal captured_status
        captured_status = status

    def send_header(name: str, value: str) -> None:
        captured_headers[name] = value

    handler.send_response = send_response  # type: ignore[method-assign]
    handler.send_header = send_header  # type: ignore[method-assign]
    handler.end_headers = lambda: None  # type: ignore[method-assign]

    if method == "GET":
        handler.do_GET()
    elif method == "POST":
        handler.do_POST()
    else:
        raise AssertionError(f"Unsupported test method: {method}")

    payload = json.loads(handler.wfile.getvalue().decode("utf-8"))
    return captured_status, captured_headers, payload


class AgentOpenAPITestCase(unittest.TestCase):
    """Validate OpenAPI and JSON Schema export behavior."""

    def test_build_agent_openapi_spec_returns_serializable_dict(self) -> None:
        """The OpenAPI builder should return deterministic JSON-compatible data."""
        spec = build_agent_openapi_spec()

        self.assertIsInstance(spec, dict)
        self.assertEqual(spec["openapi"], "3.1.0")
        self.assertEqual(spec["info"]["title"], "PyProcore Agent API")
        self.assertEqual(spec["info"]["version"], pyprocore.__version__)
        self.assertFalse(spec["x-pyprocore-safety"]["tool_execution_enabled"])
        json.dumps(spec, sort_keys=True)

    def test_openapi_spec_includes_expected_paths_and_schemas(self) -> None:
        """The OpenAPI document should describe all discovery endpoints."""
        spec = build_agent_openapi_spec()

        expected_paths = {
            "/",
            "/health",
            "/agent/manifest",
            "/agent/tools",
            "/agent/tools/{tool_name}",
            "/agent/tools/{tool_name}/call",
            "/agent/openapi.json",
            "/agent/schemas",
        }
        self.assertTrue(expected_paths.issubset(set(spec["paths"])))
        self.assertIn("AgentManifest", spec["components"]["schemas"])
        self.assertIn("AgentTool", spec["components"]["schemas"])
        self.assertIn("AgentToolRegistry", spec["components"]["schemas"])
        self.assertIn("ToolExecutionDisabledResponse", spec["components"]["schemas"])
        call_endpoint = spec["paths"]["/agent/tools/{tool_name}/call"]["post"]
        self.assertIn("disabled", call_endpoint["description"].lower())
        self.assertIn("501", call_endpoint["responses"])

    def test_schema_export_includes_models_and_tool_schemas(self) -> None:
        """The schema export should include model schemas and per-tool schemas."""
        schema_export = build_agent_tool_schemas()

        self.assertEqual(schema_export["version"], pyprocore.__version__)
        self.assertIn("AgentManifest", schema_export["schemas"])
        self.assertIn("AgentTool", schema_export["schemas"])
        self.assertIn("AgentToolRegistry", schema_export["schemas"])
        self.assertIn("AgentToolList", schema_export["schemas"])
        self.assertIn("procore.find_rfi", schema_export["tools"])
        for tool_name, tool in schema_export["tools"].items():
            with self.subTest(tool=tool_name):
                self.assertIn("input_schema", tool)
                self.assertIn("output_schema", tool)
                self.assertIn("type", tool["input_schema"])
                self.assertIn("type", tool["output_schema"])
        json.dumps(schema_export, sort_keys=True)

    def test_json_and_yaml_exports_work(self) -> None:
        """Text export helpers should return parseable JSON and simple YAML."""
        openapi_json = export_agent_openapi_json(pretty=True)
        schemas_json = export_agent_tool_schemas_json(pretty=True)
        openapi_yaml = export_agent_openapi_yaml()

        self.assertEqual(json.loads(openapi_json)["openapi"], "3.1.0")
        self.assertIn("AgentTool", json.loads(schemas_json)["schemas"])
        self.assertIn('"openapi": "3.1.0"', openapi_yaml)
        self.assertIn('"PyProcore Agent API"', openapi_yaml)

    def test_exports_do_not_read_configuration_or_call_live_api(self) -> None:
        """Spec exports should stay metadata-only."""
        with patch("pyprocore.core.config.get_settings") as get_settings:
            spec = build_agent_openapi_spec()
            schemas = build_agent_tool_schemas()

        get_settings.assert_not_called()
        self.assertFalse(spec["x-pyprocore-safety"]["calls_live_procore_api"])
        self.assertGreater(schemas["tool_count"], 0)

    def test_cli_agent_openapi_and_schemas_work(self) -> None:
        """CLI spec commands should work without credentials."""
        commands = [
            ["agent", "openapi"],
            ["agent", "openapi", "--pretty"],
            ["agent", "openapi", "--yaml"],
            ["agent", "schemas"],
            ["agent", "schemas", "--pretty"],
        ]
        for command in commands:
            with self.subTest(command=command):
                result = subprocess.run(
                    [sys.executable, "-m", "pyprocore.app", *command],
                    cwd=PROJECT_ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("pyprocore", result.stdout.lower())

    def test_cli_output_file_write_works(self) -> None:
        """CLI --output should write spec files to the requested path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            openapi_path = Path(temp_dir) / "openapi.json"
            schemas_path = Path(temp_dir) / "schemas.json"
            commands = [
                ["agent", "openapi", "--output", str(openapi_path)],
                ["agent", "schemas", "--output", str(schemas_path)],
            ]
            for command in commands:
                result = subprocess.run(
                    [sys.executable, "-m", "pyprocore.app", *command],
                    cwd=PROJECT_ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            self.assertEqual(json.loads(openapi_path.read_text())["openapi"], "3.1.0")
            self.assertIn("AgentTool", json.loads(schemas_path.read_text())["schemas"])

    def test_server_openapi_and_schema_endpoints_work(self) -> None:
        """The local server handler should expose spec documents."""
        openapi_status, openapi_headers, openapi_payload = dispatch_handler("/agent/openapi.json")
        schemas_status, _, schemas_payload = dispatch_handler("/agent/schemas")
        call_status, _, call_payload = dispatch_handler(
            "/agent/tools/procore.find_rfi/call",
            method="POST",
        )

        self.assertEqual(openapi_status, 200)
        self.assertEqual(openapi_headers["Content-Type"], "application/json")
        self.assertIsInstance(openapi_payload, dict)
        self.assertEqual(openapi_payload["openapi"], "3.1.0")

        self.assertEqual(schemas_status, 200)
        self.assertIsInstance(schemas_payload, dict)
        self.assertIn("procore.find_rfi", schemas_payload["tools"])

        self.assertEqual(call_status, 501)
        self.assertEqual(call_payload["error"], "tool_execution_disabled")

    def test_export_script_writes_expected_files(self) -> None:
        """The helper script should export both JSON files without live API calls."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/export_agent_openapi.py",
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
            openapi_path = Path(temp_dir) / "agent-openapi.json"
            schemas_path = Path(temp_dir) / "agent-schemas.json"
            self.assertTrue(openapi_path.exists())
            self.assertTrue(schemas_path.exists())
            self.assertEqual(json.loads(openapi_path.read_text())["openapi"], "3.1.0")
            self.assertIn("No Procore credentials", result.stdout)

    def test_examples_docs_and_mkdocs_are_linked(self) -> None:
        """Phase 7C examples and docs should be present and linked."""
        for relative_path in (
            "pyprocore/agent/openapi.py",
            "scripts/export_agent_openapi.py",
            "examples/56_export_agent_openapi.py",
            "examples/57_inspect_agent_schemas.py",
            "docs/recipes/export-agent-openapi.md",
        ):
            self.assertTrue((PROJECT_ROOT / relative_path).exists(), relative_path)

        mkdocs = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        docs = (PROJECT_ROOT / "docs/agent-api.md").read_text(encoding="utf-8")
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("export-agent-openapi.md", mkdocs)
        self.assertIn("OpenAPI", docs)
        self.assertIn("JSON Schema", docs)
        self.assertIn("agent openapi", readme.lower())

    def test_openapi_source_does_not_enable_execution_or_live_calls(self) -> None:
        """The OpenAPI module should not execute tools or call Procore."""
        source = (PROJECT_ROOT / "pyprocore/agent/openapi.py").read_text(encoding="utf-8")

        self.assertNotIn("requests.", source)
        self.assertNotIn("Session(", source)
        self.assertNotIn("execute", source.lower())
        self.assertIn("tool_execution_enabled", source)


if __name__ == "__main__":
    unittest.main()
