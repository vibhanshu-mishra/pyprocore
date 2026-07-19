"""Tests for Phase 11D safe plugin developer scaffolding."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pyprocore
from pyprocore.app import (
    format_plugin_scaffold_plan,
    format_plugin_scaffold_result,
)
from pyprocore.app import main as cli_main
from pyprocore.plugins import (
    PluginScaffoldFile,
    PluginScaffoldPlan,
    PluginScaffoldRequest,
    PluginScaffoldResult,
    PluginTemplateKind,
    build_plugin_scaffold_plan,
    export_plugin_scaffold_sample_plan,
    render_plugin_template,
    render_scaffold_extension_pack_template,
    render_scaffold_hook_manifest_template,
    render_scaffold_plugin_config_template,
    render_template,
    scaffold_extension_pack,
    scaffold_hook_pack,
    scaffold_plugin_config,
    scaffold_plugin_pack,
    scaffold_result_to_jsonable,
    validate_plugin_scaffold_request,
    write_scaffold_plan,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TEMPLATE_TEXT = (
    "access_token",
    "refresh_token",
    "client_secret",
    "authorization:",
    "bearer ",
    "importlib",
    "subprocess",
    "eval(",
    "exec(",
    "pip install",
    "curl ",
    "wget ",
    "create_procore",
    "update_procore",
    "delete_procore",
    "upload_procore",
    "approve_procore",
    "reject_procore",
    "submit_procore",
    "payment_procore",
)


class Phase11DPluginScaffoldingTests(unittest.TestCase):
    """Validate local template scaffolding stays safe and deterministic."""

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run the PyProcore CLI locally without credentials."""
        env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        return subprocess.run(
            [sys.executable, "-m", "pyprocore.app", *args],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_cli_in_process(self, *args: str) -> tuple[int, str]:
        """Run the PyProcore CLI in-process so scaffold branches count in coverage."""
        output = StringIO()
        with patch.object(sys, "argv", ["procore-sdk", *args]), redirect_stdout(output):
            try:
                cli_main()
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 1
            else:
                code = 0
        return code, output.getvalue()

    def test_scaffold_request_construction_and_sample_plan(self) -> None:
        """Scaffold request and sample plan should be serializable."""
        request = PluginScaffoldRequest(
            name="example_local_plugin",
            output_dir=Path("local-output"),
        )
        plan = export_plugin_scaffold_sample_plan()

        self.assertEqual(request.kind, PluginTemplateKind.FULL_PACK)
        self.assertIsInstance(plan, PluginScaffoldPlan)
        self.assertEqual(plan.request.name, "example_local_plugin")
        self.assertGreaterEqual(len(plan.files), 1)
        self.assertEqual(pyprocore.PluginTemplateKind.FULL_PACK.value, "full_pack")

    def test_invalid_name_output_url_and_path_traversal_are_rejected(self) -> None:
        """Unsafe scaffold names and paths should produce validation findings."""
        invalid_name = validate_plugin_scaffold_request(
            PluginScaffoldRequest(name="../bad", output_dir=Path("safe"))
        )
        path_traversal = validate_plugin_scaffold_request(
            PluginScaffoldRequest(name="safe_plugin", output_dir=Path("../bad"))
        )
        remote = validate_plugin_scaffold_request(
            PluginScaffoldRequest(name="safe_plugin", output_dir=Path("https://bad.invalid/x"))
        )

        self.assertTrue(any(finding.severity == "error" for finding in invalid_name))
        self.assertTrue(any("path traversal" in finding.message for finding in path_traversal))
        self.assertTrue(any("local filesystem" in finding.message for finding in remote))

    def test_dry_run_plan_generation_writes_no_files(self) -> None:
        """Dry-run mode should render a plan without creating files."""
        with tempfile.TemporaryDirectory() as raw_directory:
            output_dir = Path(raw_directory) / "plugin"
            result = scaffold_plugin_pack("example_local_plugin", output_dir, dry_run=True)

            self.assertIsInstance(result, PluginScaffoldResult)
            self.assertTrue(result.dry_run)
            self.assertEqual(result.written_count, 0)
            self.assertFalse(output_dir.exists())

    def test_create_writes_expected_files_and_parent_directories(self) -> None:
        """Create mode should write only template files under output_dir."""
        with tempfile.TemporaryDirectory() as raw_directory:
            output_dir = Path(raw_directory) / "plugin"
            result = scaffold_plugin_pack("example_local_plugin", output_dir, dry_run=False)

            self.assertEqual(result.written_count, 9)
            self.assertTrue((output_dir / "plugin_manifest.json").exists())
            self.assertTrue((output_dir / "docs" / "plugin-pack.md").exists())
            self.assertTrue((output_dir / "tests" / "test_plugin_manifest.py").exists())

    def test_overwrite_false_skips_and_overwrite_true_replaces(self) -> None:
        """Existing scaffold files should be skipped unless overwrite is explicit."""
        with tempfile.TemporaryDirectory() as raw_directory:
            output_dir = Path(raw_directory)
            scaffold_plugin_config("example_local_plugin", output_dir, dry_run=False)
            config_path = output_dir / "plugin_config.json"
            config_path.write_text("custom", encoding="utf-8")

            skipped = scaffold_plugin_config("example_local_plugin", output_dir, dry_run=False)
            replaced = scaffold_plugin_config(
                "example_local_plugin",
                output_dir,
                overwrite=True,
                dry_run=False,
            )

            self.assertEqual(skipped.skipped_count, 1)
            self.assertEqual(config_path.read_text(encoding="utf-8"), replaced.files[0].content)

    def test_kind_specific_scaffolds(self) -> None:
        """Extension, config, and hook scaffolds should write one safe file each."""
        with tempfile.TemporaryDirectory() as raw_directory:
            root = Path(raw_directory)
            extension = scaffold_extension_pack(
                "example_local_plugin", root / "pack", dry_run=False
            )
            config = scaffold_plugin_config("example_local_plugin", root / "config", dry_run=False)
            hook = scaffold_hook_pack("example_local_plugin", root / "hook", dry_run=False)

            self.assertEqual(extension.written_count, 1)
            self.assertTrue((root / "pack" / "extension_pack_manifest.json").exists())
            self.assertEqual(config.written_count, 1)
            self.assertTrue((root / "config" / "plugin_config.json").exists())
            self.assertEqual(hook.written_count, 1)
            self.assertTrue((root / "hook" / "hook_manifest.json").exists())

    def test_write_scaffold_plan_returns_errors_for_invalid_plan(self) -> None:
        """Invalid plans should not write files."""
        with tempfile.TemporaryDirectory() as raw_directory:
            output_dir = Path(raw_directory) / "bad"
            plan = build_plugin_scaffold_plan(
                PluginScaffoldRequest(name="../bad", output_dir=output_dir, dry_run=False)
            )
            result = write_scaffold_plan(plan)

            self.assertEqual(result.written_count, 0)
            self.assertTrue(result.findings)
            self.assertFalse(output_dir.exists())

    def test_result_json_serialization_and_secret_redaction(self) -> None:
        """Result metadata should serialize and redact unsafe secret-like text."""
        result = scaffold_plugin_pack(
            "example_local_plugin",
            Path("safe"),
            description="client_secret=raw-value",
            dry_run=True,
        )
        payload = scaffold_result_to_jsonable(result)
        text = json.dumps(payload)

        self.assertIn("findings", payload)
        self.assertIn("[REDACTED]", text)
        self.assertNotIn("raw-value", text)

    def test_generated_templates_are_safe_static_text(self) -> None:
        """Generated template text should not include dangerous execution patterns."""
        texts = [
            render_plugin_template("example_local_plugin"),
            render_scaffold_plugin_config_template("example_local_plugin"),
            render_scaffold_extension_pack_template("example_local_plugin"),
            render_scaffold_hook_manifest_template("example_local_plugin"),
        ]
        texts.extend(
            render_template(kind, "example_local_plugin")
            for kind in [
                PluginTemplateKind.PLUGIN_MANIFEST,
                PluginTemplateKind.PLUGIN_CONFIG,
                PluginTemplateKind.EXTENSION_PACK,
                PluginTemplateKind.HOOK_MANIFEST,
                PluginTemplateKind.README,
                PluginTemplateKind.CHANGELOG,
                PluginTemplateKind.TESTS,
                PluginTemplateKind.DOCS,
                PluginTemplateKind.EXAMPLE,
            ]
        )
        plan = export_plugin_scaffold_sample_plan()
        texts.extend(file.content for file in plan.files)

        combined = "\n".join(texts).casefold()
        for fragment in FORBIDDEN_TEMPLATE_TEXT:
            self.assertNotIn(fragment, combined)
        self.assertNotIn("https://", combined)

    def test_cli_scaffold_commands(self) -> None:
        """CLI scaffold commands should run locally without credentials."""
        with tempfile.TemporaryDirectory() as raw_directory:
            root = Path(raw_directory)
            sample = self.run_cli("plugins", "scaffold", "sample-plan")
            dry_run = self.run_cli(
                "plugins",
                "scaffold",
                "dry-run",
                "--name",
                "example_local_plugin",
                "--output-dir",
                str(root / "dry"),
            )
            create = self.run_cli(
                "plugins",
                "scaffold",
                "create",
                "--name",
                "example_local_plugin",
                "--output-dir",
                str(root / "create"),
            )
            extension = self.run_cli(
                "plugins",
                "scaffold",
                "extension-pack",
                "--name",
                "example_local_plugin",
                "--output-dir",
                str(root / "extension"),
            )
            config = self.run_cli(
                "plugins",
                "scaffold",
                "config",
                "--name",
                "example_local_plugin",
                "--output-dir",
                str(root / "config"),
            )
            hook = self.run_cli(
                "plugins",
                "scaffold",
                "hook-pack",
                "--name",
                "example_local_plugin",
                "--output-dir",
                str(root / "hook"),
            )

            for completed in [sample, dry_run, create, extension, config, hook]:
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertNotIn("Traceback", completed.stderr + completed.stdout)
            self.assertTrue((root / "create" / "plugin_manifest.json").exists())
            self.assertTrue((root / "extension" / "extension_pack_manifest.json").exists())
            self.assertTrue((root / "config" / "plugin_config.json").exists())
            self.assertTrue((root / "hook" / "hook_manifest.json").exists())

    def test_cli_scaffold_commands_in_process(self) -> None:
        """In-process CLI scaffold commands should format safe local results."""
        with tempfile.TemporaryDirectory() as raw_directory:
            root = Path(raw_directory)
            commands = [
                ("plugins", "scaffold", "sample-plan"),
                ("plugins", "scaffold", "sample-plan", "--json"),
                (
                    "plugins",
                    "scaffold",
                    "dry-run",
                    "--name",
                    "example_local_plugin",
                    "--output-dir",
                    str(root / "dry"),
                    "--kind",
                    PluginTemplateKind.README.value,
                ),
                (
                    "plugins",
                    "scaffold",
                    "create",
                    "--name",
                    "example_local_plugin",
                    "--output-dir",
                    str(root / "create"),
                    "--kind",
                    PluginTemplateKind.TESTS.value,
                ),
                (
                    "plugins",
                    "scaffold",
                    "extension-pack",
                    "--name",
                    "example_local_plugin",
                    "--output-dir",
                    str(root / "extension"),
                    "--json",
                ),
                (
                    "plugins",
                    "scaffold",
                    "config",
                    "--name",
                    "example_local_plugin",
                    "--output-dir",
                    str(root / "config"),
                ),
                (
                    "plugins",
                    "scaffold",
                    "hook-pack",
                    "--name",
                    "example_local_plugin",
                    "--output-dir",
                    str(root / "hook"),
                    "--pretty",
                ),
            ]

            for command in commands:
                code, output = self.run_cli_in_process(*command)
                self.assertEqual(code, 0, output)
                self.assertIn("example_local_plugin", output)
                self.assertNotIn("Traceback", output)

            invalid_code, invalid_output = self.run_cli_in_process(
                "plugins",
                "scaffold",
                "dry-run",
                "--name",
                "../bad",
                "--output-dir",
                str(root / "bad"),
            )

            self.assertEqual(invalid_code, 1)
            self.assertIn("ERROR", invalid_output)
            self.assertIn("safe lowercase", invalid_output)
            self.assertFalse((root / "bad").exists())
            self.assertTrue((root / "create" / "tests" / "test_plugin_manifest.py").exists())

    def test_scaffold_formatters_and_edge_paths(self) -> None:
        """Formatter and path-safety branches should stay beginner-friendly."""
        with tempfile.TemporaryDirectory() as raw_directory:
            root = Path(raw_directory)
            plan = export_plugin_scaffold_sample_plan()
            dry_result = scaffold_plugin_pack(
                "example_local_plugin",
                root / "dry",
                kind=PluginTemplateKind.PLUGIN_MANIFEST,
                description="Metadata-only scaffold",
                dry_run=True,
            )
            create_result = scaffold_plugin_pack(
                "example_local_plugin",
                root / "docs",
                kind=PluginTemplateKind.DOCS,
                dry_run=False,
            )
            escaped_plan = PluginScaffoldPlan(
                request=PluginScaffoldRequest(
                    name="example_local_plugin",
                    output_dir=root / "safe",
                    dry_run=False,
                ),
                files=[
                    PluginScaffoldFile(
                        path=str(root / "outside.md"),
                        template_kind=PluginTemplateKind.README,
                        content="safe static text",
                    )
                ],
            )
            escaped_result = write_scaffold_plan(escaped_plan)
            unsafe_action = validate_plugin_scaffold_request(
                PluginScaffoldRequest(
                    name="example_local_plugin",
                    output_dir=root / "safe",
                    description="approve" + "_procore helper",
                )
            )

            self.assertIn("Files planned", format_plugin_scaffold_plan(plan))
            self.assertIn("Files written: 0", format_plugin_scaffold_result(dry_result))
            self.assertIn("Files written: 1", format_plugin_scaffold_result(create_result))
            self.assertEqual(escaped_result.written_count, 0)
            self.assertTrue(any(finding.severity == "error" for finding in escaped_result.findings))
            self.assertTrue(any("write-action" in finding.message for finding in unsafe_action))

    def test_examples_and_sample_scaffolds_exist(self) -> None:
        """Phase 11D examples and sample scaffold files should be present."""
        for number in range(201, 209):
            matches = list((PROJECT_ROOT / "examples").glob(f"{number}_*.py"))
            self.assertEqual(len(matches), 1, f"missing example {number}")
            text = matches[0].read_text(encoding="utf-8")
            self.assertIn('if __name__ == "__main__":', text)

        sample_dir = PROJECT_ROOT / "examples" / "plugin_scaffolds"
        for name in [
            "README.md",
            "basic_plugin_manifest.json",
            "basic_plugin_config.json",
            "basic_extension_pack.json",
            "basic_hook_manifest.json",
        ]:
            self.assertTrue((sample_dir / name).exists(), name)

    def test_docs_and_source_keep_phase11d_safety_boundaries(self) -> None:
        """Docs and source should not add plugin install, fetch, or execution paths."""
        docs = "\n".join(
            [
                (PROJECT_ROOT / "README.md").read_text(encoding="utf-8"),
                (PROJECT_ROOT / "docs" / "plugins.md").read_text(encoding="utf-8"),
                (PROJECT_ROOT / "docs" / "roadmap.md").read_text(encoding="utf-8"),
            ]
        )
        app_text = (PROJECT_ROOT / "pyprocore" / "app.py").read_text(encoding="utf-8")
        plugin_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (PROJECT_ROOT / "pyprocore" / "plugins").glob("*.py")
        )

        self.assertIn("Phase 11D", docs)
        self.assertIn("plugin developer scaffolding", docs.casefold())
        self.assertNotIn("plugins install", app_text)
        self.assertNotIn("plugins run ", app_text)
        self.assertNotIn("importlib.import_module", plugin_source)
        self.assertNotIn("subprocess", plugin_source)
        self.assertNotIn("eval(", plugin_source)
        self.assertNotIn("exec(", plugin_source)
        self.assertNotIn("pip install", plugin_source)

    def test_no_workflow_changes_and_execution_remains_disabled(self) -> None:
        """Phase 11D should not touch workflows or enable tool execution."""
        workflow_diff = subprocess.run(
            ["git", "diff", "--name-only", ".github/workflows"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        agent_openapi = (PROJECT_ROOT / "pyprocore" / "agent" / "openapi.py").read_text(
            encoding="utf-8"
        )

        self.assertEqual(workflow_diff.stdout.strip(), "")
        self.assertIn('"tool_execution_enabled": False', agent_openapi)
