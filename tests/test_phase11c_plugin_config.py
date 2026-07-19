"""Tests for Phase 11C plugin config and local extension-pack metadata."""

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
    format_extension_pack,
    format_extension_pack_validation,
    format_plugin_config,
    format_plugin_config_manifest,
    format_plugin_config_validation,
)
from pyprocore.app import main as cli_main
from pyprocore.core.exceptions import ValidationError
from pyprocore.plugins import (
    PluginCapability,
    PluginConfig,
    PluginConfigSummary,
    PluginExtensionPack,
    PluginHookPreference,
    PluginHookRegistry,
    PluginHookType,
    PluginRegistry,
    builtin_hook_registry,
    discover_builtin_plugins,
    export_extension_pack_template,
    export_plugin_config_template,
    load_extension_pack_manifest_from_dict,
    load_extension_pack_manifest_from_file,
    load_plugin_config_from_dict,
    load_plugin_config_from_file,
    merge_plugin_config_with_registry_metadata,
    validate_extension_pack_manifest,
    validate_extension_pack_manifest_data,
    validate_plugin_config,
    validate_plugin_config_data,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase11CPluginConfigTests(unittest.TestCase):
    """Validate safe plugin config and extension-pack support."""

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
        """Run the CLI in-process so coverage records the render branch."""
        output = StringIO()
        with patch.object(sys, "argv", ["procore-sdk", *args]), redirect_stdout(output):
            try:
                cli_main()
            except SystemExit as exc:
                code = int(exc.code) if isinstance(exc.code, int) else 1
            else:
                code = 0
        return code, output.getvalue()

    def write_json(self, directory: Path, name: str, data: dict[str, object]) -> Path:
        """Write JSON test data under a temporary directory."""
        path = directory / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_plugin_config_construction_and_template_validation(self) -> None:
        """Plugin config models should be JSON-serializable and valid."""
        config = export_plugin_config_template()
        result = validate_plugin_config(config)

        self.assertIsInstance(config, PluginConfig)
        self.assertTrue(result.valid, result.errors)
        self.assertIn("metadata_only", config.model_dump_json())
        self.assertTrue(pyprocore.PluginConfig)

    def test_plugin_config_validation_rejects_unsafe_metadata(self) -> None:
        """Plugin config validation should reject unsafe local metadata."""
        unsafe = load_plugin_config_from_dict(
            {
                "config_version": "2",
                "enabled_plugins": ["../bad", "delete_records"],
                "enabled_capabilities": ["exporter"],
                "hook_preferences": [
                    {
                        "hook_name": "../bad_hook",
                        "hook_type": "validator",
                    }
                ],
                "notes": ["access_token=secret-value", "from unsafe.module import thing"],
                "safety_policy": "execute_code",
            }
        )

        result = validate_plugin_config(unsafe)

        self.assertFalse(result.valid)
        self.assertIn("Unsupported plugin config version", " ".join(result.errors))
        self.assertIn("[REDACTED]", " ".join(result.errors))
        self.assertNotIn("secret-value", " ".join(result.errors))

    def test_plugin_config_data_validation_handles_bad_capability_and_hook_type(self) -> None:
        """Dictionary validation should catch unsupported enum values cleanly."""
        capability = validate_plugin_config_data(
            {"config_version": "1", "enabled_capabilities": ["unknown"]}
        )
        hook = validate_plugin_config_data(
            {
                "config_version": "1",
                "hook_preferences": [
                    {"hook_name": "validate_required_fields", "hook_type": "unknown"}
                ],
            }
        )

        self.assertFalse(capability.valid)
        self.assertFalse(hook.valid)

    def test_plugin_config_file_loading_and_path_safety(self) -> None:
        """Config loading should read JSON only and reject unsafe paths."""
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            config_path = self.write_json(
                directory,
                "plugin_config.json",
                {"config_version": "1", "enabled_plugins": ["csv_exporter_plugin"]},
            )
            invalid_json = directory / "invalid.json"
            invalid_json.write_text("{", encoding="utf-8")
            text_file = directory / "config.txt"
            text_file.write_text("{}", encoding="utf-8")

            config = load_plugin_config_from_file(config_path)

            self.assertEqual(config.enabled_plugins, ["csv_exporter_plugin"])
            with self.assertRaises(ValidationError):
                load_plugin_config_from_file(invalid_json)
            with self.assertRaises(ValidationError):
                load_plugin_config_from_file(text_file)
            with self.assertRaises(ValidationError):
                load_plugin_config_from_file("../bad.json")
            with self.assertRaises(ValidationError):
                load_plugin_config_from_file("https://example.invalid/config.json")

    def test_plugin_config_filters_registry_metadata_without_execution(self) -> None:
        """Config should filter known manifests without registering hook callables."""
        config = PluginConfig(
            enabled_plugins=["csv_exporter_plugin"],
            disabled_plugins=["jsonl_exporter_plugin"],
            enabled_capabilities=[PluginCapability.EXPORTER],
            hook_preferences=[
                PluginHookPreference(
                    hook_name="validate_required_fields",
                    hook_type=PluginHookType.VALIDATOR,
                )
            ],
            extension_packs=["starter_export_pack"],
        )
        registry = PluginRegistry(discover_builtin_plugins().discovered)
        hook_registry = PluginHookRegistry()
        summary = merge_plugin_config_with_registry_metadata(config, registry.list_plugins())

        self.assertIsInstance(summary, PluginConfigSummary)
        self.assertIn("csv_exporter_plugin", summary.matched_plugins)
        self.assertNotIn("jsonl_exporter_plugin", summary.matched_plugins)
        self.assertEqual(hook_registry.list_hooks(), [])

    def test_extension_pack_template_and_validation(self) -> None:
        """Extension packs should validate as metadata-only bundles."""
        extension_pack = export_extension_pack_template()
        result = validate_extension_pack_manifest(extension_pack)

        self.assertIsInstance(extension_pack, PluginExtensionPack)
        self.assertTrue(result.valid, result.errors)
        self.assertGreaterEqual(len(extension_pack.included_plugins), 1)

    def test_extension_pack_validation_rejects_unsafe_metadata(self) -> None:
        """Extension-pack validation should reject unsafe metadata."""
        extension_pack = load_extension_pack_manifest_from_dict(
            {
                "schema_version": "2",
                "name": "../bad",
                "version": "not-semver",
                "description": "",
                "included_plugins": [{"plugin_name": "../bad"}],
                "included_hooks": [
                    {
                        "hook_name": "../bad_hook",
                        "plugin_name": "test_plugin",
                        "hook_type": "validator",
                        "description": "bad",
                    }
                ],
                "capabilities": ["exporter"],
                "notes": ["client_secret=raw-secret"],
                "safety_level": "local_file_output",
            }
        )

        result = validate_extension_pack_manifest(extension_pack)

        self.assertFalse(result.valid)
        self.assertIn("Unsupported extension-pack schema version", " ".join(result.errors))
        self.assertIn("[REDACTED]", " ".join(result.errors))
        self.assertNotIn("raw-secret", " ".join(result.errors))

    def test_extension_pack_data_validation_and_file_loading(self) -> None:
        """Extension-pack helpers should validate dictionaries and JSON files."""
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            pack = export_extension_pack_template()
            pack_path = self.write_json(
                directory,
                "extension_pack.json",
                pack.model_dump(mode="json"),
            )
            loaded = load_extension_pack_manifest_from_file(pack_path)
            invalid = validate_extension_pack_manifest_data(
                {"schema_version": "1", "name": "bad_pack", "capabilities": ["unknown"]}
            )

            self.assertEqual(loaded.name, pack.name)
            self.assertFalse(invalid.valid)
            with self.assertRaises(ValidationError):
                load_extension_pack_manifest_from_file("../bad.json")
            with self.assertRaises(ValidationError):
                load_extension_pack_manifest_from_file("https://example.invalid/pack.json")

    def test_formatters_are_human_readable_and_safe(self) -> None:
        """CLI formatter helpers should describe metadata-only behavior."""
        config = export_plugin_config_template()
        config_result = validate_plugin_config(config)
        registry = PluginRegistry(discover_builtin_plugins().discovered)
        config_summary = merge_plugin_config_with_registry_metadata(
            config,
            registry.list_plugins(),
        )
        extension_pack = export_extension_pack_template()
        pack_result = validate_extension_pack_manifest(extension_pack)

        self.assertIn("metadata only", format_plugin_config(config))
        self.assertIn("Valid: True", format_plugin_config_validation(config_result))
        self.assertIn("Matched plugins", format_plugin_config_manifest(config_summary))
        self.assertIn("metadata only", format_extension_pack(extension_pack))
        self.assertIn("Valid: True", format_extension_pack_validation(pack_result))

    def test_cli_plugin_config_and_extension_pack_commands(self) -> None:
        """Plugin config CLI commands should be local and credential-free."""
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            config_path = self.write_json(
                directory,
                "plugin_config.json",
                export_plugin_config_template().model_dump(mode="json"),
            )
            pack_path = self.write_json(
                directory,
                "extension_pack.json",
                export_extension_pack_template().model_dump(mode="json"),
            )
            cases = [
                (("plugins", "config", "sample"), "plugin configuration"),
                (("plugins", "config", "sample", "--json"), '"enabled_plugins"'),
                (("plugins", "config", "validate", str(config_path)), "Valid: True"),
                (("plugins", "config", "summary", str(config_path)), "metadata only"),
                (("plugins", "config", "manifest", str(config_path)), "Matched plugins"),
                (("plugins", "extension-pack", "sample"), "extension-pack manifest"),
                (("plugins", "extension-pack", "sample", "--json"), '"included_plugins"'),
                (
                    ("plugins", "extension-pack", "validate", str(pack_path)),
                    "Valid: True",
                ),
                (
                    ("plugins", "extension-pack", "summary", str(pack_path)),
                    "metadata only",
                ),
            ]
            for args, expected in cases:
                with self.subTest(args=args):
                    result = self.run_cli(*args)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(expected, result.stdout)
                    self.assertNotIn("Traceback", result.stdout)

    def test_cli_plugin_config_commands_render_in_process(self) -> None:
        """In-process CLI commands should cover Phase 11C rendering branches."""
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            config_path = self.write_json(
                directory,
                "plugin_config.json",
                export_plugin_config_template().model_dump(mode="json"),
            )
            invalid_config_path = self.write_json(
                directory,
                "invalid_plugin_config.json",
                {"config_version": "2", "enabled_plugins": ["../bad"]},
            )
            pack_path = self.write_json(
                directory,
                "extension_pack.json",
                export_extension_pack_template().model_dump(mode="json"),
            )
            invalid_pack_path = self.write_json(
                directory,
                "invalid_extension_pack.json",
                {
                    "schema_version": "2",
                    "name": "../bad",
                    "version": "bad",
                    "description": "",
                    "safety_level": "local_file_output",
                },
            )
            cases = [
                (("plugins", "config", "sample"), 0, "plugin configuration"),
                (("plugins", "config", "sample", "--json"), 0, '"enabled_plugins"'),
                (
                    ("plugins", "config", "validate", str(config_path)),
                    0,
                    "Valid: True",
                ),
                (
                    ("plugins", "config", "validate", str(invalid_config_path)),
                    1,
                    "Valid: False",
                ),
                (
                    ("plugins", "config", "summary", str(config_path)),
                    0,
                    "metadata only",
                ),
                (
                    ("plugins", "config", "manifest", str(config_path)),
                    0,
                    "Configured plugin metadata summary",
                ),
                (
                    ("plugins", "config", "manifest", str(config_path), "--json"),
                    0,
                    '"matched_plugins"',
                ),
                (
                    ("plugins", "extension-pack", "sample"),
                    0,
                    "extension-pack manifest",
                ),
                (
                    ("plugins", "extension-pack", "sample", "--json"),
                    0,
                    '"included_hooks"',
                ),
                (
                    ("plugins", "extension-pack", "validate", str(pack_path)),
                    0,
                    "Valid: True",
                ),
                (
                    ("plugins", "extension-pack", "validate", str(invalid_pack_path)),
                    1,
                    "Valid: False",
                ),
                (
                    ("plugins", "extension-pack", "summary", str(pack_path)),
                    0,
                    "metadata only",
                ),
            ]
            for args, expected_code, expected_text in cases:
                with self.subTest(args=args):
                    code, output = self.run_cli_in_process(*args)
                    self.assertEqual(code, expected_code, output)
                    self.assertIn(expected_text, output)
                    self.assertNotIn("Traceback", output)

    def test_sample_config_files_docs_and_examples_exist(self) -> None:
        """Sample files, docs, and examples should describe Phase 11C."""
        for filename in (
            "plugin_config_minimal.json",
            "plugin_config_hooks.json",
            "plugin_config_enterprise.json",
            "plugin_extension_pack_sample.json",
            "plugin_extension_pack_ai_workflows.json",
        ):
            path = PROJECT_ROOT / "examples" / "configs" / filename
            self.assertTrue(path.exists(), filename)
            json.loads(path.read_text(encoding="utf-8"))

        for index in range(193, 201):
            matching = sorted((PROJECT_ROOT / "examples").glob(f"{index}_*.py"))
            self.assertEqual(len(matching), 1, index)
            text = matching[0].read_text(encoding="utf-8")
            self.assertIn('if __name__ == "__main__":', text)

        docs = "\n".join(
            (PROJECT_ROOT / path).read_text(encoding="utf-8")
            for path in (
                "README.md",
                "CHANGELOG.md",
                "docs/plugins.md",
                "docs/cli.md",
                "docs/api-coverage.md",
                "docs/project-status.md",
                "docs/roadmap.md",
                "examples/README.md",
            )
        )
        self.assertIn("Phase 11C", docs)
        self.assertIn("JSON metadata", docs)

    def test_safety_boundaries_remain_enforced(self) -> None:
        """Phase 11C must not add unsafe loading, execution, or write behavior."""
        plugin_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((PROJECT_ROOT / "pyprocore" / "plugins").glob("*.py"))
        )
        app_text = (PROJECT_ROOT / "pyprocore" / "app.py").read_text(encoding="utf-8")

        for forbidden in (
            "requests.",
            "httpx",
            "urllib.request",
            "importlib.import_module",
            "subprocess",
            "eval(",
            "exec(",
            "pip install",
        ):
            self.assertNotIn(forbidden, plugin_text)
        self.assertNotIn("plugins install", app_text)
        self.assertNotIn("plugins run ", app_text)

        for forbidden in (
            "def create_",
            "def update_",
            "def delete_",
            "def upload_",
            "def approve_",
            "def reject_",
            "def submit_",
            "def payment_",
        ):
            self.assertNotIn(forbidden, plugin_text)

        before_hooks = len(builtin_hook_registry().list_hooks())
        validate_plugin_config(export_plugin_config_template())
        validate_extension_pack_manifest(export_extension_pack_template())
        after_hooks = len(builtin_hook_registry().list_hooks())
        self.assertEqual(before_hooks, after_hooks)

        workflow_diff = subprocess.run(
            ["git", "diff", "--name-only", ".github/workflows"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(workflow_diff.returncode, 0)
        self.assertEqual(workflow_diff.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
