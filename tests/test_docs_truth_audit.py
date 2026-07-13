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
        """Package and pyproject versions should be prepared as 2.2.0."""
        pyproject = tomllib.loads(self.read_text("pyproject.toml"))

        self.assertEqual(pyprocore.__version__, "2.2.0")
        self.assertEqual(pyproject["project"]["version"], "2.2.0")

    def test_cli_version_returns_2_2_0(self) -> None:
        """The CLI version output should reflect the prepared source version."""
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

    def test_readme_distinguishes_stable_and_prepared_versions(self) -> None:
        """README should distinguish published stable 2.1.0 from prepared 2.2.0."""
        readme = self.read_text("README.md")

        self.assertIn("Published stable PyPI release: `2.1.0`", readme)
        self.assertIn("Prepared next release: `2.2.0`", readme)
        self.assertIn("python3 -m pip install pyprocore==2.1.0", readme)
        self.assertIn("python3 -m pip install pyprocore==2.2.0", readme)
        self.assertIn("MCP tool execution remains disabled", readme)
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

        self.assertIn("Published stable release: `2.1.0`", status)
        self.assertIn("Prepared next release: `2.2.0`", status)
        self.assertIn("Tool execution remains disabled", status)
        self.assertIn("MCP adapter remains discovery-only", status)
        self.assertIn("project-status.md", mkdocs)
        self.assertIn("[Project Status](project-status.md)", index)
        self.assertNotIn("final-release-readiness.md", mkdocs)
        self.assertFalse((PROJECT_ROOT / "docs/final-release-readiness.md").exists())

    def test_roadmap_marks_phase_7_prepared_for_2_2_0(self) -> None:
        """Roadmap should show Phase 7 as completed and prepared for 2.2.0."""
        roadmap = self.read_text("docs/roadmap.md")

        self.assertIn("Released in 2.1.0", roadmap)
        self.assertIn("Prepared for 2.2.0", roadmap)
        self.assertIn("Phase 7A: Agent Tool Registry", roadmap)
        self.assertIn("Tool execution remains disabled", roadmap)

    def test_public_roadmap_does_not_mark_future_ideas_complete(self) -> None:
        """README and roadmap should not list unimplemented ideas as completed."""
        public_roadmap_text = "\n".join(
            [
                self.read_text("README.md"),
                self.read_text("docs/roadmap.md"),
            ]
        )

        for phrase in (
            "Async client",
            "Observations",
            "Correspondence",
            "plugin architecture",
            "Vector database examples",
            "Engineering assistant examples",
        ):
            self.assertNotIn(phrase, public_roadmap_text)

    def test_changelog_has_phase_7_under_2_2_0_not_2_1_0(self) -> None:
        """Changelog should place Phase 7 release notes under 2.2.0."""
        changelog = self.read_text("CHANGELOG.md")
        section_2_2 = changelog.split("## [2.2.0] - 2026-07-12", 1)[1].split(
            "## [2.1.0] - 2026-07-11",
            1,
        )[0]
        section_2_1 = changelog.split("## [2.1.0] - 2026-07-11", 1)[1]

        self.assertIn("Phase 7A agent tool registry", section_2_2)
        self.assertIn("Phase 7F local deterministic agent eval harness", section_2_2)
        self.assertNotIn("Phase 7A", section_2_1)
        self.assertNotIn("Phase 7F", section_2_1)

    def test_examples_readme_separates_stable_and_agent_examples(self) -> None:
        """Examples README should separate 2.1.0-era and 2.2.0 agent examples."""
        examples = self.read_text("examples/README.md")

        self.assertIn("Examples `01` through `52`", examples)
        self.assertIn("Examples `53` through `63`", examples)
        self.assertIn("prepared for `2.2.0`", examples)
        self.assertIn("do not require Procore credentials or execute tools", examples)

    def test_docs_do_not_claim_2_2_0_is_published_or_execution_enabled(self) -> None:
        """Docs should not overstate publication, live verification, or execution."""
        docs = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [PROJECT_ROOT / "README.md", PROJECT_ROOT / "CHANGELOG.md"]
            + sorted((PROJECT_ROOT / "docs").rglob("*.md"))
            + [PROJECT_ROOT / "examples" / "README.md"]
        )

        forbidden = (
            "2.2.0 has been published",
            "2.1.0 includes Phase 7",
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
