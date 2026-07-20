"""Tests for Phase 15C MCP compatibility, contracts, and snapshots."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from pyprocore import app
from pyprocore.agent import build_mcp_stdio_discovery
from pyprocore.mcp import (
    McpCompatibilityReport,
    McpCompatibilityStatus,
    McpContractValidationResult,
    McpDiscoveryContract,
    McpDiscoverySnapshot,
    build_mcp_compatibility_report,
    build_mcp_contract_report,
    build_mcp_discovery_manifest,
    build_mcp_discovery_snapshot,
    compare_mcp_discovery_snapshots,
    disabled_mcp_execution_response,
    load_mcp_discovery_snapshot,
    mcp_compatibility_report_to_json,
    mcp_compatibility_report_to_markdown,
    mcp_snapshot_to_json,
    safe_mcp_prompt_not_found,
    safe_mcp_resource_not_found,
    summarize_mcp_discovery_snapshot,
    validate_mcp_capability_summary,
    validate_mcp_contracts,
    validate_mcp_disabled_execution_contract,
    validate_mcp_discovery_manifest,
    validate_mcp_prompt_manifest,
    validate_mcp_resource_manifest,
    write_mcp_compatibility_report,
    write_mcp_discovery_snapshot,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase15CMCPCompatibilityTestCase(unittest.TestCase):
    """Validate discovery-only MCP compatibility helpers."""

    def test_contract_models_construct(self) -> None:
        """Contract model objects should be typed and serializable."""
        contract = McpDiscoveryContract()
        result = McpContractValidationResult(name="sample", passed=True)

        self.assertEqual(contract.schema_version, "mcp-contract-v1")
        self.assertTrue(contract.discovery_only)
        self.assertTrue(result.passed)
        json.dumps(contract.model_dump(mode="json"))
        json.dumps(result.model_dump(mode="json"))

    def test_contract_validation_passes_for_current_manifest(self) -> None:
        """Current local discovery metadata should satisfy the contract."""
        results = validate_mcp_contracts()
        report = build_mcp_contract_report()

        self.assertTrue(all(result.passed for result in results))
        self.assertTrue(report["passed"])
        self.assertEqual(report["finding_count"], 0)

    def test_contract_validation_finds_bad_manifest_sections(self) -> None:
        """Missing manifest sections should produce clear findings."""
        manifest = build_mcp_discovery_manifest().model_dump(mode="json", by_alias=True)
        manifest.pop("resources")

        result = validate_mcp_discovery_manifest(manifest)

        self.assertFalse(result.passed)
        self.assertIn("missing_section", {finding.code for finding in result.findings})

    def test_contract_validation_finds_empty_resources_and_prompts(self) -> None:
        """Empty resource and prompt manifests should fail validation."""
        resource_result = validate_mcp_resource_manifest([])
        prompt_result = validate_mcp_prompt_manifest([])

        self.assertFalse(resource_result.passed)
        self.assertFalse(prompt_result.passed)
        self.assertIn("empty_resources", {finding.code for finding in resource_result.findings})
        self.assertIn("empty_prompts", {finding.code for finding in prompt_result.findings})

    def test_contract_validation_finds_enabled_flags(self) -> None:
        """Capability validation should catch accidental enabled flags."""
        manifest = build_mcp_discovery_manifest().model_dump(mode="json", by_alias=True)
        capabilities = copy.deepcopy(manifest["capabilities"])
        capabilities["disabled_execution_status"]["mcp_tool_calls"] = True
        capabilities["tool_summary"]["execution_enabled"] = True
        capabilities["safety"]["mcp_execution_enabled"] = True

        result = validate_mcp_capability_summary(capabilities)

        self.assertFalse(result.passed)
        codes = {finding.code for finding in result.findings}
        self.assertIn("disabled_status_not_false", codes)
        self.assertIn("tool_execution_not_disabled", codes)
        self.assertIn("safety_flag_not_false", codes)

    def test_disabled_execution_contract_and_response_shapes(self) -> None:
        """Disabled and unknown response shapes should stay safe."""
        disabled = disabled_mcp_execution_response("procore.example")
        resource = safe_mcp_resource_not_found("pyprocore://missing")
        prompt = safe_mcp_prompt_not_found("missing_prompt")
        result = validate_mcp_disabled_execution_contract(disabled)

        self.assertTrue(result.passed)
        self.assertTrue(disabled["isError"])
        self.assertFalse(disabled["safety"]["mcp_execution_enabled"])
        self.assertTrue(resource["isError"])
        self.assertTrue(prompt["isError"])
        self.assertFalse(resource["safety"]["calls_live_procore_api"])
        self.assertFalse(prompt["safety"]["calls_live_procore_api"])

    def test_snapshot_build_write_load_compare_and_summarize(self) -> None:
        """Snapshots should round-trip through local JSON files."""
        snapshot = build_mcp_discovery_snapshot()
        summary = summarize_mcp_discovery_snapshot(snapshot)
        snapshot_json = json.loads(mcp_snapshot_to_json(snapshot))

        self.assertIsInstance(snapshot, McpDiscoverySnapshot)
        self.assertTrue(snapshot.metadata.contract_passed)
        self.assertEqual(summary["schema_version"], "mcp-snapshot-v1")
        self.assertEqual(snapshot_json["metadata"]["schema_version"], "mcp-snapshot-v1")

        with tempfile.TemporaryDirectory() as temp_dir:
            path = write_mcp_discovery_snapshot(
                "snapshot.json",
                snapshot,
                base_dir=temp_dir,
            )
            loaded = load_mcp_discovery_snapshot(path)
            comparison = compare_mcp_discovery_snapshots(snapshot, loaded)

            self.assertTrue(path.exists())
            self.assertTrue(comparison["compatible"])
            self.assertEqual(comparison["resources_added"], [])
            with self.assertRaises(ValueError):
                write_mcp_discovery_snapshot("../bad.json", snapshot, base_dir=temp_dir)

    def test_compatibility_report_json_markdown_and_write(self) -> None:
        """Compatibility reports should serialize as JSON and Markdown."""
        report = build_mcp_compatibility_report()
        json_text = mcp_compatibility_report_to_json(report, pretty=True)
        markdown = mcp_compatibility_report_to_markdown(report)

        self.assertIsInstance(report, McpCompatibilityReport)
        self.assertEqual(report.status, McpCompatibilityStatus.PASS)
        self.assertIn("mcp-compatibility-v1", json_text)
        self.assertIn("# PyProcore MCP Compatibility Report", markdown)

        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = write_mcp_compatibility_report(
                "report.json",
                report=report,
                base_dir=temp_dir,
            )
            md_path = write_mcp_compatibility_report(
                "report.md",
                format="markdown",
                report=report,
                base_dir=temp_dir,
            )

            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            with self.assertRaises(ValueError):
                write_mcp_compatibility_report("../bad.json", report=report, base_dir=temp_dir)

    def test_stdio_discovery_includes_phase15c_metadata(self) -> None:
        """Stdio discovery should expose contract and compatibility metadata."""
        discovery = build_mcp_stdio_discovery()

        self.assertEqual(discovery["contract"]["schemaVersion"], "mcp-contract-v1")
        self.assertTrue(discovery["contract"]["passed"])
        self.assertEqual(discovery["snapshot"]["schemaVersion"], "mcp-snapshot-v1")
        self.assertEqual(
            discovery["compatibility"]["schemaVersion"],
            "mcp-compatibility-v1",
        )
        self.assertIn("disabledExecutionResponseShape", discovery)
        self.assertIn("unknownResourceResponseShape", discovery)
        self.assertIn("unknownPromptResponseShape", discovery)

    def test_cli_phase15c_mcp_commands(self) -> None:
        """Phase 15C MCP commands should return local metadata only."""
        parser = app.build_parser()

        validate = app.run_command(parser.parse_args(["mcp", "validate"]))
        snapshot = app.run_command(parser.parse_args(["mcp", "snapshot"]))
        report_json = app.run_command(parser.parse_args(["mcp", "compatibility-report"]))
        report_md = app.run_command(
            parser.parse_args(["mcp", "compatibility-report", "--format", "markdown"])
        )
        fixtures = app.run_command(parser.parse_args(["mcp", "sample-fixtures"]))
        disabled = app.run_command(parser.parse_args(["mcp", "disabled-response"]))
        unknown_resource = app.run_command(parser.parse_args(["mcp", "unknown-resource-response"]))
        unknown_prompt = app.run_command(parser.parse_args(["mcp", "unknown-prompt-response"]))

        self.assertTrue(json.loads(validate)["passed"])
        self.assertEqual(json.loads(snapshot)["metadata"]["schema_version"], "mcp-snapshot-v1")
        self.assertEqual(json.loads(report_json)["schema_version"], "mcp-compatibility-v1")
        self.assertIn("MCP Compatibility Report", report_md)
        self.assertGreaterEqual(fixtures["fixture_count"], 10)
        self.assertTrue(disabled["isError"])
        self.assertTrue(unknown_resource["isError"])
        self.assertTrue(unknown_prompt["isError"])

    def test_sample_fixtures_are_valid_safe_json(self) -> None:
        """Static MCP fixtures should parse and avoid protected markers."""
        fixtures_dir = PROJECT_ROOT / "examples" / "mcp_fixtures"
        expected = {
            "initialize_response.json",
            "list_resources_response.json",
            "read_resource_response.json",
            "list_prompts_response.json",
            "get_prompt_response.json",
            "capability_summary_response.json",
            "disabled_tool_call_response.json",
            "unknown_resource_response.json",
            "unknown_prompt_response.json",
            "discovery_snapshot.json",
            "compatibility_report.json",
        }
        found = {path.name for path in fixtures_dir.glob("*.json")}
        combined = ""

        self.assertTrue(expected.issubset(found))
        for path in fixtures_dir.glob("*.json"):
            text = path.read_text(encoding="utf-8")
            json.loads(text)
            combined += text.lower()

        for marker in ("access_token", "refresh_token", "client_secret", "authorization:"):
            self.assertNotIn(marker, combined)

    def test_examples_docs_and_changelog_exist(self) -> None:
        """Phase 15C examples and docs should be visible."""
        for number in range(269, 279):
            matches = list((PROJECT_ROOT / "examples").glob(f"{number}_*.py"))
            self.assertEqual(len(matches), 1, number)

        examples_readme = (PROJECT_ROOT / "examples/README.md").read_text(encoding="utf-8")
        docs_mcp = (PROJECT_ROOT / "docs/mcp.md").read_text(encoding="utf-8")
        changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn("278_phase15c_mcp_compatibility_summary.py", examples_readme)
        self.assertIn("Phase 15C", docs_mcp)
        self.assertIn("Phase 15C", changelog)

    def test_mcp_source_stays_local_and_static(self) -> None:
        """New MCP modules should not add remote calls or dynamic loading."""
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (PROJECT_ROOT / "pyprocore/mcp").glob("*.py")
        )

        for phrase in (
            "requests.",
            "httpx.",
            "subprocess",
            "importlib",
            "pip install",
            "eval(",
            "exec(",
            "TokenManager",
            "get_settings(",
        ):
            self.assertNotIn(phrase, source)


if __name__ == "__main__":
    unittest.main()
