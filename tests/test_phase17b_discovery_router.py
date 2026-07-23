"""Tests for Phase 17B local discovery router metadata support."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pyprocore
from pyprocore import app
from pyprocore.discovery import (
    DiscoveryRouteResult,
    build_discovery_bundle,
    build_discovery_report,
    discovery_bundle_to_json,
    discovery_bundle_to_markdown,
    discovery_capability_to_json,
    discovery_capability_to_markdown,
    discovery_report_to_json,
    discovery_report_to_markdown,
    discovery_route_result_to_json,
    discovery_route_result_to_markdown,
    get_discovery_capability,
    list_discovery_capabilities,
    route_discovery_query,
    search_discovery_capabilities,
    search_oas_catalog_capabilities,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FAKE_OAS = PROJECT_ROOT / "examples" / "catalog" / "fake_procore_oas.json"


class Phase17BDiscoveryRouterTests(unittest.TestCase):
    """Validate metadata-only local discovery routing."""

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run the local CLI without requiring credentials."""
        env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        return subprocess.run(
            [sys.executable, "-m", "pyprocore.app", *args],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_builtin_capabilities_load_with_safety_boundaries(self) -> None:
        """Built-in discovery metadata should include expected capability groups."""
        capabilities = list_discovery_capabilities()
        names = {capability.name for capability in capabilities}
        bundle = build_discovery_bundle()

        self.assertIn("rfis", names)
        self.assertIn("submittals", names)
        self.assertIn("project_tools", names)
        self.assertIn("mcp_discovery_metadata", names)
        self.assertIn("oas_catalog_reports", names)
        self.assertGreaterEqual(len(capabilities), 20)
        self.assertEqual(len(bundle.capabilities), len(capabilities))
        self.assertTrue(hasattr(pyprocore, "search_discovery_capabilities"))
        for capability in capabilities:
            self.assertTrue(capability.metadata_only)
            self.assertFalse(capability.execution_enabled)
            self.assertFalse(capability.procore_api_call_required)
            self.assertFalse(capability.write_enabled)
            self.assertFalse(capability.mcp_execution_enabled)
            self.assertFalse(capability.external_ai_required)

    def test_search_finds_rfis_submittals_and_project_tools(self) -> None:
        """Lexical routing should find common resource intents deterministically."""
        rfi_result = search_discovery_capabilities("overdue rfis", limit=3)
        submittal_result = search_discovery_capabilities("submittal package", limit=3)
        tools_result = search_discovery_capabilities("active project tools", limit=3)

        self.assertEqual(rfi_result.candidates[0].capability.name, "rfis")
        self.assertEqual(submittal_result.candidates[0].capability.name, "submittals")
        self.assertEqual(tools_result.candidates[0].capability.name, "project_tools")
        self.assertIn("rfi", rfi_result.candidates[0].matched_terms)
        for result in (rfi_result, submittal_result, tools_result):
            self.assert_route_is_metadata_only(result)

    def test_route_candidates_never_claim_enabled_execution(self) -> None:
        """Route suggestions should remain suggestions, not executable actions."""
        result = route_discovery_query("download drawings", limit=5)

        self.assertIsInstance(result, DiscoveryRouteResult)
        self.assertEqual(result.candidates[0].capability.name, "drawings")
        self.assert_route_is_metadata_only(result)
        for candidate in result.candidates:
            self.assertTrue(candidate.metadata_only)
            self.assertFalse(candidate.execution_enabled)
            self.assertFalse(candidate.procore_api_call_required)
            self.assertFalse(candidate.write_enabled)
            self.assertFalse(candidate.mcp_execution_enabled)
            self.assertFalse(candidate.external_ai_required)

    def test_get_capability_and_reports_render(self) -> None:
        """Capability inventory and reports should serialize to JSON and Markdown."""
        capability = get_discovery_capability("rfis")
        bundle = build_discovery_bundle()
        report = build_discovery_report()
        route = search_discovery_capabilities("mcp discovery metadata", limit=2)

        bundle_payload = json.loads(discovery_bundle_to_json(bundle, pretty=True))
        report_payload = json.loads(discovery_report_to_json(report, pretty=True))
        route_payload = json.loads(discovery_route_result_to_json(route, pretty=True))
        bundle_markdown = discovery_bundle_to_markdown(bundle)
        report_markdown = discovery_report_to_markdown(report)
        route_markdown = discovery_route_result_to_markdown(route)

        self.assertEqual(capability.name, "rfis")
        self.assertEqual(bundle_payload["mode"], "local_discovery_metadata_only")
        self.assertFalse(report_payload["execution_enabled"])
        self.assertIn("candidates", route_payload)
        self.assertIn("Discovery Capabilities", bundle_markdown)
        self.assertIn("does not call Procore", report_markdown)
        self.assertIn("Execution enabled: false", route_markdown)

    def test_capability_renderers_and_empty_search_render(self) -> None:
        """Single capability and empty search reports should render safely."""
        capability = get_discovery_capability("rfis")
        capability_payload = json.loads(discovery_capability_to_json(capability, pretty=True))
        capability_markdown = discovery_capability_to_markdown(capability)
        empty_result = search_discovery_capabilities(
            "zzzz qqqq yyyy",
            limit=3,
        )
        empty_markdown = discovery_route_result_to_markdown(empty_result)

        self.assertEqual(capability_payload["name"], "rfis")
        self.assertIn("RFIs", capability_markdown)
        self.assertIn("Execution enabled: false", capability_markdown)
        self.assertEqual(empty_result.candidates, [])
        self.assertIn("No candidate matched", empty_markdown)

        with self.assertRaisesRegex(KeyError, "Unknown discovery capability"):
            get_discovery_capability("not-a-capability")

    def test_search_oas_catalog_adds_local_catalog_candidates(self) -> None:
        """OAS-backed discovery should include fake OAS endpoint metadata safely."""
        result = search_oas_catalog_capabilities(FAKE_OAS, "payment applications", limit=5)

        oas_candidates = [
            candidate
            for candidate in result.candidates
            if candidate.capability.source == "local_oas"
        ]
        self.assertTrue(oas_candidates)
        self.assertTrue(
            any(
                "local_oas_risky_write_candidate" in candidate.capability.safety_labels
                for candidate in oas_candidates
            )
        )
        self.assert_route_is_metadata_only(result)

    def test_cli_discovery_commands_work_without_credentials(self) -> None:
        """Discovery CLI commands should run locally without Procore access."""
        capabilities = self.run_cli("discovery", "capabilities", "--json")
        search = self.run_cli("discovery", "search", "overdue rfis", "--json")
        describe = self.run_cli("discovery", "describe", "rfis", "--json")
        route = self.run_cli("discovery", "route", "download drawings")
        report = self.run_cli("discovery", "report", "--format", "json")
        search_oas = self.run_cli(
            "discovery",
            "search-oas",
            str(FAKE_OAS),
            "change orders",
            "--format",
            "markdown",
        )

        for completed in (capabilities, search, describe, route, report, search_oas):
            self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("capabilities", json.loads(capabilities.stdout))
        self.assertEqual(json.loads(search.stdout)["candidates"][0]["capability"]["name"], "rfis")
        self.assertEqual(json.loads(describe.stdout)["name"], "rfis")
        self.assertIn("Discovery Route Suggestions", route.stdout)
        self.assertFalse(json.loads(report.stdout)["execution_enabled"])
        self.assertIn("Discovery Route Suggestions", search_oas.stdout)

    def test_cli_discovery_main_renders_in_process(self) -> None:
        """In-process CLI rendering should cover local discovery output branches."""
        commands = [
            ["procore-sdk", "discovery", "capabilities", "--json"],
            ["procore-sdk", "discovery", "capabilities"],
            ["procore-sdk", "discovery", "describe", "rfis", "--json"],
            ["procore-sdk", "discovery", "describe", "rfis"],
            ["procore-sdk", "discovery", "search", "overdue rfis", "--json"],
            ["procore-sdk", "discovery", "route", "download drawings"],
            ["procore-sdk", "discovery", "report", "--format", "json"],
            ["procore-sdk", "discovery", "report"],
            [
                "procore-sdk",
                "discovery",
                "search-oas",
                str(FAKE_OAS),
                "payment applications",
                "--format",
                "json",
            ],
            [
                "procore-sdk",
                "discovery",
                "search-oas",
                str(FAKE_OAS),
                "payment applications",
            ],
        ]

        outputs = [self.run_main_in_process(command) for command in commands]

        self.assertIn('"capabilities"', outputs[0])
        self.assertIn("Discovery Capabilities", outputs[1])
        self.assertIn('"name": "rfis"', outputs[2])
        self.assertIn("RFIs", outputs[3])
        self.assertIn('"candidates"', outputs[4])
        self.assertIn("Discovery Route Suggestions", outputs[5])
        self.assertIn('"capability_count"', outputs[6])
        self.assertIn("Discovery Metadata Safety Report", outputs[7])
        self.assertIn("local_oas_risky_write_candidate", outputs[8])
        self.assertIn("Discovery Route Suggestions", outputs[9])

    def test_discovery_source_does_not_enable_calls_or_dynamic_loading(self) -> None:
        """Discovery source should avoid network calls, dynamic loading, and execution."""
        discovery_sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((PROJECT_ROOT / "pyprocore" / "discovery").glob("*.py"))
        )

        forbidden_snippets = (
            "import requests",
            "from requests",
            "import httpx",
            "from httpx",
            "import urllib.request",
            "from urllib",
            "import subprocess",
            "from subprocess",
            "import importlib",
            "from importlib",
            "api.procore.com",
            "procore.com/rest",
            "exec(",
            "eval(",
        )
        for snippet in forbidden_snippets:
            self.assertNotIn(snippet, discovery_sources)

    def assert_route_is_metadata_only(self, result: DiscoveryRouteResult) -> None:
        """Assert route result safety flags stay disabled."""
        self.assertTrue(result.metadata_only)
        self.assertFalse(result.execution_enabled)
        self.assertFalse(result.procore_api_call_required)
        self.assertFalse(result.write_enabled)
        self.assertFalse(result.mcp_execution_enabled)
        self.assertFalse(result.external_ai_required)
        self.assertFalse(result.remote_fetch_enabled)

    def run_main_in_process(self, argv: list[str]) -> str:
        """Run the CLI main function in-process and return stdout."""
        stdout = StringIO()
        with patch.object(sys, "argv", argv), redirect_stdout(stdout):
            app.main()
        return stdout.getvalue()


if __name__ == "__main__":
    unittest.main()
