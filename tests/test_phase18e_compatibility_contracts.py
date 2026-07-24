"""Tests for Phase 18E local API compatibility contracts."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pyprocore.app import build_parser, run_command
from pyprocore.core.exceptions import ValidationError
from pyprocore.maintenance import (
    ApiCompatibilityContract,
    ApiCompatibilityContractOptions,
    ApiCompatibilityDiffReport,
    ApiCompatibilityValidationReport,
    CodebaseCompatibilityReport,
    analyze_codebase_compatibility_with_contract,
    build_current_compatibility_contract,
    codebase_compatibility_report_to_json,
    codebase_compatibility_report_to_markdown,
    compatibility_contract_to_json,
    compatibility_contract_to_markdown,
    compatibility_diff_report_to_json,
    compatibility_diff_report_to_markdown,
    compatibility_validation_report_to_json,
    compatibility_validation_report_to_markdown,
    diff_compatibility_contracts,
    load_compatibility_contract,
    validate_compatibility_contract,
    validate_compatibility_contract_file,
    write_compatibility_contract,
)

ROOT = Path(__file__).resolve().parents[1]
MAINTENANCE = ROOT / "examples" / "maintenance"
FAKE_CODEBASE = MAINTENANCE / "customer_codebase"
OLD_CONTRACT = MAINTENANCE / "contracts" / "old_pyprocore_compatibility_contract.json"
NEW_CONTRACT = MAINTENANCE / "contracts" / "new_pyprocore_compatibility_contract.json"


class CurrentCompatibilityContractTests(unittest.TestCase):
    """Verify current package contract truth and validation."""

    def test_current_contract_builds_deterministically(self) -> None:
        """Identical deterministic options should produce identical JSON."""
        options = ApiCompatibilityContractOptions(generated_at="2026-07-24T00:00:00Z")

        first = build_current_compatibility_contract(options)
        second = build_current_compatibility_contract(options)

        self.assertIsInstance(first, ApiCompatibilityContract)
        self.assertEqual(
            compatibility_contract_to_json(first),
            compatibility_contract_to_json(second),
        )

    def test_current_contract_includes_version_and_boundaries(self) -> None:
        """Current metadata should state version and non-negotiable safety."""
        contract = build_current_compatibility_contract()
        boundaries = {row.name: row.status for row in contract.safety_boundaries}

        self.assertEqual(contract.pyprocore_version, "2.3.0")
        self.assertEqual(boundaries["mcp"], "discovery_only")
        self.assertEqual(boundaries["procore_write_actions"], "disabled")
        self.assertEqual(boundaries["tool_execution"], "disabled")
        self.assertEqual(boundaries["external_ai_model_calls"], "none")
        self.assertFalse(contract.certification)

    def test_current_contract_validates(self) -> None:
        """The package-generated contract should pass its own safety validator."""
        report = validate_compatibility_contract(build_current_compatibility_contract())

        self.assertTrue(report.valid)
        self.assertFalse([row for row in report.findings if row.severity == "error"])

    def test_invalid_mapping_reports_required_fields(self) -> None:
        """Raw malformed metadata should return findings rather than crash."""
        report = validate_compatibility_contract({"resources": []})

        self.assertFalse(report.valid)
        self.assertIn(
            "missing_required_field",
            {finding.code for finding in report.findings},
        )

    def test_missing_safety_boundaries_is_invalid(self) -> None:
        """A structurally valid contract without boundaries must fail."""
        contract = build_current_compatibility_contract().model_copy(
            update={"safety_boundaries": []}
        )
        report = validate_compatibility_contract(contract)

        self.assertFalse(report.valid)
        self.assertIn(
            "missing_safety_boundaries",
            {finding.code for finding in report.findings},
        )

    def test_write_contract_is_single_file_and_requires_overwrite(self) -> None:
        """Explicit output should write only one JSON file and preserve it by default."""
        contract = build_current_compatibility_contract()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "contract.json"
            result = write_compatibility_contract(contract, output)

            self.assertEqual(result, output.resolve())
            self.assertEqual([path.name for path in Path(directory).iterdir()], ["contract.json"])
            with self.assertRaises(ValidationError):
                write_compatibility_contract(contract, output)
            write_compatibility_contract(contract, output, overwrite=True)

    def test_remote_and_non_json_paths_are_rejected(self) -> None:
        """Contract loading must remain local JSON only."""
        with self.assertRaises(ValidationError):
            load_compatibility_contract("https://example.com/contract.json")
        with tempfile.NamedTemporaryFile(suffix=".txt") as file:
            with self.assertRaises(ValidationError):
                load_compatibility_contract(file.name)


class CompatibilityFixtureAndDiffTests(unittest.TestCase):
    """Exercise local fixture loading and contract diffs."""

    def test_local_fixture_loads_and_validates(self) -> None:
        """The realistic new contract fixture should be accepted."""
        contract = load_compatibility_contract(NEW_CONTRACT)
        report = validate_compatibility_contract_file(NEW_CONTRACT)

        self.assertEqual(contract.pyprocore_version, "2.3.0")
        self.assertTrue(report.valid)

    def test_diff_detects_requested_changes(self) -> None:
        """Diff should expose family, CLI, deprecation, and known-gap changes."""
        report = diff_compatibility_contracts(OLD_CONTRACT, NEW_CONTRACT)

        self.assertIsInstance(report, ApiCompatibilityDiffReport)
        self.assertEqual(report.added_resource_families, ["photos"])
        self.assertEqual(report.added_cli_groups, ["catalog"])
        self.assertEqual(
            [item.helper for item in report.added_deprecations],
            ["build_project_context_package"],
        )
        self.assertEqual(
            [item.subject for item in report.changed_known_gaps],
            ["transmittals"],
        )
        self.assertFalse(report.changed_safety_boundaries)

    def test_contract_and_diff_reports_render(self) -> None:
        """JSON and Markdown should remain readable and deterministic."""
        contract = load_compatibility_contract(NEW_CONTRACT)
        diff = diff_compatibility_contracts(OLD_CONTRACT, NEW_CONTRACT)

        self.assertIn('"pyprocore_version": "2.3.0"', compatibility_contract_to_json(contract))
        self.assertIn(
            "not a production compatibility certification",
            compatibility_contract_to_markdown(contract),
        )
        self.assertIn('"added_resource_families"', compatibility_diff_report_to_json(diff))
        self.assertIn("Added Resource Families", compatibility_diff_report_to_markdown(diff))

    def test_validation_reports_render(self) -> None:
        """Validation reports should include status and local safety text."""
        report = validate_compatibility_contract_file(NEW_CONTRACT)

        self.assertIn('"valid": true', compatibility_validation_report_to_json(report, pretty=True))
        self.assertIn("Valid: yes", compatibility_validation_report_to_markdown(report))


class CodebaseCompatibilityTests(unittest.TestCase):
    """Compare fake customer usage with local contract metadata."""

    def test_scan_marks_supported_and_local_usage(self) -> None:
        """RFI use should be compatible and workflow metadata local-only."""
        report = analyze_codebase_compatibility_with_contract(
            FAKE_CODEBASE,
            OLD_CONTRACT,
        )

        self.assertIsInstance(report, CodebaseCompatibilityReport)
        self.assertTrue(report.compatible)
        self.assertTrue(report.local_only)
        self.assertFalse(report.customer_files_modified)

    def test_scan_marks_deprecated_helper(self) -> None:
        """The new fixture deprecation should match the fake workflow import."""
        report = analyze_codebase_compatibility_with_contract(
            FAKE_CODEBASE,
            NEW_CONTRACT,
        )

        self.assertIn(
            "build_project_context_package",
            {finding.symbol for finding in report.deprecated},
        )
        self.assertTrue(all(finding.migration_note for finding in report.deprecated))

    def test_scan_marks_unknown_dynamic_usage_for_review(self) -> None:
        """Unknown dynamic capability access should not be certified compatible."""
        report = analyze_codebase_compatibility_with_contract(
            FAKE_CODEBASE,
            NEW_CONTRACT,
        )

        self.assertTrue(report.unknown_manual_review)
        self.assertTrue(report.human_review_required)

    def test_codebase_reports_render(self) -> None:
        """Codebase compatibility reports should render in both formats."""
        report = analyze_codebase_compatibility_with_contract(
            FAKE_CODEBASE,
            NEW_CONTRACT,
        )

        self.assertIn(
            '"customer_files_modified": false', codebase_compatibility_report_to_json(report)
        )
        self.assertIn("Unknown / Manual Review", codebase_compatibility_report_to_markdown(report))


class CompatibilityCliAndSafetyTests(unittest.TestCase):
    """Exercise credential-free commands and source safety boundaries."""

    def test_cli_commands_work_without_credentials(self) -> None:
        """Build, validate, diff, and scan commands should use local metadata."""
        parser = build_parser()
        cases = [
            (
                ["maintenance", "compatibility-contract", "--format", "json"],
                ApiCompatibilityContract,
            ),
            (
                ["maintenance", "validate-contract", str(NEW_CONTRACT)],
                ApiCompatibilityValidationReport,
            ),
            (
                [
                    "maintenance",
                    "diff-contracts",
                    str(OLD_CONTRACT),
                    str(NEW_CONTRACT),
                ],
                ApiCompatibilityDiffReport,
            ),
            (
                [
                    "maintenance",
                    "compatibility-scan",
                    str(FAKE_CODEBASE),
                    "--contract",
                    str(NEW_CONTRACT),
                ],
                CodebaseCompatibilityReport,
            ),
        ]
        for arguments, expected_type in cases:
            with self.subTest(arguments=arguments):
                self.assertIsInstance(
                    run_command(parser.parse_args(arguments)),
                    expected_type,
                )

    def test_cli_output_writes_only_requested_contract(self) -> None:
        """CLI output should preserve safe overwrite behavior."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "current.json"
            args = build_parser().parse_args(
                [
                    "maintenance",
                    "compatibility-contract",
                    "--output",
                    str(output),
                ]
            )
            run_command(args)

            self.assertTrue(output.is_file())
            self.assertEqual(len(list(Path(directory).iterdir())), 1)
            with self.assertRaises(ValidationError):
                run_command(args)

    def test_sources_have_no_remote_git_github_or_execution_integrations(self) -> None:
        """Phase 18E implementation must remain standard-library local metadata."""
        source = "\n".join(
            (ROOT / "pyprocore" / "maintenance" / name).read_text(encoding="utf-8")
            for name in ["compatibility.py", "compatibility_reports.py"]
        ).lower()
        for forbidden in [
            "subprocess",
            "import requests",
            "from requests",
            "urllib",
            "httpx",
            "gitpython",
            "pygithub",
            "os.system",
            "api.github.com",
            "mcp.execute",
        ]:
            self.assertNotIn(forbidden, source)

    def test_fixture_contracts_are_plain_local_json(self) -> None:
        """Fixtures should parse without imports, credentials, or remote references."""
        for path in [OLD_CONTRACT, NEW_CONTRACT]:
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertIsInstance(payload, dict)
            self.assertNotIn("token", path.read_text(encoding="utf-8").lower())
            self.assertNotIn("https://", path.read_text(encoding="utf-8").lower())


if __name__ == "__main__":
    unittest.main()
