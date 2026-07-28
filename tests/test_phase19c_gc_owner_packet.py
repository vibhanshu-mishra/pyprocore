"""Tests for Phase 19C local GC/Owner installation packets."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pyprocore
from pyprocore.app import build_parser, run_command
from pyprocore.core.exceptions import ValidationError
from pyprocore.dmsa import (
    GcOwnerInstallationPacketOptions,
    build_gc_owner_email_templates,
    build_gc_owner_installation_packet,
    build_gc_owner_security_statement,
    build_gc_owner_troubleshooting_guide,
    build_rfi_submittal_permission_request,
    gc_owner_email_templates_to_markdown,
    gc_owner_install_checklist_to_markdown,
    gc_owner_installation_packet_to_markdown,
    gc_owner_packet_to_json,
    gc_owner_packet_write_result_to_markdown,
    gc_owner_permission_request_to_markdown,
    gc_owner_security_statement_to_markdown,
    gc_owner_troubleshooting_guide_to_markdown,
    write_gc_owner_installation_packet,
)

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FILES = {
    "gc_owner_installation_packet.md",
    "permission_request.md",
    "security_statement.md",
    "admin_install_checklist.md",
    "email_templates.md",
    "troubleshooting_guide.md",
    "packet_metadata.json",
}


class Phase19CGcOwnerPacketTests(unittest.TestCase):
    """Validate local-only GC/Owner packet generation."""

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run local CLI commands with credentials removed."""
        env = {
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                "PROCORE_CLIENT_ID",
                "PROCORE_CLIENT_SECRET",
                "OPENAI_API_KEY",
            }
        }
        env["PYTHONPATH"] = str(ROOT)
        return subprocess.run(
            [sys.executable, "-m", "pyprocore.app", *args],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_default_packet_has_executive_summary_and_root_exports(self) -> None:
        """Default packet should be complete and available from package root."""
        packet = build_gc_owner_installation_packet()
        self.assertIn("read-only", packet.executive_summary)
        self.assertEqual(len(packet.artifacts), 7)
        self.assertTrue(hasattr(pyprocore, "GcOwnerInstallationPacket"))
        self.assertTrue(hasattr(pyprocore, "build_gc_owner_installation_packet"))

    def test_permission_request_is_minimum_read_only_access(self) -> None:
        """Permission request should include RFIs/Submittals and exclude writes."""
        request = build_rfi_submittal_permission_request()
        access = {(item.resource, item.access) for item in request.required_items}
        self.assertIn(("RFIs", "Read Only"), access)
        self.assertIn(("Submittals", "Read Only"), access)
        self.assertTrue(all(not item.write_access_requested for item in request.required_items))
        excluded = " ".join(request.excluded_actions).casefold()
        for action in (
            "no create",
            "no edit",
            "no approve",
            "no submit",
            "no close",
            "no delete",
            "no upload",
            "no payment",
        ):
            self.assertIn(action, excluded)

    def test_conditional_permissions_follow_options(self) -> None:
        """Optional access should appear only when explicitly selected."""
        minimal = build_rfi_submittal_permission_request(
            GcOwnerInstallationPacketOptions(
                include_attachments=False,
                use_webhooks=False,
                include_linked_references=False,
            )
        )
        expanded = build_rfi_submittal_permission_request(
            GcOwnerInstallationPacketOptions(
                include_attachments=True,
                use_webhooks=True,
                include_linked_references=True,
            )
        )
        self.assertEqual(minimal.conditional_items, [])
        self.assertEqual(len(expanded.conditional_items), 3)
        self.assertTrue(all(not item.write_access_requested for item in expanded.conditional_items))

    def test_security_statement_preserves_all_boundaries(self) -> None:
        """Security copy should state controls without claiming certification."""
        statement = build_gc_owner_security_statement()
        text = " ".join(
            [
                *statement.statements,
                *statement.data_handling,
                *statement.control_and_revocation,
                statement.disclaimer,
            ]
        ).casefold()
        self.assertIn("no procore write actions", text)
        self.assertIn("gc/owner controls", text)
        self.assertIn("does not install the app", text)
        self.assertIn("create the dmsa", text)
        self.assertIn("no external ai/model", text)
        self.assertIn("mcp and procore tool execution remain disabled", text)
        self.assertIn("not a security certification", text)

    def test_email_templates_cover_request_followup_and_offboarding(self) -> None:
        """Email set should cover the full human-owned onboarding lifecycle."""
        templates = build_gc_owner_email_templates()
        ids = {item.template_id for item in templates}
        self.assertEqual(
            ids,
            {
                "initial-request",
                "installed-follow-up",
                "permission-clarification",
                "no-access",
                "offboarding",
            },
        )
        rendered = gc_owner_email_templates_to_markdown(templates)
        self.assertIn("Initial request", rendered)
        self.assertIn("no permitted Procore projects visible", rendered)
        self.assertIn("[Integration Support Contact]", rendered)

    def test_troubleshooting_maps_requested_conditions_cautiously(self) -> None:
        """Guide should use likely causes and recommended reviews."""
        guide = build_gc_owner_troubleshooting_guide()
        codes = {item.code for item in guide.findings}
        self.assertTrue(
            {
                "401",
                "403",
                "404",
                "empty_projects",
                "empty_records",
                "missing_attachments",
                "webhook_not_firing",
                "polling_no_updates",
                "access_revoked",
                "projects_not_assigned",
            }.issubset(codes)
        )
        text = gc_owner_troubleshooting_guide_to_markdown(guide)
        self.assertIn("Likely cause", text)
        self.assertIn("Recommended review", text)
        self.assertIn("not live findings", guide.disclaimer)

    def test_all_json_and_markdown_reports_render(self) -> None:
        """Every packet component should have a useful local renderer."""
        packet = build_gc_owner_installation_packet()
        reports = (
            gc_owner_installation_packet_to_markdown(packet),
            gc_owner_permission_request_to_markdown(packet.permission_request),
            gc_owner_security_statement_to_markdown(packet.security_statement),
            gc_owner_install_checklist_to_markdown(packet.install_checklist),
            gc_owner_email_templates_to_markdown(packet.email_templates),
            gc_owner_troubleshooting_guide_to_markdown(packet.troubleshooting_guide),
            gc_owner_packet_to_json(packet),
        )
        self.assertTrue(all(report.strip() for report in reports))
        self.assertIn("Local template/documentation aid", reports[0])
        self.assertIn('"title": "GC/Owner Private App Installation Packet"', reports[-1])

    def test_artifact_dry_run_lists_files_without_writing(self) -> None:
        """Dry-run should list all artifacts and create no directory."""
        packet = build_gc_owner_installation_packet()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "not-created"
            result = write_gc_owner_installation_packet(packet, root, dry_run=True)
            self.assertEqual(set(result.planned_files), EXPECTED_FILES)
            self.assertFalse(root.exists())
            summary = gc_owner_packet_write_result_to_markdown(result)
            self.assertIn("Dry-run: yes", summary)
            self.assertIn("App installation performed: no", summary)

    def test_artifact_writer_is_contained_and_overwrite_protected(self) -> None:
        """Explicit writes should remain inside output_dir and require overwrite."""
        packet = build_gc_owner_installation_packet()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "packet"
            result = write_gc_owner_installation_packet(packet, root, dry_run=False)
            self.assertEqual(set(result.written_files), EXPECTED_FILES)
            self.assertTrue(all((root / name).is_file() for name in EXPECTED_FILES))
            with self.assertRaises(ValidationError):
                write_gc_owner_installation_packet(packet, root, dry_run=False)
            replaced = write_gc_owner_installation_packet(
                packet,
                root,
                dry_run=False,
                overwrite=True,
            )
            self.assertEqual(set(replaced.written_files), EXPECTED_FILES)

    def test_artifact_writer_blocks_path_traversal(self) -> None:
        """Packet writer should reject traversing output paths."""
        with self.assertRaises(ValidationError):
            write_gc_owner_installation_packet(
                build_gc_owner_installation_packet(),
                "../outside",
                dry_run=True,
            )

    def test_cli_commands_work_without_credentials(self) -> None:
        """Packet CLI commands should use local builders only."""
        commands = [
            ("dmsa", "gc-owner-packet", "--format", "json"),
            ("dmsa", "permission-request"),
            ("dmsa", "security-statement"),
            ("dmsa", "email-templates"),
            ("dmsa", "troubleshooting-guide"),
        ]
        for command in commands:
            with self.subTest(command=command):
                completed = self.run_cli(*command)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertNotIn("Traceback", completed.stdout + completed.stderr)

    def test_cli_dispatch_is_typed_and_local_in_process(self) -> None:
        """Parser dispatch should return packet models without credentials."""
        parser = build_parser()
        commands = [
            ("gc-owner-packet", pyprocore.GcOwnerInstallationPacket),
            ("permission-request", pyprocore.GcOwnerPermissionRequest),
            ("security-statement", pyprocore.GcOwnerSecurityStatement),
            ("email-templates", list),
            ("troubleshooting-guide", pyprocore.GcOwnerTroubleshootingGuide),
        ]
        for command, expected_type in commands:
            with self.subTest(command=command):
                args = parser.parse_args(["dmsa", command])
                with patch("requests.Session.request") as request:
                    result = run_command(args)
                self.assertIsInstance(result, expected_type)
                request.assert_not_called()
        with tempfile.TemporaryDirectory() as temp_dir:
            args = parser.parse_args(
                [
                    "dmsa",
                    "gc-owner-packet-write",
                    "--output-dir",
                    temp_dir,
                    "--dry-run",
                ]
            )
            result = run_command(args)
            self.assertIsInstance(result, pyprocore.GcOwnerPacketWriteResult)
            self.assertTrue(result.dry_run)

    def test_cli_packet_writer_supports_dry_run_and_local_write(self) -> None:
        """CLI writer should preview or explicitly write local artifacts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dry_root = Path(temp_dir) / "dry"
            dry = self.run_cli(
                "dmsa",
                "gc-owner-packet-write",
                "--output-dir",
                str(dry_root),
                "--dry-run",
            )
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertFalse(dry_root.exists())
            root = Path(temp_dir) / "written"
            written = self.run_cli(
                "dmsa",
                "gc-owner-packet-write",
                "--output-dir",
                str(root),
            )
            self.assertEqual(written.returncode, 0, written.stderr)
            self.assertTrue((root / "packet_metadata.json").is_file())

    def test_examples_347_through_352_run_without_credentials(self) -> None:
        """Phase 19C examples should be deterministic and local."""
        for number in range(347, 353):
            example = next(ROOT.glob(f"examples/{number}_*.py"))
            completed = subprocess.run(
                [sys.executable, str(example)],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT), "PATH": os.environ.get("PATH", "")},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_no_network_or_execution_occurs(self) -> None:
        """Builders and writers should not touch network-capable APIs."""
        with (
            patch("requests.Session.request") as request,
            patch("subprocess.run") as subprocess_run,
        ):
            packet = build_gc_owner_installation_packet()
            with tempfile.TemporaryDirectory() as temp_dir:
                write_gc_owner_installation_packet(
                    packet,
                    temp_dir,
                    dry_run=False,
                )
        request.assert_not_called()
        subprocess_run.assert_not_called()

    def test_dependency_version_and_safety_surface_are_unchanged(self) -> None:
        """Phase 19C should add no dependency or executable/write surface."""
        sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                ROOT / "pyprocore/dmsa/onboarding.py",
                ROOT / "pyprocore/dmsa/packet_reports.py",
            )
        ).casefold()
        for phrase in (
            "requests.get(",
            "requests.post(",
            "session.request(",
            "openai",
            "git commit",
            "tools/call",
            "create_rfi(",
            "approve_submittal(",
        ):
            self.assertNotIn(phrase, sources)
        self.assertEqual(pyprocore.__version__, "2.4.0")
        self.assertEqual((ROOT / "pyproject.toml").stat().st_size > 0, True)

    def test_packet_docs_preserve_gc_owner_product_boundary(self) -> None:
        """Packet documentation should retain strict access and write boundaries."""
        text = (ROOT / "docs/gc-owner-installation-packet.md").read_text(encoding="utf-8")
        text_lower = text.casefold()
        for phrase in (
            "does not create the dmsa",
            "does not grant access",
            "gc/owner controls",
            "read only",
            "rfis",
            "submittals",
            "no procore write actions",
            "template/documentation aid",
        ):
            self.assertIn(phrase, text_lower)


if __name__ == "__main__":
    unittest.main()
