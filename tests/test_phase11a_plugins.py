"""Tests for Phase 11A metadata-only plugin architecture."""

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
from unittest.mock import patch

import pyprocore
from pyprocore.app import (
    build_default_plugin_registry,
    build_parser,
    format_plugin,
    format_plugin_registry_manifest,
    format_plugin_validation,
    format_plugins,
    main,
    run_command,
    sample_plugin_manifest,
)
from pyprocore.core.exceptions import DuplicateMatchError, NotFoundError, ValidationError
from pyprocore.plugins import (
    PLUGIN_SCHEMA_VERSION,
    PluginCapability,
    PluginManifest,
    PluginRegistry,
    discover_builtin_plugins,
    discover_installed_plugin_metadata,
    discover_local_plugin_manifests,
    discover_plugins,
    export_plugin_registry_manifest,
    find_plugins_by_capability,
    get_plugin,
    list_plugins,
    load_local_plugin_manifest_file,
    register_plugin_manifest,
    unregister_plugin,
    validate_plugin_manifest,
    validate_plugin_manifest_data,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase11APluginTests(unittest.TestCase):
    """Validate safe metadata-only plugin support."""

    def manifest(self, *, name: str = "example_plugin") -> PluginManifest:
        """Build a valid test plugin manifest."""
        return PluginManifest(
            name=name,
            version="1.0.0",
            description="Example metadata-only plugin.",
            capabilities=[PluginCapability.EXPORTER],
        )

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run the PyProcore CLI locally without requiring credentials."""
        env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        return subprocess.run(
            [sys.executable, "-m", "pyprocore.app", *args],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_main(self, *args: str) -> tuple[int, str]:
        """Run CLI main in-process and capture its safe output."""
        stdout = io.StringIO()
        with patch.object(sys, "argv", ["procore-sdk", *args]):
            with contextlib.redirect_stdout(stdout):
                try:
                    main()
                except SystemExit as exc:
                    code = exc.code if isinstance(exc.code, int) else 1
                    return code, stdout.getvalue()
        return 0, stdout.getvalue()

    def test_manifest_construction_and_validation(self) -> None:
        """A valid manifest should pass Phase 11A validation."""
        manifest = self.manifest()
        result = validate_plugin_manifest(manifest)

        self.assertTrue(result.valid)
        self.assertEqual(manifest.schema_version, PLUGIN_SCHEMA_VERSION)
        self.assertEqual(manifest.capabilities, [PluginCapability.EXPORTER])

    def test_invalid_name_version_schema_and_unsafe_entry_point_are_rejected(self) -> None:
        """Unsafe names, versions, schemas, and mutation-like metadata should fail."""
        cases = [
            {
                "schema_version": "1",
                "name": "../unsafe",
                "version": "1.0.0",
                "description": "Unsafe path name.",
                "capabilities": ["exporter"],
            },
            {
                "schema_version": "1",
                "name": "bad_version_plugin",
                "version": "latest",
                "description": "Bad version.",
                "capabilities": ["exporter"],
            },
            {
                "schema_version": "99",
                "name": "bad_schema_plugin",
                "version": "1.0.0",
                "description": "Bad schema.",
                "capabilities": ["exporter"],
            },
            {
                "schema_version": "1",
                "name": "unsafe_entry_plugin",
                "version": "1.0.0",
                "description": "Unsafe entry point.",
                "capabilities": ["exporter"],
                "entry_points": {"delete": "example.delete_records"},
            },
        ]

        for data in cases:
            result = validate_plugin_manifest_data(data)
            self.assertFalse(result.valid, data)
            self.assertTrue(result.errors)

    def test_invalid_capability_is_rejected_by_model_validation(self) -> None:
        """Unsupported capability strings should not become plugin manifests."""
        result = validate_plugin_manifest_data(
            {
                "name": "unsupported_capability_plugin",
                "version": "1.0.0",
                "description": "Invalid capability.",
                "capabilities": ["write_action"],
            }
        )

        self.assertFalse(result.valid)
        self.assertIn("Manifest structure is invalid", result.errors[0])

    def test_registry_list_show_duplicate_export_and_capability_filter(self) -> None:
        """Registry should validate manifests, reject duplicates, and export JSON."""
        registry = PluginRegistry()
        manifest = self.manifest(name="registry_plugin")

        registry.register_plugin_manifest(manifest)
        with self.assertRaises(DuplicateMatchError):
            registry.register_plugin_manifest(manifest)

        self.assertEqual(registry.get_plugin("registry_plugin").name, "registry_plugin")
        self.assertEqual(
            [item.name for item in registry.find_plugins_by_capability("exporter")],
            ["registry_plugin"],
        )
        exported = registry.export_plugin_registry_manifest()
        self.assertEqual(exported.plugin_count, 1)
        self.assertEqual(exported.plugins[0].name, "registry_plugin")
        self.assertIn("registry_plugin", exported.model_dump_json())

    def test_registry_rejects_invalid_manifest(self) -> None:
        """Registry registration should raise SDK validation errors."""
        registry = PluginRegistry()
        manifest = PluginManifest(
            schema_version="99",
            name="bad_schema_plugin",
            version="1.0.0",
            description="Invalid schema.",
            capabilities=[PluginCapability.EXPORTER],
        )

        with self.assertRaises(ValidationError):
            registry.register_plugin_manifest(manifest)

    def test_registry_helpers_and_error_paths(self) -> None:
        """Module-level registry helpers should preserve registry behavior."""
        first = self.manifest(name="helper_plugin")
        replacement = PluginManifest(
            name="helper_plugin",
            version="1.0.1",
            description="Replacement metadata.",
            capabilities=[PluginCapability.REPORT],
        )
        registry = PluginRegistry([first])

        self.assertEqual(list_plugins(registry)[0].name, "helper_plugin")
        self.assertEqual(get_plugin(registry, "helper_plugin").version, "1.0.0")
        self.assertEqual(
            [plugin.name for plugin in find_plugins_by_capability(registry, "exporter")],
            ["helper_plugin"],
        )
        self.assertEqual(export_plugin_registry_manifest(registry).plugin_count, 1)

        registration = register_plugin_manifest(
            registry,
            replacement,
            source="test",
            replace=True,
        )
        self.assertEqual(registration.source, "test")
        self.assertEqual(get_plugin(registry, "helper_plugin").version, "1.0.1")
        self.assertEqual(unregister_plugin(registry, "helper_plugin").name, "helper_plugin")

        with self.assertRaises(NotFoundError):
            get_plugin(registry, "missing_plugin")
        with self.assertRaises(NotFoundError):
            unregister_plugin(registry, "missing_plugin")

        registration_from_data = registry.register_plugin_manifest_data(
            {
                "name": "data_plugin",
                "version": "1.0.0",
                "description": "Loaded from local dictionary data.",
                "capabilities": ["validator"],
            }
        )
        self.assertEqual(registration_from_data.manifest.name, "data_plugin")

    def test_builtin_and_local_discovery(self) -> None:
        """Discovery should return built-in metadata and parse local dictionaries."""
        builtins = discover_builtin_plugins()
        self.assertTrue(builtins.discovered)
        self.assertFalse(builtins.errors)
        self.assertIn("csv_exporter_plugin", [item.name for item in builtins.discovered])

        local = discover_local_plugin_manifests(
            [
                {
                    "name": "local_report_plugin",
                    "version": "1.0.0",
                    "description": "Local report metadata.",
                    "capabilities": ["report"],
                }
            ]
        )
        self.assertEqual([item.name for item in local.discovered], ["local_report_plugin"])

        installed = discover_installed_plugin_metadata()
        self.assertFalse(installed.discovered)
        self.assertTrue(installed.warnings)

        discovered = discover_plugins()
        self.assertEqual(discovered.source, "built-in")
        self.assertTrue(discovered.discovered)

    def test_local_discovery_file_loading_and_validation_warnings(self) -> None:
        """Local discovery should report parse errors, validation errors, and warnings."""
        warning_data = {
            "name": "warning_plugin",
            "version": "1.0.0",
            "description": "Warning metadata.",
            "capabilities": ["exporter"],
            "enabled_by_default": True,
            "supports_agent_metadata": True,
        }
        result = validate_plugin_manifest_data(warning_data)
        self.assertTrue(result.valid)
        self.assertGreaterEqual(len(result.warnings), 2)

        invalid_result = validate_plugin_manifest(
            PluginManifest(
                name="empty_metadata_plugin",
                version="1.0.0",
                description="",
                capabilities=[],
                entry_points={
                    "formatter/path": "example.formatter",
                    "secret": "example.access_token_reader",
                },
            )
        )
        self.assertFalse(invalid_result.valid)
        self.assertTrue(
            any("description" in error for error in invalid_result.errors),
            invalid_result.errors,
        )
        self.assertTrue(
            any("capability" in error for error in invalid_result.errors),
            invalid_result.errors,
        )
        self.assertTrue(
            any("filesystem path" in error for error in invalid_result.errors),
            invalid_result.errors,
        )
        self.assertTrue(
            any("secret-like" in error for error in invalid_result.errors),
            invalid_result.errors,
        )

        discovery = discover_local_plugin_manifests(
            [
                {"name": "missing_fields_plugin"},
                {
                    "schema_version": "99",
                    "name": "bad_local_plugin",
                    "version": "1.0.0",
                    "description": "Bad local metadata.",
                    "capabilities": ["report"],
                },
                warning_data,
            ]
        )
        self.assertEqual([item.name for item in discovery.discovered], ["warning_plugin"])
        self.assertTrue(discovery.errors)
        self.assertTrue(discovery.warnings)

        with self.subTest("manifest file loading"):
            with tempfile.TemporaryDirectory() as directory:
                valid_path = Path(directory) / "plugin.json"
                valid_path.write_text(json.dumps(warning_data), encoding="utf-8")
                loaded = load_local_plugin_manifest_file(valid_path)
                self.assertEqual(loaded.name, "warning_plugin")

                invalid_path = Path(directory) / "not-an-object.json"
                invalid_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_local_plugin_manifest_file(invalid_path)

    def test_app_plugin_helpers_and_run_command_paths(self) -> None:
        """CLI helper functions should be covered without invoking child processes."""
        registry = build_default_plugin_registry()
        plugins = registry.list_plugins()
        sample = sample_plugin_manifest()

        self.assertIn("No plugin manifests", format_plugins([]))
        self.assertIn("Registered plugin manifests", format_plugins(plugins))
        self.assertIn("metadata only", format_plugin(sample))
        self.assertIn("example_exporter_plugin", format_plugin(sample))
        homepage_plugin = PluginManifest(
            name="homepage_plugin",
            version="1.0.0",
            description="Metadata with optional presentation fields.",
            capabilities=[PluginCapability.REPORT],
            homepage="https://example.invalid/plugin",
            notes=["Local metadata only."],
        )
        formatted_homepage = format_plugin(homepage_plugin)
        self.assertIn("Homepage:", formatted_homepage)
        self.assertIn("Notes:", formatted_homepage)
        self.assertIn(
            "Plugins:", format_plugin_registry_manifest(registry.export_plugin_registry_manifest())
        )

        valid_validation = validate_plugin_manifest(sample)
        self.assertIn("Valid: True", format_plugin_validation(valid_validation))

        invalid_validation = validate_plugin_manifest(
            PluginManifest(
                name="invalid_for_formatting",
                version="1.0.0",
                description="",
                capabilities=[],
            )
        )
        formatted_invalid = format_plugin_validation(invalid_validation)
        self.assertIn("Valid: False", formatted_invalid)
        self.assertIn("Errors:", formatted_invalid)

        parser = build_parser()
        list_result = run_command(parser.parse_args(["plugins", "list"]))
        self.assertGreaterEqual(len(list_result), 1)

        show_result = run_command(parser.parse_args(["plugins", "show", "csv_exporter_plugin"]))
        self.assertEqual(show_result.name, "csv_exporter_plugin")

        manifest_result = run_command(parser.parse_args(["plugins", "manifest"]))
        self.assertGreaterEqual(manifest_result.plugin_count, 1)

        sample_result = run_command(parser.parse_args(["plugins", "sample-manifest"]))
        self.assertEqual(sample_result.name, "example_exporter_plugin")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plugin.json"
            path.write_text(sample.model_dump_json(), encoding="utf-8")
            validate_result = run_command(parser.parse_args(["plugins", "validate", str(path)]))
        self.assertTrue(validate_result.valid)

    def test_plugin_main_rendering_paths(self) -> None:
        """Plugin CLI rendering should work in-process for coverage and behavior."""
        cases = [
            (("plugins", "list"), 0, "Registered plugin manifests"),
            (("plugins", "list", "--json"), 0, "csv_exporter_plugin"),
            (("plugins", "show", "csv_exporter_plugin"), 0, "csv_exporter_plugin"),
            (("plugins", "show", "csv_exporter_plugin", "--json"), 0, "safety_level"),
            (("plugins", "manifest"), 0, "PyProcore plugin registry manifest."),
            (("plugins", "manifest", "--json"), 0, '"plugin_count"'),
            (("plugins", "sample-manifest"), 0, "example_exporter_plugin"),
            (("plugins", "sample-manifest", "--json"), 0, '"example_exporter_plugin"'),
        ]
        for args, expected_code, expected_text in cases:
            with self.subTest(args=args):
                code, output = self.run_main(*args)
                self.assertEqual(code, expected_code, output)
                self.assertIn(expected_text, output)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plugin.json"
            path.write_text(sample_plugin_manifest().model_dump_json(), encoding="utf-8")
            code, output = self.run_main("plugins", "validate", str(path))
            self.assertEqual(code, 0, output)
            self.assertIn("Valid: True", output)

            invalid_path = Path(directory) / "invalid-plugin.json"
            invalid_path.write_text(
                json.dumps(
                    {
                        "name": "invalid_plugin",
                        "version": "1.0.0",
                        "description": "",
                        "capabilities": [],
                    }
                ),
                encoding="utf-8",
            )
            code, output = self.run_main("plugins", "validate", str(invalid_path), "--json")
            self.assertEqual(code, 1, output)
            self.assertIn('"valid": false', output)

    def test_cli_plugins_list_show_manifest_and_sample(self) -> None:
        """Plugin CLI commands should expose safe metadata without credentials."""
        list_result = self.run_cli("plugins", "list")
        self.assertEqual(list_result.returncode, 0, list_result.stderr)
        self.assertIn("Registered plugin manifests", list_result.stdout)
        self.assertNotIn("Traceback", list_result.stdout)

        show_result = self.run_cli("plugins", "show", "csv_exporter_plugin")
        self.assertEqual(show_result.returncode, 0, show_result.stderr)
        self.assertIn("csv_exporter_plugin", show_result.stdout)
        self.assertIn("metadata only", show_result.stdout)

        manifest_result = self.run_cli("plugins", "manifest", "--json")
        self.assertEqual(manifest_result.returncode, 0, manifest_result.stderr)
        manifest_json = json.loads(manifest_result.stdout)
        self.assertGreaterEqual(manifest_json["plugin_count"], 1)

        sample_result = self.run_cli("plugins", "sample-manifest", "--json")
        self.assertEqual(sample_result.returncode, 0, sample_result.stderr)
        sample_json = json.loads(sample_result.stdout)
        self.assertEqual(sample_json["name"], "example_exporter_plugin")

    def test_cli_plugins_validate(self) -> None:
        """Plugin validate should read local JSON only and return friendly output."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plugin.json"
            path.write_text(
                json.dumps(
                    {
                        "name": "validated_plugin",
                        "version": "1.0.0",
                        "description": "Validated metadata.",
                        "capabilities": ["validator"],
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_cli("plugins", "validate", str(path))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Valid: True", result.stdout)
        self.assertNotIn("Traceback", result.stdout)

    def test_docs_examples_and_package_exports(self) -> None:
        """Docs and examples should mention Phase 11A plugin support."""
        self.assertTrue(hasattr(pyprocore, "PluginManifest"))
        self.assertTrue(hasattr(pyprocore, "PluginRegistry"))
        self.assertTrue((PROJECT_ROOT / "docs" / "plugins.md").exists())

        examples = (PROJECT_ROOT / "examples" / "README.md").read_text(encoding="utf-8")
        plugin_docs = (PROJECT_ROOT / "docs" / "plugins.md").read_text(encoding="utf-8")
        mkdocs = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")

        self.assertIn("Examples `177` through `184`", examples)
        self.assertIn("Phase 11A", plugin_docs)
        self.assertIn("plugins.md", mkdocs)

        for index in range(177, 185):
            matching = sorted((PROJECT_ROOT / "examples").glob(f"{index}_*.py"))
            self.assertEqual(len(matching), 1, index)
            self.assertIn('if __name__ == "__main__":', matching[0].read_text(encoding="utf-8"))

    def test_safety_boundaries_remain_enforced(self) -> None:
        """Phase 11A should not add plugin execution, installation, or workflow changes."""
        plugin_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((PROJECT_ROOT / "pyprocore" / "plugins").glob("*.py"))
        )
        app_text = (PROJECT_ROOT / "pyprocore" / "app.py").read_text(encoding="utf-8")

        self.assertNotIn("requests.", plugin_text)
        self.assertNotIn("httpx", plugin_text)
        self.assertNotIn("urllib.request", plugin_text)
        self.assertNotIn("importlib.import_module", plugin_text)
        self.assertNotIn("pip install", plugin_text)
        self.assertNotIn("plugins install", app_text)
        self.assertNotIn("plugins run", app_text)

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
