"""Tests for Phase 16B metadata-only plugin trust policy support."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pyprocore
from pyprocore.app import build_parser, run_command
from pyprocore.core.exceptions import ValidationError
from pyprocore.plugins import (
    PluginCapability,
    PluginExtensionPack,
    PluginExtensionPackItem,
    PluginManifest,
    PluginTrustPolicy,
    PluginTrustReport,
    build_trust_report_for_path,
    export_trust_policy_template,
    load_trust_policy_from_dict,
    load_trust_policy_from_file,
    render_trust_report_markdown,
    trust_report_to_json,
    validate_config_trust,
    validate_extension_pack_trust,
    validate_manifest_trust,
)
from pyprocore.plugins.config import PluginConfig

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase16BPluginTrustTests(unittest.TestCase):
    """Validate local-only plugin trust metadata behavior."""

    def trusted_manifest(self) -> PluginManifest:
        """Return a trusted metadata-only manifest."""
        return PluginManifest(
            name="trusted_exporter_plugin",
            version="1.0.0",
            description="Trusted exporter metadata.",
            author="PyProcore",
            publisher="PyProcore",
            capabilities=[PluginCapability.EXPORTER],
            allowed_capability_categories=[PluginCapability.EXPORTER],
            safety_boundaries=[
                "Metadata validation only.",
                "No plugin code is installed, imported, or executed.",
            ],
            checksum_sha256="a" * 64,
        )

    def policy(self) -> PluginTrustPolicy:
        """Return a restrictive local trust policy."""
        return PluginTrustPolicy(
            allowed_publishers=["PyProcore"],
            allowed_plugin_names=["trusted_exporter_plugin", "starter_export_pack"],
            allowed_capabilities=[PluginCapability.EXPORTER, PluginCapability.FORMATTER],
            require_trusted_publisher=True,
        )

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run the local CLI with PYTHONPATH pinned to this checkout."""
        return subprocess.run(
            [sys.executable, "-m", "pyprocore.app", *args],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
            env={"PYTHONPATH": str(PROJECT_ROOT)},
        )

    def test_trust_policy_template_is_conservative(self) -> None:
        """Sample trust policy should deny remote install, execution, and imports."""
        policy = export_trust_policy_template()

        self.assertTrue(policy.deny_remote_install)
        self.assertTrue(policy.deny_execution)
        self.assertTrue(policy.deny_arbitrary_import)
        self.assertIn(PluginCapability.EXPORTER, policy.allowed_capabilities)
        self.assertTrue(hasattr(pyprocore, "PluginTrustPolicy"))

    def test_trusted_manifest_passes_with_metadata_warnings_only(self) -> None:
        """Trusted manifests should pass when policy allows publisher/name/capability."""
        report = validate_manifest_trust(self.trusted_manifest(), self.policy())

        self.assertTrue(report.trusted)
        self.assertTrue(report.valid)
        self.assertIsInstance(report, PluginTrustReport)
        self.assertTrue(
            any(f.code == "checksum_not_verified_against_artifact" for f in report.findings)
        )
        self.assertFalse(any(f.severity == "error" for f in report.findings))

    def test_untrusted_manifest_fails_policy(self) -> None:
        """Untrusted publishers and capabilities should produce blocking findings."""
        manifest = PluginManifest(
            name="delete_everything_plugin",
            version="1.0.0",
            description="Unsafe metadata.",
            publisher="Unknown Publisher",
            capabilities=[PluginCapability.INTEGRATION_ADAPTER],
            safety_boundaries=["Metadata only."],
        )

        report = validate_manifest_trust(manifest, self.policy())

        self.assertFalse(report.trusted)
        codes = {finding.code for finding in report.findings}
        self.assertIn("plugin_not_allowed", codes)
        self.assertIn("publisher_not_allowed", codes)
        self.assertIn("capability_not_allowed", codes)

    def test_risky_policy_flags_fail_closed(self) -> None:
        """Policy validation should fail if execution/import/install denials are disabled."""
        policy = self.policy().model_copy(
            update={
                "deny_remote_install": False,
                "deny_execution": False,
                "deny_arbitrary_import": False,
            }
        )

        report = validate_manifest_trust(self.trusted_manifest(), policy)

        self.assertFalse(report.trusted)
        codes = {finding.code for finding in report.findings}
        self.assertIn("remote_install_allowed", codes)
        self.assertIn("execution_allowed", codes)
        self.assertIn("arbitrary_import_allowed", codes)

    def test_signature_and_checksum_are_syntactic_metadata_only(self) -> None:
        """Signature/checksum metadata should not claim cryptographic verification."""
        manifest = self.trusted_manifest().model_copy(
            update={"signature": "abc123abc123abc1", "checksum_sha256": "not-a-sha"}
        )

        report = validate_manifest_trust(manifest, self.policy())

        self.assertFalse(report.trusted)
        codes = {finding.code for finding in report.findings}
        self.assertIn("invalid_checksum_metadata", codes)
        self.assertIn("signature_not_cryptographically_verified", codes)

    def test_config_trust_validates_allowed_names_and_capabilities(self) -> None:
        """Plugin config trust checks should apply the same local allow lists."""
        config = PluginConfig(
            enabled_plugins=["unknown_plugin"],
            enabled_capabilities=[PluginCapability.MCP_METADATA],
        )

        report = validate_config_trust(config, self.policy())

        self.assertFalse(report.trusted)
        codes = {finding.code for finding in report.findings}
        self.assertIn("config_plugin_not_allowed", codes)
        self.assertIn("config_capability_not_allowed", codes)

    def test_local_policy_file_and_report_path(self) -> None:
        """Trust policy and target reports should load only local JSON files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            policy_path = temp / "policy.json"
            manifest_path = temp / "manifest.json"
            policy_path.write_text(self.policy().model_dump_json(), encoding="utf-8")
            manifest_path.write_text(
                self.trusted_manifest().model_dump_json(),
                encoding="utf-8",
            )

            policy = load_trust_policy_from_file(policy_path)
            report = build_trust_report_for_path(manifest_path, policy)

        self.assertTrue(report.trusted)
        self.assertIn("metadata-only", render_trust_report_markdown(report))
        self.assertIn('"target_name": "trusted_exporter_plugin"', trust_report_to_json(report))

    def test_remote_policy_paths_are_rejected(self) -> None:
        """Trust policy loading should never fetch remote URLs."""
        with self.assertRaises(ValidationError):
            load_trust_policy_from_file("https://example.invalid/policy.json")

    def test_policy_and_local_json_validation_errors_are_friendly(self) -> None:
        """Invalid policy and target files should fail without execution side effects."""
        with self.assertRaises(ValidationError):
            load_trust_policy_from_dict({"allowed_capabilities": ["not-a-capability"]})

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            not_json = temp / "policy.txt"
            invalid_json = temp / "policy.json"
            array_json = temp / "array.json"
            not_json.write_text("{}", encoding="utf-8")
            invalid_json.write_text("{", encoding="utf-8")
            array_json.write_text("[]", encoding="utf-8")

            with self.assertRaisesRegex(ValidationError, ".json suffix"):
                load_trust_policy_from_file(not_json)
            with self.assertRaisesRegex(ValidationError, "JSON is invalid"):
                load_trust_policy_from_file(invalid_json)
            with self.assertRaisesRegex(ValidationError, "object at the top level"):
                load_trust_policy_from_file(array_json)
            with self.assertRaisesRegex(ValidationError, "path traversal"):
                build_trust_report_for_path("../manifest.json", self.policy())

    def test_manifest_strict_metadata_findings(self) -> None:
        """Strict policy and manifest metadata should surface compatibility findings."""
        policy = self.policy().model_copy(
            update={
                "allowed_safety_levels": [],
                "allow_unsigned": False,
                "require_checksum_or_signature": True,
            }
        )
        manifest = PluginManifest(
            name="trusted_exporter_plugin",
            version="1.0.0",
            description="Trusted exporter metadata.",
            publisher="PyProcore",
            capabilities=[PluginCapability.EXPORTER, PluginCapability.FORMATTER],
            allowed_capability_categories=[PluginCapability.EXPORTER],
            safety_level="local_read_only",
            min_pyprocore_version="not-semver",
            max_pyprocore_version="also-bad",
            requires_pyprocore="2.3.0",
            entry_points={"main": "example.module:main"},
            enabled_by_default=True,
        )

        report = validate_manifest_trust(manifest, policy)
        codes = {finding.code for finding in report.findings}

        self.assertFalse(report.trusted)
        self.assertIn("safety_level_not_allowed", codes)
        self.assertIn("invalid_version_metadata", codes)
        self.assertIn("requires_pyprocore_unparsed", codes)
        self.assertIn("entry_points_metadata_only", codes)
        self.assertIn("enabled_by_default_ignored", codes)
        self.assertIn("capability_boundary_mismatch", codes)
        self.assertIn("signature_or_checksum_required", codes)
        self.assertIn("signature_required", codes)
        self.assertIn("missing_safety_boundaries", codes)

    def test_extension_pack_trust_and_path_detection(self) -> None:
        """Extension-pack manifests should be detected and policy-checked locally."""
        pack = PluginExtensionPack(
            name="starter_export_pack",
            version="1.0.0",
            description="Starter metadata bundle.",
            publisher="PyProcore",
            capabilities=[PluginCapability.EXPORTER],
            included_plugins=[
                PluginExtensionPackItem(plugin_name="trusted_exporter_plugin"),
                PluginExtensionPackItem(plugin_name="unknown_plugin"),
            ],
            requires_pyprocore="2.3.0",
        )

        report = validate_extension_pack_trust(pack, self.policy())

        self.assertFalse(report.trusted)
        self.assertIn(
            "included_plugin_not_allowed",
            {finding.code for finding in report.findings},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            pack_path = temp / "pack.json"
            pack_path.write_text(pack.model_dump_json(), encoding="utf-8")

            path_report = build_trust_report_for_path(pack_path, self.policy())

        self.assertEqual(path_report.target_type, "extension_pack")

    def test_config_path_detection_can_pass_policy(self) -> None:
        """Config JSON targets should be detected and trusted when policy allows them."""
        config = PluginConfig(
            enabled_plugins=["trusted_exporter_plugin"],
            enabled_capabilities=[PluginCapability.EXPORTER],
            extension_packs=["starter_export_pack"],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            config_path = temp / "plugins.json"
            config_path.write_text(config.model_dump_json(), encoding="utf-8")

            report = build_trust_report_for_path(config_path, self.policy())

        self.assertEqual(report.target_type, "config")
        self.assertTrue(report.trusted)

    def test_cli_trust_commands(self) -> None:
        """CLI trust commands should validate local metadata and render reports."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            policy_path = temp / "policy.json"
            manifest_path = temp / "manifest.json"
            policy_path.write_text(self.policy().model_dump_json(), encoding="utf-8")
            manifest_path.write_text(
                self.trusted_manifest().model_dump_json(),
                encoding="utf-8",
            )

            sample = self.run_cli("plugins", "trust", "sample-policy")
            validate = self.run_cli(
                "plugins",
                "trust",
                "validate-manifest",
                str(manifest_path),
                "--policy",
                str(policy_path),
            )
            report = self.run_cli(
                "plugins",
                "trust",
                "report",
                str(manifest_path),
                "--policy",
                str(policy_path),
                "--format",
                "json",
            )

        self.assertEqual(sample.returncode, 0, sample.stderr)
        self.assertIn("Deny execution: True", sample.stdout)
        self.assertEqual(validate.returncode, 0, validate.stderr)
        self.assertIn("Trusted: True", validate.stdout)
        self.assertEqual(report.returncode, 0, report.stderr)
        self.assertIn('"trusted": true', report.stdout)
        self.assertNotIn("Traceback", validate.stdout + validate.stderr)

    def test_run_command_trust_report(self) -> None:
        """run_command should return trust reports without executing plugin code."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            policy_path = temp / "policy.json"
            manifest_path = temp / "manifest.json"
            policy_path.write_text(self.policy().model_dump_json(), encoding="utf-8")
            manifest_path.write_text(
                self.trusted_manifest().model_dump_json(),
                encoding="utf-8",
            )

            parser = build_parser()
            result = run_command(
                parser.parse_args(
                    [
                        "plugins",
                        "trust",
                        "report",
                        str(manifest_path),
                        "--policy",
                        str(policy_path),
                    ]
                )
            )

        self.assertIsInstance(result, PluginTrustReport)
        self.assertTrue(result.trusted)

    def test_docs_examples_and_safety_boundaries(self) -> None:
        """Docs/examples should describe trust metadata without enabling execution."""
        docs = (PROJECT_ROOT / "docs" / "plugins.md").read_text(encoding="utf-8")
        examples = (PROJECT_ROOT / "examples" / "README.md").read_text(encoding="utf-8")
        app_text = (PROJECT_ROOT / "pyprocore" / "app.py").read_text(encoding="utf-8")
        plugin_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((PROJECT_ROOT / "pyprocore" / "plugins").glob("*.py"))
        )

        self.assertIn("Phase 16B", docs)
        self.assertIn("Examples `281` through `283`", examples)
        self.assertTrue(
            (PROJECT_ROOT / "examples" / "configs" / "plugin_trust_policy.json").exists()
        )
        self.assertNotIn("plugins install", app_text)
        self.assertNotIn("plugins run ", app_text)
        self.assertNotIn("importlib.import_module", plugin_source)
        self.assertNotIn("urllib.request", plugin_source)
        self.assertNotIn("requests.", plugin_source)
        self.assertNotIn("pip install", plugin_source)

        workflow_diff = subprocess.run(
            ["git", "diff", "--name-only", ".github/workflows"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(workflow_diff.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
