"""Tests for Phase 11B safe local plugin extension hooks."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any

import pyprocore
from pyprocore.app import (
    build_default_hook_registry,
    format_plugin_hook_manifest,
    format_plugin_hook_result,
    format_plugin_hooks,
    sample_hook_manifest,
    sample_hook_records,
)
from pyprocore.core.exceptions import DuplicateMatchError, NotFoundError, ValidationError
from pyprocore.plugins import (
    PluginCapability,
    PluginHookContext,
    PluginHookMetadata,
    PluginHookRegistry,
    PluginHookRegistryManifest,
    PluginHookResult,
    PluginHookType,
    PluginManifest,
    builtin_hook_metadata,
    builtin_hook_registry,
    export_hook_registry_manifest,
    find_hooks_by_type,
    get_hook,
    list_hooks,
    redact_sensitive_text,
    run_exporter_hook,
    run_formatter_hook,
    run_record_transformer_hook,
    run_validator_hook,
    sanitize_hook_value,
    unregister_hook,
    validate_hook_registration,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase11BPluginHookTests(unittest.TestCase):
    """Validate safe local plugin hook support."""

    def metadata(
        self,
        *,
        hook_name: str = "local_quality_check",
        hook_type: PluginHookType = PluginHookType.VALIDATOR,
    ) -> PluginHookMetadata:
        """Build valid hook metadata for tests."""
        return PluginHookMetadata(
            hook_name=hook_name,
            plugin_name="test_plugin",
            hook_type=hook_type,
            description="Local test hook.",
        )

    def hook(self, context: PluginHookContext, payload: Any) -> dict[str, Any]:
        """Return a JSON-safe local hook result."""
        return {
            "hook": context.hook_name,
            "type": context.hook_type.value,
            "count": len(payload) if isinstance(payload, list) else 1,
        }

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

    def test_hook_metadata_context_and_result_are_serializable(self) -> None:
        """Hook models should serialize while redacting context secrets."""
        metadata = self.metadata()
        context = PluginHookContext(
            plugin_name="test_plugin",
            hook_name="local_quality_check",
            hook_type=PluginHookType.VALIDATOR,
            options={
                "access_token": "token-value",
                "nested": {"client_secret": "secret-value"},
            },
        )
        result = PluginHookResult(
            hook_name=metadata.hook_name,
            plugin_name=metadata.plugin_name,
            hook_type=metadata.hook_type,
            success=True,
            output={"ok": True},
        )

        self.assertEqual(context.options["access_token"], "[REDACTED]")
        self.assertEqual(context.options["nested"]["client_secret"], "[REDACTED]")
        self.assertIn("local_quality_check", metadata.model_dump_json())
        self.assertIn('"success":true', result.model_dump_json())

    def test_registry_registration_listing_lookup_and_export(self) -> None:
        """Hook registry should support explicit local registration and lookup."""
        registry = PluginHookRegistry()
        metadata = self.metadata()

        registration = registry.register_hook(metadata, self.hook, source="test")
        copied_registry = PluginHookRegistry([registration])

        self.assertEqual(registration.source, "test")
        self.assertEqual(registry.get_hook("local_quality_check").hook_name, metadata.hook_name)
        self.assertEqual(
            copied_registry.get_hook("local_quality_check").hook_name,
            metadata.hook_name,
        )
        self.assertEqual(list_hooks(registry)[0].hook_name, metadata.hook_name)
        self.assertEqual(get_hook(registry, metadata.hook_name).plugin_name, "test_plugin")
        self.assertEqual(
            find_hooks_by_type(registry, PluginHookType.VALIDATOR)[0].hook_name,
            metadata.hook_name,
        )
        manifest = export_hook_registry_manifest(registry)
        self.assertIsInstance(manifest, PluginHookRegistryManifest)
        self.assertEqual(manifest.hook_count, 1)
        self.assertIn("explicit_local_hooks", manifest.model_dump_json())

    def test_registry_rejects_duplicate_invalid_and_non_callable_hooks(self) -> None:
        """Unsafe or malformed hook registrations should be rejected."""
        registry = PluginHookRegistry()
        metadata = self.metadata()
        registry.register_hook(metadata, self.hook)

        with self.assertRaises(DuplicateMatchError):
            registry.register_hook(metadata, self.hook)
        replaced = registry.register_hook(metadata, self.hook, replace=True)
        self.assertEqual(replaced.metadata.hook_name, metadata.hook_name)
        with self.assertRaises(ValidationError):
            registry.register_hook(self.metadata(hook_name="../bad"), self.hook)
        with self.assertRaises(ValidationError):
            registry.register_hook(self.metadata(hook_name="delete_records"), self.hook)
        with self.assertRaises(ValidationError):
            registry.register_hook(
                PluginHookMetadata(
                    hook_name="unsafe_hook",
                    plugin_name="test_plugin",
                    hook_type=PluginHookType.VALIDATOR,
                    description="Unsafe.",
                    read_only=False,
                ),
                self.hook,
            )
        with self.assertRaises(ValidationError):
            validate_hook_registration(self.metadata(hook_name="not_callable"), "not callable")
        with self.assertRaises(ValidationError):
            validate_hook_registration(
                PluginHookMetadata(
                    hook_name="missing_description",
                    plugin_name="test_plugin",
                    hook_type=PluginHookType.VALIDATOR,
                    description=" ",
                ),
                self.hook,
            )
        with self.assertRaises(ValidationError):
            validate_hook_registration(
                PluginHookMetadata(
                    hook_name="unsafe_default",
                    plugin_name="test_plugin",
                    hook_type=PluginHookType.VALIDATOR,
                    description="Unsafe.",
                    safe_by_default=False,
                ),
                self.hook,
            )

    def test_registry_run_and_error_redaction(self) -> None:
        """Hook runs should return sanitized outputs and redacted errors."""
        registry = PluginHookRegistry()
        registry.register_hook(self.metadata(), self.hook)

        result = registry.run_validator_hook(
            "local_quality_check",
            [{"id": 1, "access_token": "secret-token"}],
        )

        self.assertTrue(result.success)
        self.assertEqual(result.output["count"], 1)

        def bad_hook(_context: PluginHookContext, _payload: Any) -> None:
            raise RuntimeError("client_secret=super-secret access_token=also-secret")

        registry.register_hook(
            self.metadata(hook_name="bad_hook", hook_type=PluginHookType.REPORT),
            bad_hook,
        )
        failed = registry.run_hook("bad_hook", {})

        self.assertFalse(failed.success)
        self.assertIn("[REDACTED]", failed.errors[0])
        self.assertNotIn("super-secret", failed.errors[0])
        self.assertNotIn("also-secret", failed.errors[0])

    def test_typed_run_helpers_and_not_found_errors(self) -> None:
        """Typed run helpers should enforce hook type and missing hooks."""
        registry = PluginHookRegistry()
        registry.register_hook(self.metadata(hook_type=PluginHookType.FORMATTER), self.hook)

        with self.assertRaises(ValidationError):
            registry.run_validator_hook("local_quality_check", [])
        with self.assertRaises(NotFoundError):
            registry.get_hook("missing_hook")
        self.assertEqual(
            unregister_hook(registry, "local_quality_check").hook_name, "local_quality_check"
        )

    def test_builtin_hooks_are_deterministic_and_local(self) -> None:
        """Built-in hooks should operate on local records only."""
        registry = builtin_hook_registry()
        records = [
            {"id": 1, "name": "RFI 1", "status": "open"},
            {"id": "", "name": "Submittal 2", "status": "closed"},
        ]

        required = run_validator_hook(
            registry,
            "validate_required_fields",
            records,
            options={"required_fields": ["id", "name"]},
        )
        no_empty_ids = registry.run_validator_hook("validate_no_empty_ids", records)
        formatted = run_formatter_hook(registry, "format_records_as_summary", records)
        transformed = run_record_transformer_hook(
            registry,
            "transform_records_select_fields",
            records,
            options={"fields": ["id", "name"]},
        )
        exported = run_exporter_hook(registry, "export_records_to_jsonl_payload", records)
        report = registry.run_hook("build_basic_quality_report", records)
        long_summary = run_formatter_hook(
            registry,
            "format_records_as_summary",
            [{"id": index, "title": f"Record {index}"} for index in range(1, 7)],
        )
        identity_transform = run_record_transformer_hook(
            registry,
            "transform_records_select_fields",
            {"records": [{"id": 3, "name": "Single"}]},
        )
        non_record_export = run_exporter_hook(
            registry,
            "export_records_to_jsonl_payload",
            "not records",
        )

        self.assertFalse(required.output["valid"])
        self.assertFalse(no_empty_ids.output["valid"])
        self.assertIn("Records: 2", formatted.output)
        self.assertIn("1 more", long_summary.output)
        self.assertEqual(transformed.output[0], {"id": 1, "name": "RFI 1"})
        self.assertEqual(identity_transform.output, [{"id": 3, "name": "Single"}])
        self.assertIn('"name": "RFI 1"', exported.output)
        self.assertEqual(non_record_export.output, "")
        self.assertEqual(report.output["record_count"], 2)
        self.assertGreaterEqual(len(builtin_hook_metadata()), 6)

    def test_manifest_hook_metadata_is_not_executable(self) -> None:
        """Manifest hook metadata should serialize without containing callables."""
        metadata = self.metadata(hook_name="manifest_only_hook")
        manifest = PluginManifest(
            name="manifest_hook_plugin",
            version="1.0.0",
            description="Manifest with hook metadata only.",
            capabilities=[PluginCapability.VALIDATOR],
            hooks=[metadata],
        )
        dumped = manifest.model_dump()

        self.assertEqual(dumped["hooks"][0]["hook_name"], "manifest_only_hook")
        self.assertNotIn("hook", dumped["hooks"][0])
        self.assertNotIn("callable", manifest.model_dump_json())

    def test_sanitizers_redact_secret_like_values(self) -> None:
        """Hook sanitizers should avoid leaking secrets."""
        sanitized = sanitize_hook_value(
            {
                "Authorization": "Bearer abc123",
                "message": "refresh_token=very-secret",
                "nested": [{"password": "pw"}],
            }
        )

        self.assertEqual(sanitized["Authorization"], "[REDACTED]")
        self.assertIn("[REDACTED]", sanitized["message"])
        self.assertEqual(sanitized["nested"][0]["password"], "[REDACTED]")
        self.assertIn("[REDACTED]", redact_sensitive_text("Bearer raw-token"))
        self.assertEqual(
            sanitize_hook_value(("safe", {"token": "hidden"}))[1]["token"], "[REDACTED]"
        )
        self.assertEqual(sanitize_hook_value({"b", "a"}), ["a", "b"])
        with self.assertRaises(ValueError):
            PluginHookContext(
                plugin_name="bad",
                hook_name="bad_context",
                hook_type=PluginHookType.VALIDATOR,
                options="not a mapping",
            )

    def test_app_hook_helpers_render_without_remote_execution(self) -> None:
        """App helper functions should render hook metadata and sample results locally."""
        registry = build_default_hook_registry()
        manifest = registry.export_hook_registry_manifest()
        hooks_text = format_plugin_hooks(registry.list_hooks())
        manifest_text = format_plugin_hook_manifest(manifest)
        validator_result = registry.run_validator_hook(
            "validate_required_fields",
            sample_hook_records(),
            options={"required_fields": ["id", "name"]},
        )
        result_text = format_plugin_hook_result(validator_result)
        plugin_manifest = sample_hook_manifest()

        self.assertIn("Registered plugin hooks", hooks_text)
        self.assertIn("explicit local hooks", hooks_text)
        self.assertIn("plugin hook registry manifest", manifest_text)
        self.assertIn("Plugin hook run complete", result_text)
        self.assertIn("Success: True", result_text)
        self.assertEqual(plugin_manifest.hooks[0].hook_name, "example_quality_validator")

    def test_cli_plugin_hook_commands(self) -> None:
        """Plugin hook CLI commands should be safe and credential-free."""
        cases = [
            (("plugins", "hooks"), "Registered plugin hooks"),
            (("plugins", "hooks", "--type", "validator"), "validate_required_fields"),
            (("plugins", "hook-manifest"), "plugin hook registry manifest"),
            (("plugins", "hook-manifest", "--json"), '"hook_count"'),
            (("plugins", "sample-hook-manifest"), "example_hook_plugin"),
            (("plugins", "sample-hook-manifest", "--json"), '"hooks"'),
            (("plugins", "run-sample-validator"), "Success: True"),
            (("plugins", "run-sample-validator", "--json"), '"success": true'),
            (("plugins", "run-sample-formatter"), "Records: 2"),
        ]
        for args, expected in cases:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(expected, result.stdout)
                self.assertNotIn("Traceback", result.stdout)

    def test_docs_examples_and_root_exports(self) -> None:
        """Docs, examples, and package root should expose Phase 11B safely."""
        self.assertTrue(hasattr(pyprocore, "PluginHookRegistry"))
        self.assertTrue(hasattr(pyprocore, "builtin_hook_registry"))

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
        self.assertIn("Phase 11B", docs)
        self.assertIn("Examples `185` through `192`", docs)
        self.assertIn("explicitly registered", docs)

        for index in range(185, 193):
            matching = sorted((PROJECT_ROOT / "examples").glob(f"{index}_*.py"))
            self.assertEqual(len(matching), 1, index)
            text = matching[0].read_text(encoding="utf-8")
            self.assertIn('if __name__ == "__main__":', text)

    def test_safety_boundaries_remain_enforced(self) -> None:
        """Phase 11B must not add unsafe plugin loading or execution paths."""
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
