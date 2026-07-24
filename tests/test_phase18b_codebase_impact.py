"""Tests for the Phase 18B local customer-codebase impact scanner."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from pyprocore.app import build_parser, run_command
from pyprocore.core.exceptions import ValidationError
from pyprocore.maintenance import (
    ApiImpactReport,
    CodebaseScanOptions,
    CodebaseScanReport,
    analyze_codebase_api_impact,
    api_impact_report_to_json,
    api_impact_report_to_markdown,
    codebase_scan_report_to_json,
    codebase_scan_report_to_markdown,
    scan_pyprocore_usage,
)
from pyprocore.maintenance.usage import detect_python_usages, detect_text_usages

ROOT = Path(__file__).resolve().parents[1]
MAINTENANCE_EXAMPLES = ROOT / "examples" / "maintenance"
FAKE_CODEBASE = MAINTENANCE_EXAMPLES / "customer_codebase"
OLD_OAS = MAINTENANCE_EXAMPLES / "old_fake_procore_oas.json"
NEW_OAS = MAINTENANCE_EXAMPLES / "new_fake_procore_oas.json"


def _digest_tree(root: Path) -> dict[str, str]:
    """Return stable content digests for regular files beneath a fixture."""
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


class CodebaseUsageScannerTests(unittest.TestCase):
    """Exercise bounded AST and lexical usage detection."""

    def test_scan_detects_imports_calls_cli_and_capabilities(self) -> None:
        """The fake codebase should produce a structured capability inventory."""
        report = scan_pyprocore_usage(FAKE_CODEBASE)

        self.assertIsInstance(report, CodebaseScanReport)
        self.assertTrue(report.imports)
        self.assertTrue(report.calls)
        self.assertEqual({usage.command for usage in report.cli_usages}, {"rfis", "analytics"})
        self.assertGreater(report.capability_counts["rfis"], 0)
        self.assertGreater(report.capability_counts["workflows"], 0)
        self.assertGreater(report.capability_counts["analytics"], 0)
        self.assertFalse(report.files_modified)
        self.assertFalse(report.remote_repo_access_enabled)
        self.assertFalse(report.execution_enabled)

    def test_scan_does_not_modify_customer_files(self) -> None:
        """Scanning must leave all customer fixture contents unchanged."""
        before = _digest_tree(FAKE_CODEBASE)

        scan_pyprocore_usage(FAKE_CODEBASE)

        self.assertEqual(_digest_tree(FAKE_CODEBASE), before)

    def test_secret_looking_snippets_are_redacted(self) -> None:
        """Stored snippets must not preserve fake credential values."""
        report = scan_pyprocore_usage(FAKE_CODEBASE)
        serialized = report.model_dump_json()

        self.assertIn("[REDACTED]", serialized)
        self.assertNotIn("fake-secret-for-redaction-tests", serialized)

    def test_dynamic_usage_is_unknown_and_low_confidence(self) -> None:
        """Unresolved getattr usage must not be overclassified."""
        report = scan_pyprocore_usage(FAKE_CODEBASE)
        dynamic = [usage for usage in report.usages if usage.dynamic]

        self.assertTrue(dynamic)
        self.assertTrue(all(usage.capability_family == "unknown" for usage in dynamic))
        self.assertTrue(all(usage.confidence == "low" for usage in dynamic))

    def test_python_aliases_and_static_clients_are_detected(self) -> None:
        """Aliased package and client names should retain static call context."""
        source = (
            "import pyprocore as pp\n"
            "from pyprocore.workflows import build_project_context_package as build\n"
            "sdk = pp.Procore()\n"
            "sdk.submittals.list(project_id=1)\n"
            "build(project_id=1)\n"
        )

        imports, calls, _ = detect_python_usages(source, "customer.py")

        self.assertEqual(len(imports), 2)
        self.assertIn("submittals", {call.capability_family for call in calls})
        self.assertIn("workflows", {call.capability_family for call in calls})

    def test_unrelated_getattr_is_not_reported(self) -> None:
        """Ordinary dynamic Python access must not become a false SDK finding."""
        _, _, other = detect_python_usages(
            "value = getattr(config, 'name')\n",
            "unrelated.py",
        )

        self.assertEqual(other, [])

    def test_text_detection_handles_cli_and_package_references(self) -> None:
        """Shell-style CLI commands and package references should be lexical only."""
        cli, references = detect_text_usages(
            "PYTHONPATH=. procore-sdk documents 123\nrequires = ['pyprocore']\n",
            "README.md",
        )

        self.assertEqual(cli[0].capability_family, "documents")
        self.assertTrue(references)

    def test_scan_skips_ignored_large_binary_and_hidden_files(self) -> None:
        """Default bounds should report unsafe or irrelevant files as skipped."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text("import pyprocore\n", encoding="utf-8")
            (root / ".hidden.py").write_text("import pyprocore\n", encoding="utf-8")
            ignored = root / ".venv"
            ignored.mkdir()
            (ignored / "ignored.py").write_text("import pyprocore\n", encoding="utf-8")
            (root / "large.py").write_text("x" * 30, encoding="utf-8")
            (root / "binary.py").write_bytes(b"pyprocore\x00binary")

            report = scan_pyprocore_usage(
                root,
                options=CodebaseScanOptions(max_file_size_bytes=20),
            )

        reasons = {item.reason for item in report.files_skipped}
        self.assertIn("hidden file", reasons)
        self.assertIn("ignored directory: .venv", reasons)
        self.assertIn("file exceeds max_file_size_bytes", reasons)
        self.assertIn("binary file detected", reasons)

    def test_remote_or_missing_paths_are_rejected(self) -> None:
        """The scanner must never clone or fetch a remote repository."""
        with self.assertRaises(ValidationError):
            scan_pyprocore_usage("https://example.invalid/customer.git")
        with self.assertRaises(ValidationError):
            scan_pyprocore_usage(ROOT / "missing-customer-codebase")


class CodebaseImpactTests(unittest.TestCase):
    """Exercise conservative optional OAS drift correlation."""

    def test_impact_without_oas_is_unknown_and_local_only(self) -> None:
        """No OAS input should produce a valid report without speculative certainty."""
        report = analyze_codebase_api_impact(FAKE_CODEBASE)

        self.assertIsInstance(report, ApiImpactReport)
        self.assertFalse(report.oas_comparison_provided)
        classifications = {
            finding.capability_family: finding.classification for finding in report.findings
        }
        self.assertEqual(classifications["rfis"], "unknown")
        self.assertEqual(classifications["analytics"], "not_affected")

    def test_impact_with_fake_oas_marks_direct_rfi_usage(self) -> None:
        """RFI parameter drift should map to direct fake RFI usage."""
        report = analyze_codebase_api_impact(FAKE_CODEBASE, OLD_OAS, NEW_OAS)
        classifications = {
            finding.capability_family: finding.classification for finding in report.findings
        }

        self.assertTrue(report.oas_comparison_provided)
        self.assertEqual(classifications["rfis"], "likely_affected")
        self.assertEqual(classifications["workflows"], "possibly_affected")
        self.assertEqual(classifications["analytics"], "not_affected")
        self.assertEqual(classifications["unknown"], "unknown")
        self.assertFalse(report.files_modified)

    def test_impact_requires_both_oas_paths(self) -> None:
        """One-sided drift input should fail before making any remote request."""
        with self.assertRaisesRegex(ValueError, "provided together"):
            analyze_codebase_api_impact(FAKE_CODEBASE, old_oas_path=OLD_OAS)

    def test_json_and_markdown_reports_are_structured_and_safe(self) -> None:
        """Both formats should serialize locally with explicit safety language."""
        scan = scan_pyprocore_usage(FAKE_CODEBASE)
        impact = analyze_codebase_api_impact(FAKE_CODEBASE, OLD_OAS, NEW_OAS)

        self.assertEqual(
            json.loads(codebase_scan_report_to_json(scan))["mode"],
            "local_customer_codebase_scan",
        )
        self.assertEqual(
            json.loads(api_impact_report_to_json(impact))["mode"],
            "local_customer_codebase_impact_scan",
        )
        self.assertIn("No files were modified", codebase_scan_report_to_markdown(scan))
        self.assertIn("Human review is required", api_impact_report_to_markdown(impact))


class CodebaseImpactCliTests(unittest.TestCase):
    """Verify local maintenance commands parse and dispatch without credentials."""

    def test_usage_scan_and_usage_map_commands(self) -> None:
        """Both usage commands should return the typed local report."""
        parser = build_parser()
        for command in ("usage-scan", "usage-map"):
            args = parser.parse_args(["maintenance", command, str(FAKE_CODEBASE)])
            self.assertIsInstance(run_command(args), CodebaseScanReport)

    def test_impact_scan_commands_with_and_without_oas(self) -> None:
        """Impact CLI dispatch should keep OAS comparison optional and paired."""
        parser = build_parser()
        without_oas = parser.parse_args(["maintenance", "impact-scan", str(FAKE_CODEBASE)])
        with_oas = parser.parse_args(
            [
                "maintenance",
                "impact-scan",
                str(FAKE_CODEBASE),
                "--old-oas",
                str(OLD_OAS),
                "--new-oas",
                str(NEW_OAS),
            ]
        )

        self.assertFalse(run_command(without_oas).oas_comparison_provided)
        self.assertTrue(run_command(with_oas).oas_comparison_provided)

    def test_phase18b_sources_do_not_enable_network_or_execution(self) -> None:
        """Scanner modules must not contain remote, subprocess, or mutation hooks."""
        sources = "\n".join(
            (ROOT / "pyprocore" / "maintenance" / name).read_text(encoding="utf-8")
            for name in ["codebase.py", "usage.py", "impact.py", "impact_reports.py"]
        ).lower()

        for forbidden in [
            "requests.",
            "subprocess.",
            "git clone",
            "github",
            "openai",
            "anthropic",
            "mcp execution",
        ]:
            self.assertNotIn(forbidden, sources)


if __name__ == "__main__":
    unittest.main()
