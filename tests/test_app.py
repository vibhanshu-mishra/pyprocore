"""Unit tests for the PyProcore command-line interface."""

from __future__ import annotations

import argparse
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pydantic import BaseModel

from pyprocore import app
from pyprocore.auth.diagnostics import AuthRefreshResult, AuthStatusReport
from pyprocore.core.doctor import DoctorReport, DoctorSummary


class SampleModel(BaseModel):
    """Small model used to validate CLI serialization."""

    id: int
    path: Path


class AppTestCase(unittest.TestCase):
    """Validate CLI parsing, command dispatch, and output formatting."""

    def test_build_parser_accepts_supported_commands(self) -> None:
        """The CLI parser accepts each public command shape."""
        parser = app.build_parser()

        self.assertEqual(parser.parse_args(["companies"]).command, "companies")
        doctor_args = parser.parse_args(["doctor", "--json", "--live"])
        self.assertEqual(doctor_args.command, "doctor")
        self.assertTrue(doctor_args.json_output)
        self.assertTrue(doctor_args.live)
        auth_status_args = parser.parse_args(["auth", "status", "--json"])
        self.assertEqual(auth_status_args.command, "auth")
        self.assertEqual(auth_status_args.auth_command, "status")
        self.assertTrue(auth_status_args.json_output)
        self.assertEqual(parser.parse_args(["auth", "refresh"]).auth_command, "refresh")
        self.assertEqual(parser.parse_args(["auth", "login-url"]).auth_command, "login-url")
        self.assertEqual(parser.parse_args(["find-company", "Tracker"]).name, "Tracker")
        self.assertEqual(parser.parse_args(["projects", "--company-id", "123"]).company_id, 123)
        self.assertEqual(parser.parse_args(["find-project", "Hospital"]).query, "Hospital")
        self.assertEqual(
            parser.parse_args(["find-project", "--number", "001"]).number,
            "001",
        )
        rfi_list_args = parser.parse_args(
            [
                "rfis",
                "--project",
                "10",
                "--status",
                "open",
                "--updated-after",
                "2026-07-01",
            ]
        )
        self.assertEqual(rfi_list_args.project_id, 10)
        self.assertEqual(rfi_list_args.status, "open")
        self.assertEqual(rfi_list_args.updated_after, "2026-07-01")
        self.assertEqual(
            parser.parse_args(["rfi", "--project", "10", "--id", "20"]).rfi_id,
            20,
        )
        self.assertEqual(
            parser.parse_args(["find-rfi", "--project", "10", "--number", "15"]).number,
            "15",
        )
        submittal_list_args = parser.parse_args(
            [
                "submittals",
                "--project-id",
                "10",
                "--status",
                "pending",
                "--updated-after",
                "2026-07-01",
            ]
        )
        self.assertEqual(submittal_list_args.project_id, 10)
        self.assertEqual(submittal_list_args.status, "pending")
        self.assertEqual(submittal_list_args.updated_after, "2026-07-01")
        self.assertEqual(
            parser.parse_args(["submittal", "--project", "10", "--id", "30"]).submittal_id,
            30,
        )
        self.assertEqual(
            parser.parse_args(["find-submittal", "--project", "10", "--number", "27"]).number,
            "27",
        )
        package_rfi = parser.parse_args(
            [
                "package-rfi",
                "--project-name",
                "Sandbox Test Project",
                "--number",
                "15",
                "--output-dir",
                "downloads/rfi",
                "--no-downloads",
            ]
        )
        self.assertEqual(package_rfi.command, "package-rfi")
        self.assertEqual(package_rfi.project_name, "Sandbox Test Project")
        self.assertEqual(package_rfi.item_number, "15")
        self.assertFalse(package_rfi.download_attachments)

        package_submittal = parser.parse_args(
            ["package-submittal", "--project", "10", "--id", "30", "--company", "123"]
        )
        self.assertEqual(package_submittal.command, "package-submittal")
        self.assertEqual(package_submittal.project_id, 10)
        self.assertEqual(package_submittal.item_id, 30)
        self.assertEqual(package_submittal.company_id, 123)

    def test_download_command_aliases_are_supported(self) -> None:
        """Legacy attachment command aliases still parse to the canonical command."""
        parser = app.build_parser()

        rfi_args = parser.parse_args(["download-rfi-attachments", "--project", "10", "--id", "20"])
        submittal_args = parser.parse_args(
            ["download-submittal-attachments", "--project", "10", "--id", "30"]
        )

        self.assertEqual(rfi_args.command, "download-rfi")
        self.assertEqual(rfi_args.legacy_command, "download-rfi-attachments")
        self.assertEqual(submittal_args.command, "download-submittal")
        self.assertEqual(submittal_args.legacy_command, "download-submittal-attachments")

    def test_run_command_dispatches_service_calls(self) -> None:
        """Parsed commands dispatch to the expected service function."""
        cases = [
            (argparse.Namespace(command="companies"), "list_companies", (), {}),
            (
                argparse.Namespace(command="find-company", name="Tracker"),
                "find_company",
                ("Tracker",),
                {},
            ),
            (
                argparse.Namespace(
                    command="rfis",
                    project_id=10,
                    status=None,
                    updated_after=None,
                    updated_before=None,
                    created_after=None,
                    created_before=None,
                ),
                "list_rfis",
                (10,),
                {
                    "status": None,
                    "updated_after": None,
                    "updated_before": None,
                    "created_after": None,
                    "created_before": None,
                },
            ),
            (
                argparse.Namespace(command="rfi", project_id=10, rfi_id=20),
                "get_rfi",
                (10, 20),
                {},
            ),
            (
                argparse.Namespace(command="find-rfi", project_id=10, number="15"),
                "find_rfi",
                (10,),
                {"number": "15"},
            ),
            (
                argparse.Namespace(
                    command="submittals",
                    project_id=10,
                    status=None,
                    updated_after=None,
                    updated_before=None,
                    created_after=None,
                    created_before=None,
                ),
                "list_submittals",
                (10,),
                {
                    "status": None,
                    "updated_after": None,
                    "updated_before": None,
                    "created_after": None,
                    "created_before": None,
                },
            ),
            (
                argparse.Namespace(command="submittal", project_id=10, submittal_id=30),
                "get_submittal",
                (10, 30),
                {},
            ),
            (
                argparse.Namespace(command="find-submittal", project_id=10, number="27"),
                "find_submittal",
                (10,),
                {"number": "27"},
            ),
        ]

        for args, function_name, expected_args, expected_kwargs in cases:
            with self.subTest(command=args.command):
                with patch.object(app, function_name, return_value="result") as function:
                    self.assertEqual(app.run_command(args), "result")
                    function.assert_called_once_with(*expected_args, **expected_kwargs)

    def test_run_command_passes_list_filters(self) -> None:
        """RFI and submittal list commands pass optional filter flags."""
        with patch.object(app, "list_rfis", return_value="rfis") as list_rfis:
            result = app.run_command(
                argparse.Namespace(
                    command="rfis",
                    project_id=10,
                    status="open",
                    updated_after="2026-07-01",
                    updated_before="2026-07-31",
                    created_after=None,
                    created_before=None,
                )
            )
        self.assertEqual(result, "rfis")
        list_rfis.assert_called_once_with(
            10,
            status="open",
            updated_after="2026-07-01",
            updated_before="2026-07-31",
            created_after=None,
            created_before=None,
        )

        with patch.object(app, "list_submittals", return_value="submittals") as list_submittals:
            result = app.run_command(
                argparse.Namespace(
                    command="submittals",
                    project_id=10,
                    status="pending",
                    updated_after="2026-07-01",
                    updated_before=None,
                    created_after="2026-01-01",
                    created_before=None,
                )
            )
        self.assertEqual(result, "submittals")
        list_submittals.assert_called_once_with(
            10,
            status="pending",
            updated_after="2026-07-01",
            updated_before=None,
            created_after="2026-01-01",
            created_before=None,
        )

    def test_run_doctor_dispatches_diagnostics(self) -> None:
        """Doctor command dispatches to diagnostics without live checks by default."""
        with patch.object(app, "run_doctor", return_value="report") as doctor:
            result = app.run_command(argparse.Namespace(command="doctor", live=False))

        self.assertEqual(result, "report")
        doctor.assert_called_once_with(live=False)

    def test_run_auth_commands_dispatch_to_helpers(self) -> None:
        """Auth command group dispatches to the matching helper."""
        with patch.object(app, "get_auth_status", return_value="status") as helper:
            result = app.run_command(argparse.Namespace(command="auth", auth_command="status"))
        self.assertEqual(result, "status")
        helper.assert_called_once_with()

        with patch.object(app, "refresh_auth_token", return_value="refresh") as helper:
            result = app.run_command(argparse.Namespace(command="auth", auth_command="refresh"))
        self.assertEqual(result, "refresh")
        helper.assert_called_once_with()

        with patch.object(app, "build_authorization_url", return_value="login") as helper:
            result = app.run_command(argparse.Namespace(command="auth", auth_command="login-url"))
        self.assertEqual(result, "login")
        helper.assert_called_once_with()

        with self.assertRaises(ValueError):
            app.run_command(argparse.Namespace(command="auth", auth_command="unknown"))

    def test_run_projects_uses_configured_company_when_omitted(self) -> None:
        """Project listing defaults to the configured company ID."""
        settings = Mock(company_id=456)

        with (
            patch.object(app, "get_settings", return_value=settings),
            patch.object(app, "list_projects", return_value="projects") as list_projects,
        ):
            result = app.run_command(argparse.Namespace(command="projects", company_id=None))

        self.assertEqual(result, "projects")
        list_projects.assert_called_once_with(456)

    def test_run_projects_uses_explicit_company_id(self) -> None:
        """Explicit project company IDs are passed through."""
        with patch.object(app, "list_projects", return_value="projects") as list_projects:
            result = app.run_command(argparse.Namespace(command="projects", company_id=123))

        self.assertEqual(result, "projects")
        list_projects.assert_called_once_with(123)

    def test_run_find_project_passes_query_number_and_company_id(self) -> None:
        """Project resolver CLI forwards query options."""
        with patch.object(app, "find_project", return_value="project") as find_project:
            result = app.run_command(
                argparse.Namespace(
                    command="find-project",
                    query="Hospital",
                    number=None,
                    company_id=123,
                )
            )

        self.assertEqual(result, "project")
        find_project.assert_called_once_with("Hospital", number=None, company_id=123)

    def test_run_download_commands_return_string_paths(self) -> None:
        """Download command output is converted to path strings."""
        with patch.object(
            app,
            "download_rfi_attachments",
            return_value=[Path("rfi.pdf")],
        ) as download_rfi:
            result = app.run_command(
                argparse.Namespace(
                    command="download-rfi",
                    project_id=10,
                    rfi_id=20,
                    destination_dir=Path("downloads"),
                )
            )

        self.assertEqual(result, ["rfi.pdf"])
        download_rfi.assert_called_once_with(10, 20, Path("downloads"))

        with patch.object(
            app,
            "download_submittal_attachments",
            return_value=[Path("submittal.pdf")],
        ) as download_submittal:
            result = app.run_command(
                argparse.Namespace(
                    command="download-submittal",
                    project_id=10,
                    submittal_id=30,
                    destination_dir=Path("downloads"),
                )
            )

        self.assertEqual(result, ["submittal.pdf"])
        download_submittal.assert_called_once_with(10, 30, Path("downloads"))

    def test_run_package_commands_build_workflow_packages(self) -> None:
        """Automation package commands build workflow inputs and return packages."""
        with patch.object(app, "build_workflow_package", return_value="package") as builder:
            result = app.run_command(
                argparse.Namespace(
                    command="package-rfi",
                    company_id=123,
                    project_id=None,
                    project_name="Sandbox",
                    project_number=None,
                    item_id=None,
                    item_number="15",
                    output_dir=Path("downloads/rfi"),
                    download_attachments=False,
                )
            )

        self.assertEqual(result, "package")
        automation_input = builder.call_args.args[0]
        self.assertEqual(automation_input.item_type, "rfi")
        self.assertEqual(automation_input.company_id, 123)
        self.assertEqual(automation_input.project_name, "Sandbox")
        self.assertEqual(automation_input.item_number, "15")
        self.assertFalse(automation_input.download_attachments)

        with patch.object(app, "build_workflow_package", return_value="package") as builder:
            result = app.run_command(
                argparse.Namespace(
                    command="package-submittal",
                    company_id=None,
                    project_id=10,
                    project_name=None,
                    project_number=None,
                    item_id=30,
                    item_number=None,
                    output_dir=None,
                    download_attachments=True,
                )
            )

        self.assertEqual(result, "package")
        automation_input = builder.call_args.args[0]
        self.assertEqual(automation_input.item_type, "submittal")
        self.assertEqual(automation_input.project_id, 10)
        self.assertEqual(automation_input.item_id, 30)

    def test_run_command_rejects_unknown_command(self) -> None:
        """Unsupported commands fail clearly."""
        with self.assertRaises(ValueError):
            app.run_command(argparse.Namespace(command="unknown"))

    def test_to_serializable_handles_nested_sdk_values(self) -> None:
        """CLI serialization handles models, paths, lists, tuples, and mappings."""
        value = {
            "model": SampleModel(id=1, path=Path("file.pdf")),
            "tuple": (Path("a.txt"), SampleModel(id=2, path=Path("b.txt"))),
        }

        self.assertEqual(
            app.to_serializable(value),
            {
                "model": {"id": 1, "path": "file.pdf"},
                "tuple": ["a.txt", {"id": 2, "path": "b.txt"}],
            },
        )

    def test_main_prints_serialized_json(self) -> None:
        """main parses arguments, runs a command, and prints formatted JSON."""
        with (
            patch.object(app, "build_parser") as build_parser,
            patch.object(app, "run_command", return_value={"ok": True}),
            patch("builtins.print") as print_function,
        ):
            parser = Mock()
            parser.parse_args.return_value = argparse.Namespace(command="companies")
            build_parser.return_value = parser

            app.main()

        print_function.assert_called_once()
        printed = print_function.call_args.args[0]
        self.assertEqual(json.loads(printed), {"ok": True})

    def test_main_prints_doctor_report_and_exits_with_report_code(self) -> None:
        """Doctor output controls CLI exit code."""
        report = DoctorReport(checks=[], summary=DoctorSummary(passed=1, warnings=0, failed=0))

        with (
            patch.object(app, "build_parser") as build_parser,
            patch.object(app, "run_command", return_value=report),
            patch.object(app, "format_doctor_report", return_value="doctor output"),
            patch("builtins.print") as print_function,
        ):
            parser = Mock()
            parser.parse_args.return_value = argparse.Namespace(
                command="doctor",
                json_output=False,
            )
            build_parser.return_value = parser

            with self.assertRaises(SystemExit) as context:
                app.main()

        self.assertEqual(context.exception.code, 0)
        print_function.assert_called_once_with("doctor output")

    def test_main_prints_auth_status_and_exits_with_report_code(self) -> None:
        """Auth status output controls CLI exit code."""
        report = AuthStatusReport(
            token_store_path="token.json",
            token_store_exists=True,
            token_store_readable=True,
            access_token_present=True,
            refresh_token_present=True,
            token_status="Valid",
            missing_configuration=[],
            errors=[],
            warnings=[],
        )

        with (
            patch.object(app, "build_parser") as build_parser,
            patch.object(app, "run_command", return_value=report),
            patch.object(app, "format_auth_status", return_value="auth status"),
            patch("builtins.print") as print_function,
        ):
            parser = Mock()
            parser.parse_args.return_value = argparse.Namespace(
                command="auth",
                auth_command="status",
                json_output=False,
            )
            build_parser.return_value = parser

            with self.assertRaises(SystemExit) as context:
                app.main()

        self.assertEqual(context.exception.code, 0)
        print_function.assert_called_once_with("auth status")

    def test_main_prints_auth_status_json(self) -> None:
        """Auth status can print JSON output."""
        report = AuthStatusReport(
            token_store_path="token.json",
            token_store_exists=False,
            token_store_readable=False,
            access_token_present=False,
            refresh_token_present=False,
            token_status="Missing",
            missing_configuration=[],
            errors=["Token store is missing."],
            warnings=[],
        )

        with (
            patch.object(app, "build_parser") as build_parser,
            patch.object(app, "run_command", return_value=report),
            patch("builtins.print") as print_function,
        ):
            parser = Mock()
            parser.parse_args.return_value = argparse.Namespace(
                command="auth",
                auth_command="status",
                json_output=True,
            )
            build_parser.return_value = parser

            with self.assertRaises(SystemExit) as context:
                app.main()

        self.assertEqual(context.exception.code, 1)
        printed = json.loads(print_function.call_args.args[0])
        self.assertEqual(printed["token_status"], "Missing")

    def test_main_prints_auth_refresh_and_exits_with_result_code(self) -> None:
        """Auth refresh output controls CLI exit code."""
        result = AuthRefreshResult(success=False, message="failed", error="bad token")

        with (
            patch.object(app, "build_parser") as build_parser,
            patch.object(app, "run_command", return_value=result),
            patch.object(app, "format_auth_refresh", return_value="refresh failed"),
            patch("builtins.print") as print_function,
        ):
            parser = Mock()
            parser.parse_args.return_value = argparse.Namespace(
                command="auth",
                auth_command="refresh",
            )
            build_parser.return_value = parser

            with self.assertRaises(SystemExit) as context:
                app.main()

        self.assertEqual(context.exception.code, 1)
        print_function.assert_called_once_with("refresh failed")

    def test_main_prints_auth_login_url(self) -> None:
        """Auth login URL output exits successfully."""
        result = app.AuthLoginUrlResult(
            authorization_url="https://login.example/oauth/authorize?response_type=code",
            redirect_uri="http://localhost/callback",
        )

        with (
            patch.object(app, "build_parser") as build_parser,
            patch.object(app, "run_command", return_value=result),
            patch.object(app, "format_login_url", return_value="login url"),
            patch("builtins.print") as print_function,
        ):
            parser = Mock()
            parser.parse_args.return_value = argparse.Namespace(
                command="auth",
                auth_command="login-url",
            )
            build_parser.return_value = parser

            with self.assertRaises(SystemExit) as context:
                app.main()

        self.assertEqual(context.exception.code, 0)
        print_function.assert_called_once_with("login url")


if __name__ == "__main__":
    unittest.main()
