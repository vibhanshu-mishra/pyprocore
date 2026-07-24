"""Tests for Phase 17E optional FastAPI read API starter templates."""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pyprocore
from pyprocore import app as cli_app
from pyprocore.core.exceptions import NotFoundError
from pyprocore.templates import (
    copy_starter_template,
    get_starter_template,
    list_starter_templates,
    template_copy_result_to_markdown,
    template_metadata_to_json,
    template_metadata_to_markdown,
    templates_to_markdown,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase17EFastApiStarterTemplateTests(unittest.TestCase):
    """Validate safe static starter template behavior."""

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run the local CLI without credentials."""
        env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        return subprocess.run(
            [sys.executable, "-m", "pyprocore.app", *args],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_template_registry_lists_fastapi_read_api(self) -> None:
        """The starter template registry should include the FastAPI read API template."""
        templates = list_starter_templates()
        names = {template.name for template in templates}
        template = get_starter_template("fastapi-read-api")

        self.assertIn("fastapi-read-api", names)
        self.assertEqual(template.category, "optional_backend_example")
        self.assertIn("GET /health", template.read_only_routes)
        self.assertFalse(template.procore_api_call_required)
        self.assertFalse(template.external_ai_call_required)
        self.assertFalse(template.mcp_execution_enabled)
        self.assertFalse(template.procore_write_actions_enabled)
        with self.assertRaises(NotFoundError):
            get_starter_template("missing-template")

    def test_template_metadata_renders_json_and_markdown(self) -> None:
        """Template reports should render without importing FastAPI or calling Procore."""
        template = get_starter_template("fastapi-read-api")
        payload = json.loads(template_metadata_to_json(template, pretty=True))
        markdown = template_metadata_to_markdown(template)
        inventory = templates_to_markdown(list_starter_templates())

        self.assertEqual(payload["name"], "fastapi-read-api")
        self.assertIn("FastAPI is optional", markdown)
        self.assertIn("Procore write actions enabled: false", markdown)
        self.assertIn("Copy only", inventory)

    def test_copy_dry_run_and_copy_write_expected_files(self) -> None:
        """Dry-run should not write files, while copy should write static files locally."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "starter"
            dry_run = copy_starter_template("fastapi-read-api", output_dir, dry_run=True)
            self.assertEqual(dry_run.written_count, 0)
            self.assertFalse((output_dir / "README.md").exists())

            result = copy_starter_template("fastapi-read-api", output_dir)
            self.assertGreaterEqual(result.written_count, 13)
            self.assertTrue((output_dir / "README.md").exists())
            self.assertTrue((output_dir / "app" / "main.py").exists())
            self.assertTrue((output_dir / "app" / "routes" / "health.py").exists())
            self.assertIn("No Procore writes", (output_dir / "README.md").read_text())

    def test_copy_refuses_overwrite_by_default_and_allows_explicit_overwrite(self) -> None:
        """Existing files should be skipped unless overwrite is explicitly requested."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "starter"
            copy_starter_template("fastapi-read-api", output_dir)
            readme = output_dir / "README.md"
            readme.write_text("custom local edit", encoding="utf-8")

            skipped = copy_starter_template("fastapi-read-api", output_dir)
            self.assertGreater(skipped.skipped_count, 0)
            self.assertEqual(readme.read_text(encoding="utf-8"), "custom local edit")

            overwritten = copy_starter_template("fastapi-read-api", output_dir, overwrite=True)
            self.assertGreater(overwritten.written_count, 0)
            self.assertIn("PyProcore FastAPI Read API Starter", readme.read_text(encoding="utf-8"))

    def test_copy_blocks_path_traversal_and_remote_outputs(self) -> None:
        """Copy helpers should reject traversal and remote-looking output paths."""
        traversal = copy_starter_template("fastapi-read-api", Path("..") / "bad")
        remote = copy_starter_template("fastapi-read-api", "https://example.com/template")

        self.assertTrue(any(finding.severity == "error" for finding in traversal.findings))
        self.assertTrue(any(finding.severity == "error" for finding in remote.findings))
        self.assertIn("ERROR", template_copy_result_to_markdown(traversal))

    def test_cli_template_commands_work_without_credentials(self) -> None:
        """Template CLI commands should be local-only and credential-free."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "starter"
            commands = [
                ("templates", "list"),
                ("templates", "list", "--json"),
                ("templates", "show", "fastapi-read-api"),
                ("templates", "show", "fastapi-read-api", "--format", "json"),
                (
                    "templates",
                    "copy",
                    "fastapi-read-api",
                    "--output-dir",
                    str(output_dir),
                    "--dry-run",
                ),
            ]
            for command in commands:
                completed = self.run_cli(*command)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertNotIn("Traceback", completed.stderr + completed.stdout)

    def test_cli_template_commands_in_process(self) -> None:
        """In-process CLI branches should format template results for coverage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "starter"
            commands = [
                ("templates", "list"),
                ("templates", "show", "fastapi-read-api"),
                (
                    "templates",
                    "copy",
                    "fastapi-read-api",
                    "--output-dir",
                    str(output_dir),
                    "--dry-run",
                ),
            ]
            for command in commands:
                with self.subTest(command=command):
                    buffer = io.StringIO()
                    with patch_argv(command), contextlib.redirect_stdout(buffer):
                        if command[1] == "copy":
                            with self.assertRaises(SystemExit) as exit_context:
                                cli_app.main()
                            self.assertEqual(exit_context.exception.code, 0)
                        else:
                            cli_app.main()
                    self.assertRegex(buffer.getvalue(), r"fastapi-read-api|FastAPI Read API")

    def test_static_template_contains_no_real_secrets_or_write_routes(self) -> None:
        """Generated template content should preserve explicit safety boundaries."""
        template = get_starter_template("fastapi-read-api")
        combined = "\n".join(file.content for file in template.files).casefold()

        forbidden = [
            "real_client_secret",
            "real_access_token",
            "bearer ey",
            "@router.post",
            "@router.patch",
            "@router.put",
            "@router.delete",
            "subprocess",
            "openai",
            "anthropic",
            'mcp execution enabled": true',
        ]
        for phrase in forbidden:
            self.assertNotIn(phrase, combined)
        self.assertIn("no procore write", combined)
        self.assertIn("no external ai/model calls", combined)
        self.assertIn("tests use mocked clients", combined)

    def test_examples_docs_and_dependencies_stay_safe(self) -> None:
        """Docs, examples, and package metadata should describe optional template scope."""
        pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8").casefold()
        docs = (PROJECT_ROOT / "docs" / "fastapi-starter.md").read_text(encoding="utf-8")
        examples_readme = (PROJECT_ROOT / "examples" / "README.md").read_text(encoding="utf-8")
        template_readme = (
            PROJECT_ROOT / "examples" / "templates" / "fastapi_read_api" / "README.md"
        ).read_text(encoding="utf-8")

        self.assertNotIn('"fastapi', pyproject)
        self.assertNotIn('"uvicorn', pyproject)
        self.assertIn("FastAPI is not a PyProcore dependency", docs)
        self.assertIn("No Procore writes are enabled", docs)
        self.assertIn("301_template_inventory.py", examples_readme)
        self.assertIn("This folder is a copied starter template", template_readme)

    def test_package_root_exports_template_helpers(self) -> None:
        """Package root exports should include additive template helpers."""
        self.assertEqual(
            pyprocore.get_starter_template("fastapi-read-api").name, "fastapi-read-api"
        )
        self.assertTrue(callable(pyprocore.copy_starter_template))


class patch_argv:
    """Small context manager for in-process CLI argument patching."""

    def __init__(self, command: tuple[str, ...]) -> None:
        """Store the CLI command to patch into ``sys.argv``."""
        self.command = command
        self.original: list[str] = []

    def __enter__(self) -> None:
        """Patch ``sys.argv``."""
        self.original = list(sys.argv)
        sys.argv = ["procore-sdk", *self.command]

    def __exit__(self, *exc_info: object) -> None:
        """Restore ``sys.argv``."""
        sys.argv = self.original


if __name__ == "__main__":
    unittest.main()
