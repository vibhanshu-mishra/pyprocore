"""Tests for release-status documentation truth and version alignment."""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path

import pyprocore

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DocsTruthAuditTestCase(unittest.TestCase):
    """Validate release-status documentation stays truthful."""

    def read_text(self, relative_path: str) -> str:
        """Read a repository file."""
        return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")

    def test_source_version_is_2_2_0(self) -> None:
        """Package and pyproject versions should remain at 2.2.0."""
        pyproject = tomllib.loads(self.read_text("pyproject.toml"))

        self.assertEqual(pyprocore.__version__, "2.2.0")
        self.assertEqual(pyproject["project"]["version"], "2.2.0")

    def test_cli_version_returns_2_2_0(self) -> None:
        """The CLI version output should reflect the package version."""
        env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        completed = subprocess.run(
            [sys.executable, "-m", "pyprocore.app", "--version"],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("pyprocore 2.2.0", completed.stdout)

    def test_readme_positions_sdk_automation_and_agent_layer(self) -> None:
        """README should explain the SDK, automation toolkit, and agent layer."""
        readme = self.read_text("README.md")

        self.assertIn("open-source Python SDK, automation toolkit, and agent-ready", readme)
        self.assertIn("python3 -m pip install pyprocore==2.2.0", readme)
        self.assertIn("Phase 7 Agent Layer", readme)
        for phrase in (
            "Agent Tool Registry",
            "Local Agent API Server",
            "OpenAPI / JSON Schema Export",
            "Agent Run Logs + Replay",
            "Discovery-only MCP Adapter",
            "Agent Evaluation Harness",
        ):
            self.assertIn(phrase, readme)

    def test_project_status_page_and_mkdocs_nav_exist(self) -> None:
        """Project status page should exist and be included in docs navigation."""
        status = self.read_text("docs/project-status.md")
        mkdocs = self.read_text("mkdocs.yml")
        index = self.read_text("docs/index.md")

        self.assertIn("Current stable release: `2.2.0`", status)
        self.assertIn("Previous stable release: `2.1.0`", status)
        self.assertIn("PyPI release completed", self.read_text("docs/release.md"))
        self.assertIn("Tool execution remains disabled", status)
        self.assertIn("MCP adapter remains discovery-only", status)
        self.assertIn("project-status.md", mkdocs)
        self.assertIn("[Project Status](project-status.md)", index)
        self.assertNotIn("final-release-readiness.md", mkdocs)
        self.assertFalse((PROJECT_ROOT / "docs/final-release-readiness.md").exists())

    def test_roadmap_places_future_items_under_future(self) -> None:
        """Roadmap should separate released and future work."""
        roadmap = self.read_text("docs/roadmap.md")
        completed_section = roadmap.split("## Future", 1)[0]
        future_section = roadmap.split("## Future", 1)[1]
        unreleased_section = roadmap.split("## Unreleased Branch Work", 1)[1].split(
            "## Future",
            1,
        )[0]

        self.assertIn("### v2.2.0", roadmap)
        self.assertIn("Phase 7 Agent Layer", completed_section)
        for phrase in ("Observations", "Punch item", "correspondence", "client credentials"):
            self.assertIn(phrase.lower(), unreleased_section.lower())
        self.assertIn("Phase 12", unreleased_section)
        self.assertIn("AI Workflow Examples", unreleased_section)
        self.assertIn("vector export", unreleased_section)
        self.assertIn("engineering context", unreleased_section)
        self.assertIn("Phase 10A", unreleased_section)
        self.assertIn("Async Client Foundation", unreleased_section)
        self.assertIn("Phase 10B", unreleased_section)
        self.assertIn("Async Exports And File Download Patterns", unreleased_section)
        self.assertIn("Async CSV and JSONL export helpers", unreleased_section)
        self.assertIn("Phase 10C", unreleased_section)
        self.assertIn("Async Multi-Project Operations", unreleased_section)
        self.assertIn("AsyncBatchPlan", unreleased_section)
        self.assertIn("Phase 11A", unreleased_section)
        self.assertIn("Plugin Architecture Foundation", unreleased_section)
        self.assertIn("Metadata-only plugin manifest", unreleased_section)
        self.assertIn("Phase 11B", unreleased_section)
        self.assertIn("Safe Local Plugin Extension Hooks", unreleased_section)
        self.assertIn("explicit in-process registration", unreleased_section.lower())
        self.assertIn("Phase 11C", unreleased_section)
        self.assertIn("Plugin Configuration and Local Extension Packs", unreleased_section)
        self.assertIn("json-only plugin configuration", unreleased_section.lower())
        self.assertNotIn("Async exports", future_section)
        self.assertNotIn("Async downloads", future_section)
        self.assertNotIn("Richer async batch orchestration", future_section)

        for phrase in (
            "trusted plugin",
            "golden datasets",
            "richer MCP integration",
        ):
            self.assertIn(phrase.lower(), future_section.lower())
            self.assertNotIn(phrase, completed_section)

    def test_changelog_has_released_2_2_0_section(self) -> None:
        """Changelog should place Phase 7 release notes under 2.2.0."""
        changelog = self.read_text("CHANGELOG.md")
        section_2_2 = changelog.split("## [2.2.0] - 2026-07-12", 1)[1].split(
            "## [2.1.0] - 2026-07-11",
            1,
        )[0]
        section_2_1 = changelog.split("## [2.1.0] - 2026-07-11", 1)[1]

        self.assertIn("published to PyPI", section_2_2)
        self.assertIn("Phase 7A agent tool registry", section_2_2)
        self.assertIn("Phase 7F local deterministic agent eval harness", section_2_2)
        self.assertNotIn("Phase 7A", section_2_1)
        self.assertNotIn("Phase 7F", section_2_1)

    def test_examples_readme_documents_agent_examples_as_released(self) -> None:
        """Examples README should describe 53-63 as v2.2.0 agent examples."""
        examples = self.read_text("examples/README.md")

        self.assertIn("Examples `01` through `52`", examples)
        self.assertIn("Examples `53` through `63`", examples)
        self.assertIn("Examples `64` through `69`", examples)
        self.assertIn("Examples `70` through `73`", examples)
        self.assertIn("Examples `131` through `140`", examples)
        self.assertIn("Examples `141` through `146`", examples)
        self.assertIn("Examples `147` through `152`", examples)
        self.assertIn("Examples `153` through `160`", examples)
        self.assertIn("Examples `177` through `184`", examples)
        self.assertIn("Examples `185` through `192`", examples)
        self.assertIn("cover the `v2.2.0` Phase 7", examples)
        self.assertIn("do not require Procore credentials or execute tools", examples)
        self.assertIn("client credentials auth", examples)
        self.assertNotIn("prepared for `2.2.0`", examples)

    def test_docs_do_not_claim_unpublished_state_or_execution_enabled(self) -> None:
        """Docs should not keep stale pre-release or unsafe execution claims."""
        docs = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [PROJECT_ROOT / "README.md", PROJECT_ROOT / "CHANGELOG.md"]
            + sorted((PROJECT_ROOT / "docs").rglob("*.md"))
            + [PROJECT_ROOT / "examples" / "README.md"]
        )

        forbidden = (
            "2.2.0 has not been published",
            "2.2.0 is prepared",
            "prepared next release",
            "current stable PyPI release: `2.1.0`",
            "tool execution enabled",
            "MCP execution enabled",
            "live Procore verification complete",
            "GitHub token limitation",
            "local token warning",
        )
        for phrase in forbidden:
            self.assertNotIn(phrase, docs)

    def test_docs_truth_audit_script_and_make_target_exist(self) -> None:
        """Docs truth audit script and Makefile target should be present."""
        self.assertTrue((PROJECT_ROOT / "scripts/audit_docs_truth.py").exists())
        makefile = self.read_text("Makefile")

        self.assertIn("docs-truth-check", makefile)
        self.assertIn("scripts/audit_docs_truth.py", makefile)


if __name__ == "__main__":
    unittest.main()
