"""Tests for the PyProcore agent tool registry."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pyprocore
from pyprocore.agent import (
    AgentToolNotFoundError,
    AgentToolPermission,
    AgentToolSafety,
    build_agent_manifest,
    export_agent_manifest_json,
    export_agent_tools_json,
    get_agent_tool,
    list_agent_tools,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AgentRegistryTestCase(unittest.TestCase):
    """Validate the static agent registry stays safe and discoverable."""

    def test_registry_contains_expected_stable_tools(self) -> None:
        """The registry should include the Phase 7A stable tool names."""
        expected = {
            "procore.list_companies",
            "procore.find_company",
            "procore.list_projects",
            "procore.find_project",
            "procore.list_rfis",
            "procore.get_rfi",
            "procore.find_rfi",
            "procore.list_submittals",
            "procore.get_submittal",
            "procore.find_submittal",
            "procore.list_documents",
            "procore.get_document",
            "procore.find_document",
            "procore.list_drawings",
            "procore.get_drawing",
            "procore.find_drawing",
            "procore.list_specification_sections",
            "procore.find_specification_section",
            "procore.list_photo_albums",
            "procore.list_photos",
            "procore.list_daily_logs",
            "procore.build_project_context_package",
            "procore.build_enhanced_rfi_package",
            "procore.build_enhanced_submittal_package",
            "procore.build_ai_review_export",
            "procore.build_ai_prompt_pack",
            "procore.validate_workflow_plan",
        }

        names = {tool.name for tool in list_agent_tools()}

        self.assertTrue(expected.issubset(names))

    def test_tools_are_sorted_and_prefixed(self) -> None:
        """Tool names should be deterministic and namespaced."""
        names = [tool.name for tool in list_agent_tools()]

        self.assertEqual(names, sorted(names))
        self.assertTrue(all(name.startswith("procore.") for name in names))

    def test_tools_have_descriptions_schemas_and_safety_metadata(self) -> None:
        """Every tool should include useful metadata for agent planners."""
        for tool in list_agent_tools():
            self.assertTrue(tool.title)
            self.assertTrue(tool.description)
            self.assertEqual(tool.input_schema.get("type"), "object")
            self.assertIn("type", tool.output_schema)
            self.assertTrue(tool.permissions)
            self.assertIn(
                tool.safety_level,
                {AgentToolSafety.READ_ONLY, AgentToolSafety.LOCAL_FILE_OUTPUT},
            )

    def test_registry_does_not_execute_network_or_read_configuration(self) -> None:
        """Building registry metadata should not call Procore or read credentials."""
        with patch("pyprocore.core.config.get_settings") as get_settings:
            manifest = build_agent_manifest()

        get_settings.assert_not_called()
        self.assertEqual(manifest.package_name, "pyprocore")

    def test_manifest_is_json_serializable_and_includes_version(self) -> None:
        """Manifest exports should be JSON serializable and versioned."""
        manifest = build_agent_manifest()
        payload = json.loads(manifest.model_dump_json())

        self.assertEqual(payload["package_version"], pyprocore.__version__)
        self.assertEqual(payload["tool_count"], len(payload["tools"]))
        self.assertEqual(payload["registry_version"], "1")
        self.assertIn("generated_at", payload)
        self.assertEqual(json.loads(export_agent_manifest_json())["package_name"], "pyprocore")
        self.assertIsInstance(json.loads(export_agent_tools_json()), list)

    def test_unknown_tool_raises_clear_error(self) -> None:
        """Unknown lookups should fail with a clear custom exception."""
        with self.assertRaisesRegex(AgentToolNotFoundError, "not registered"):
            get_agent_tool("procore.nope")

    def test_registry_excludes_destructive_tool_names(self) -> None:
        """The agent registry should not advertise destructive Procore operations."""
        forbidden_fragments = (".create", ".update", ".delete", ".remove", ".send")
        for tool in list_agent_tools():
            self.assertFalse(
                any(fragment in tool.name for fragment in forbidden_fragments),
                tool.name,
            )
            self.assertNotIn("delete", " ".join(tool.side_effects).lower())
            if tool.produces_files:
                self.assertIn(AgentToolPermission.WRITE_LOCAL_FILES, tool.permissions)
            else:
                self.assertNotIn(AgentToolPermission.WRITE_LOCAL_FILES, tool.permissions)

    def test_cli_agent_commands_work_without_credentials(self) -> None:
        """Agent CLI commands should inspect metadata without live Procore access."""
        commands = [
            ["agent", "manifest"],
            ["agent", "manifest", "--json"],
            ["agent", "tools"],
            ["agent", "tool", "procore.find_rfi"],
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
                self.assertIn("procore", result.stdout.lower())

    def test_examples_and_docs_exist(self) -> None:
        """Agent examples and docs should be linked from project documentation."""
        for relative_path in (
            "examples/53_agent_tool_registry.py",
            "examples/54_agent_manifest_export.py",
            "docs/agent-api.md",
            "docs/recipes/use-agent-tool-registry.md",
        ):
            self.assertTrue((PROJECT_ROOT / relative_path).exists(), relative_path)

        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        mkdocs = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        recipes = (PROJECT_ROOT / "docs/recipes/index.md").read_text(encoding="utf-8")

        self.assertIn("agent tool registry", readme.lower())
        self.assertIn("agent-api.md", mkdocs)
        self.assertIn("use-agent-tool-registry.md", mkdocs)
        self.assertIn("Use The Agent Tool Registry", recipes)


if __name__ == "__main__":
    unittest.main()
