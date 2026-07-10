"""Unit tests for the PyProcore command-line interface."""

from __future__ import annotations

import argparse
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pydantic import BaseModel

from pyprocore import app
from pyprocore.auth.diagnostics import AuthExchangeResult, AuthRefreshResult, AuthStatusReport
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
        exchange_args = parser.parse_args(["auth", "exchange-code", "code-123"])
        self.assertEqual(exchange_args.auth_command, "exchange-code")
        self.assertEqual(exchange_args.code, "code-123")
        exchange_alias_args = parser.parse_args(["auth", "exchange", "code-123"])
        self.assertEqual(exchange_alias_args.auth_command, "exchange-code")
        self.assertEqual(exchange_alias_args.code, "code-123")
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

        document_folders = parser.parse_args(
            ["document-folders", "--project", "10", "--parent", "5", "--company-id", "123"]
        )
        self.assertEqual(document_folders.command, "document-folders")
        self.assertEqual(document_folders.project_id, 10)
        self.assertEqual(document_folders.parent_id, 5)
        self.assertEqual(document_folders.company_id, 123)
        self.assertEqual(
            parser.parse_args(["document-folder", "--project", "10", "--id", "5"]).folder_id,
            5,
        )
        self.assertEqual(
            parser.parse_args(
                ["find-document-folder", "--project", "10", "--name", "Drawings"]
            ).name,
            "Drawings",
        )
        documents = parser.parse_args(
            ["documents", "--project", "10", "--folder", "5", "--recursive"]
        )
        self.assertEqual(documents.command, "documents")
        self.assertEqual(documents.folder_id, 5)
        self.assertTrue(documents.recursive)
        self.assertEqual(
            parser.parse_args(["document", "--project", "10", "--id", "99"]).document_id,
            99,
        )
        self.assertEqual(
            parser.parse_args(
                ["find-document", "--project", "10", "--filename", "plan.pdf"]
            ).filename,
            "plan.pdf",
        )
        download_document = parser.parse_args(
            [
                "download-document",
                "--project",
                "10",
                "--id",
                "99",
                "--output",
                "docs",
                "--filename",
                "plan.pdf",
                "--overwrite",
            ]
        )
        self.assertEqual(download_document.command, "download-document")
        self.assertEqual(download_document.output_dir, Path("docs"))
        self.assertTrue(download_document.overwrite)

        drawing_areas = parser.parse_args(
            ["drawing-areas", "--project", "10", "--company-id", "123"]
        )
        self.assertEqual(drawing_areas.command, "drawing-areas")
        self.assertEqual(drawing_areas.project_id, 10)
        self.assertEqual(drawing_areas.company_id, 123)
        self.assertEqual(
            parser.parse_args(["drawing-area", "--project", "10", "--id", "5"]).drawing_area_id,
            5,
        )
        self.assertEqual(
            parser.parse_args(["drawing-disciplines", "--project", "10"]).command,
            "drawing-disciplines",
        )
        drawings = parser.parse_args(
            [
                "drawings",
                "--project",
                "10",
                "--area",
                "5",
                "--discipline",
                "6",
                "--current",
            ]
        )
        self.assertEqual(drawings.command, "drawings")
        self.assertEqual(drawings.drawing_area_id, 5)
        self.assertEqual(drawings.discipline_id, 6)
        self.assertTrue(drawings.current)
        self.assertEqual(
            parser.parse_args(["drawing", "--project", "10", "--id", "99"]).drawing_id,
            99,
        )
        self.assertEqual(
            parser.parse_args(["find-drawing", "--project", "10", "--number", "S-101"]).number,
            "S-101",
        )
        self.assertEqual(
            parser.parse_args(["find-drawings", "--project", "10", "--contains", "stair"]).text,
            "stair",
        )
        download_drawing = parser.parse_args(
            [
                "download-drawing",
                "--project",
                "10",
                "--id",
                "99",
                "--output",
                "drawings",
                "--filename",
                "S-101.pdf",
                "--overwrite",
            ]
        )
        self.assertEqual(download_drawing.command, "download-drawing")
        self.assertEqual(download_drawing.output_dir, Path("drawings"))
        self.assertTrue(download_drawing.overwrite)

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

        export_rfis = parser.parse_args(
            [
                "export-rfis",
                "--project",
                "10",
                "--output",
                "rfis.csv",
                "--status",
                "open",
            ]
        )
        self.assertEqual(export_rfis.command, "export-rfis")
        self.assertEqual(export_rfis.project_id, 10)
        self.assertEqual(export_rfis.output_path, Path("rfis.csv"))
        self.assertEqual(export_rfis.status, "open")

        sync_submittals = parser.parse_args(
            [
                "sync-submittals",
                "--project",
                "10",
                "--output",
                "out",
                "--no-attachments",
                "--overwrite",
                "--no-tracker",
                "--no-markdown",
                "--dry-run",
            ]
        )
        self.assertEqual(sync_submittals.command, "sync-submittals")
        self.assertFalse(sync_submittals.download_attachments)
        self.assertTrue(sync_submittals.overwrite)
        self.assertFalse(sync_submittals.create_tracker)
        self.assertFalse(sync_submittals.create_markdown)
        self.assertTrue(sync_submittals.dry_run)

        sync_project = parser.parse_args(
            [
                "sync-project",
                "--project",
                "10",
                "--output",
                "project-out",
                "--rfis-only",
                "--incremental",
            ]
        )
        self.assertEqual(sync_project.command, "sync-project")
        self.assertTrue(sync_project.rfis_only)
        self.assertFalse(sync_project.submittals_only)
        self.assertTrue(sync_project.incremental)

        sync_documents = parser.parse_args(
            [
                "sync-documents",
                "--project",
                "10",
                "--output",
                "documents",
                "--folder",
                "5",
                "--recursive",
                "--dry-run",
                "--incremental",
            ]
        )
        self.assertEqual(sync_documents.command, "sync-documents")
        self.assertEqual(sync_documents.folder_id, 5)
        self.assertTrue(sync_documents.recursive)
        self.assertTrue(sync_documents.dry_run)
        self.assertTrue(sync_documents.incremental)

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

        with patch.object(app, "exchange_code_and_save", return_value="exchange") as helper:
            result = app.run_command(
                argparse.Namespace(
                    command="auth",
                    auth_command="exchange-code",
                    code="code-123",
                )
            )
        self.assertEqual(result, "exchange")
        helper.assert_called_once_with("code-123")

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

    def test_run_document_commands_dispatch_to_helpers(self) -> None:
        """Document commands call document service helpers."""
        with patch.object(app, "list_document_folders", return_value="folders") as helper:
            result = app.run_command(
                argparse.Namespace(
                    command="document-folders",
                    project_id=10,
                    parent_id=5,
                    company_id=123,
                )
            )
        self.assertEqual(result, "folders")
        helper.assert_called_once_with(10, parent_id=5, company_id=123)

        with patch.object(app, "get_document_folder", return_value="folder") as helper:
            result = app.run_command(
                argparse.Namespace(
                    command="document-folder",
                    project_id=10,
                    folder_id=5,
                    company_id=123,
                )
            )
        self.assertEqual(result, "folder")
        helper.assert_called_once_with(10, 5, company_id=123)

        with patch.object(app, "find_document_folder", return_value="folder") as helper:
            result = app.run_command(
                argparse.Namespace(
                    command="find-document-folder",
                    project_id=10,
                    name="Drawings",
                )
            )
        self.assertEqual(result, "folder")
        helper.assert_called_once_with(10, "Drawings")

        with patch.object(app, "list_documents", return_value="documents") as helper:
            result = app.run_command(
                argparse.Namespace(
                    command="documents",
                    project_id=10,
                    folder_id=5,
                    recursive=True,
                    company_id=123,
                )
            )
        self.assertEqual(result, "documents")
        helper.assert_called_once_with(10, folder_id=5, recursive=True, company_id=123)

        with patch.object(app, "get_document", return_value="document") as helper:
            result = app.run_command(
                argparse.Namespace(
                    command="document",
                    project_id=10,
                    document_id=99,
                    company_id=123,
                )
            )
        self.assertEqual(result, "document")
        helper.assert_called_once_with(10, 99, company_id=123)

        with patch.object(app, "find_document", return_value="document") as helper:
            result = app.run_command(
                argparse.Namespace(
                    command="find-document",
                    project_id=10,
                    name=None,
                    filename="plan.pdf",
                )
            )
        self.assertEqual(result, "document")
        helper.assert_called_once_with(10, name=None, filename="plan.pdf")

        with patch.object(app, "download_document", return_value=Path("plan.pdf")) as helper:
            result = app.run_command(
                argparse.Namespace(
                    command="download-document",
                    project_id=10,
                    document_id=99,
                    output_dir=Path("docs"),
                    filename="plan.pdf",
                    company_id=123,
                    overwrite=True,
                )
            )
        self.assertEqual(result, Path("plan.pdf"))
        helper.assert_called_once_with(
            10,
            99,
            output_dir=Path("docs"),
            filename="plan.pdf",
            company_id=123,
            overwrite=True,
        )

    def test_run_drawing_commands_dispatch_to_helpers(self) -> None:
        """Drawing commands call drawing service helpers."""
        with patch.object(app, "list_drawing_areas", return_value="areas") as helper:
            result = app.run_command(
                argparse.Namespace(command="drawing-areas", project_id=10, company_id=123)
            )
        self.assertEqual(result, "areas")
        helper.assert_called_once_with(10, company_id=123)

        with patch.object(app, "get_drawing_area", return_value="area") as helper:
            result = app.run_command(
                argparse.Namespace(
                    command="drawing-area",
                    project_id=10,
                    drawing_area_id=5,
                    company_id=123,
                )
            )
        self.assertEqual(result, "area")
        helper.assert_called_once_with(10, 5, company_id=123)

        with patch.object(app, "list_drawing_disciplines", return_value="disciplines") as helper:
            result = app.run_command(
                argparse.Namespace(command="drawing-disciplines", project_id=10, company_id=123)
            )
        self.assertEqual(result, "disciplines")
        helper.assert_called_once_with(10, company_id=123)

        with patch.object(app, "list_drawings", return_value="drawings") as helper:
            result = app.run_command(
                argparse.Namespace(
                    command="drawings",
                    project_id=10,
                    company_id=123,
                    drawing_area_id=5,
                    discipline_id=6,
                    current=True,
                )
            )
        self.assertEqual(result, "drawings")
        helper.assert_called_once_with(
            10,
            company_id=123,
            drawing_area_id=5,
            discipline_id=6,
            current=True,
        )

        with patch.object(app, "get_drawing", return_value="drawing") as helper:
            result = app.run_command(
                argparse.Namespace(command="drawing", project_id=10, drawing_id=99, company_id=123)
            )
        self.assertEqual(result, "drawing")
        helper.assert_called_once_with(10, 99, company_id=123)

        with patch.object(app, "find_drawing", return_value="drawing") as helper:
            result = app.run_command(
                argparse.Namespace(
                    command="find-drawing",
                    project_id=10,
                    number="S-101",
                    title=None,
                    company_id=123,
                )
            )
        self.assertEqual(result, "drawing")
        helper.assert_called_once_with(10, number="S-101", title=None, company_id=123)

        with patch.object(app, "find_drawings_contains", return_value=["drawing"]) as helper:
            result = app.run_command(
                argparse.Namespace(
                    command="find-drawings",
                    project_id=10,
                    text="stair",
                    company_id=123,
                )
            )
        self.assertEqual(result, ["drawing"])
        helper.assert_called_once_with(10, "stair", company_id=123)

        with patch.object(app, "download_drawing", return_value=Path("S-101.pdf")) as helper:
            result = app.run_command(
                argparse.Namespace(
                    command="download-drawing",
                    project_id=10,
                    drawing_id=99,
                    output_dir=Path("drawings"),
                    filename="S-101.pdf",
                    company_id=123,
                    overwrite=True,
                )
            )
        self.assertEqual(result, Path("S-101.pdf"))
        helper.assert_called_once_with(
            10,
            99,
            output_dir=Path("drawings"),
            filename="S-101.pdf",
            company_id=123,
            overwrite=True,
        )

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

    def test_run_workflow_export_commands_dispatch_to_helpers(self) -> None:
        """Workflow export commands call CSV helpers with filters."""
        with patch.object(app, "export_rfis_to_csv", return_value=Path("rfis.csv")) as export:
            result = app.run_command(
                argparse.Namespace(
                    command="export-rfis",
                    project_id=10,
                    output_path=Path("rfis.csv"),
                    status="open",
                    updated_after="2026-07-01",
                    updated_before=None,
                    created_after=None,
                    created_before=None,
                )
            )

        self.assertEqual(result, Path("rfis.csv"))
        export.assert_called_once_with(
            10,
            Path("rfis.csv"),
            status="open",
            updated_after="2026-07-01",
            updated_before=None,
            created_after=None,
            created_before=None,
        )

        with patch.object(
            app,
            "export_submittals_to_csv",
            return_value=Path("submittals.csv"),
        ) as export:
            result = app.run_command(
                argparse.Namespace(
                    command="export-submittals",
                    project_id=10,
                    output_path=Path("submittals.csv"),
                    status=None,
                    updated_after=None,
                    updated_before=None,
                    created_after="2026-01-01",
                    created_before=None,
                )
            )

        self.assertEqual(result, Path("submittals.csv"))
        export.assert_called_once_with(
            10,
            Path("submittals.csv"),
            status=None,
            updated_after=None,
            updated_before=None,
            created_after="2026-01-01",
            created_before=None,
        )

    def test_run_workflow_sync_commands_dispatch_to_helpers(self) -> None:
        """Workflow sync commands call folder sync helpers with options."""
        with patch.object(app, "sync_rfis_to_folder", return_value="sync") as sync:
            result = app.run_command(
                argparse.Namespace(
                    command="sync-rfis",
                    project_id=10,
                    output_path=Path("rfis"),
                    status="open",
                    updated_after=None,
                    updated_before=None,
                    created_after=None,
                    created_before=None,
                    download_attachments=False,
                    overwrite=True,
                    create_tracker=False,
                    create_markdown=False,
                    dry_run=True,
                )
            )

        self.assertEqual(result, "sync")
        sync.assert_called_once_with(
            10,
            Path("rfis"),
            status="open",
            updated_after=None,
            updated_before=None,
            created_after=None,
            created_before=None,
            download_attachments=False,
            overwrite=True,
            create_tracker=False,
            create_markdown=False,
            dry_run=True,
            incremental=False,
        )

        with patch.object(app, "sync_documents_to_folder", return_value="sync-docs") as sync:
            result = app.run_command(
                argparse.Namespace(
                    command="sync-documents",
                    project_id=10,
                    output_path=Path("documents"),
                    folder_id=5,
                    recursive=True,
                    overwrite=True,
                    create_tracker=False,
                    create_markdown=False,
                    dry_run=True,
                    incremental=True,
                )
            )

        self.assertEqual(result, "sync-docs")
        sync.assert_called_once_with(
            10,
            Path("documents"),
            folder_id=5,
            recursive=True,
            overwrite=True,
            create_tracker=False,
            create_markdown=False,
            dry_run=True,
            incremental=True,
        )

    def test_run_project_sync_command_dispatches_to_helper(self) -> None:
        """Project sync command validates flags and calls the workflow helper."""
        with patch.object(app, "sync_project_to_folder", return_value="project-sync") as sync:
            result = app.run_command(
                argparse.Namespace(
                    command="sync-project",
                    project_id=10,
                    output_path=Path("project"),
                    status="open",
                    updated_after="2026-07-01",
                    updated_before=None,
                    created_after=None,
                    created_before=None,
                    download_attachments=False,
                    overwrite=True,
                    create_tracker=True,
                    create_markdown=True,
                    dry_run=True,
                    incremental=True,
                    rfis_only=True,
                    submittals_only=False,
                )
            )

        self.assertEqual(result, "project-sync")
        sync.assert_called_once_with(
            10,
            Path("project"),
            include_rfis=True,
            include_submittals=False,
            status="open",
            updated_after="2026-07-01",
            updated_before=None,
            created_after=None,
            created_before=None,
            download_attachments=False,
            overwrite=True,
            create_tracker=True,
            create_markdown=True,
            dry_run=True,
            incremental=True,
        )

        with self.assertRaisesRegex(ValueError, "either --rfis-only or --submittals-only"):
            app.run_command(
                argparse.Namespace(
                    command="sync-project",
                    rfis_only=True,
                    submittals_only=True,
                )
            )

        with patch.object(app, "sync_submittals_to_folder", return_value="sync") as sync:
            result = app.run_command(
                argparse.Namespace(
                    command="sync-submittals",
                    project_id=10,
                    output_path=Path("submittals"),
                    status=None,
                    updated_after="2026-07-01",
                    updated_before=None,
                    created_after=None,
                    created_before=None,
                    download_attachments=True,
                    overwrite=False,
                    create_tracker=True,
                    create_markdown=True,
                    dry_run=False,
                )
            )

        self.assertEqual(result, "sync")
        sync.assert_called_once_with(
            10,
            Path("submittals"),
            status=None,
            updated_after="2026-07-01",
            updated_before=None,
            created_after=None,
            created_before=None,
            download_attachments=True,
            overwrite=False,
            create_tracker=True,
            create_markdown=True,
            dry_run=False,
            incremental=False,
        )

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

    def test_format_export_and_sync_summaries(self) -> None:
        """Workflow CLI summaries are beginner-friendly."""
        export_summary = app.format_export_summary(Path("rfis.csv"))
        self.assertIn("Export complete.", export_summary)
        self.assertIn("Output: rfis.csv", export_summary)

        sync_result = app.SyncResult(
            output_dir=Path("out"),
            item_type="rfi",
            project_id=352338,
            item_count=2,
            tracker_path=Path("out/rfi_tracker.csv"),
            manifest_path=Path("out/sync_manifest.json"),
            downloaded_files=[Path("a.pdf"), Path("b.pdf")],
        )
        sync_summary = app.format_sync_summary(sync_result)
        self.assertIn("RFI sync complete.", sync_summary)
        self.assertIn("Items synced: 2", sync_summary)
        self.assertIn("Attachments downloaded: 2", sync_summary)

        dry_run_result = app.SyncResult(
            output_dir=Path("out"),
            item_type="submittal",
            project_id=352338,
            item_count=1,
            tracker_path=Path("out/submittal_tracker.csv"),
            dry_run=True,
            warnings=["Dry run: no files were written."],
        )
        dry_run_summary = app.format_sync_summary(dry_run_result)
        self.assertIn("SUBMITTAL sync planned.", dry_run_summary)
        self.assertIn("Manifest: not written during dry run", dry_run_summary)
        self.assertIn("Dry run: no files were written.", dry_run_summary)

        project_summary = app.format_project_sync_summary(
            app.ProjectSyncResult(
                output_dir=Path("out"),
                project_id=352338,
                item_count=3,
                synced_count=2,
                skipped_count=1,
                warning_count=0,
                error_count=0,
            )
        )
        self.assertIn("Project sync complete.", project_summary)
        self.assertIn("Items skipped: 1", project_summary)

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

    def test_main_prints_workflow_summaries(self) -> None:
        """Workflow commands print human-readable summaries."""
        with (
            patch.object(app, "build_parser") as build_parser,
            patch.object(app, "run_command", return_value=Path("rfis.csv")),
            patch("builtins.print") as print_function,
        ):
            parser = Mock()
            parser.parse_args.return_value = argparse.Namespace(command="export-rfis")
            build_parser.return_value = parser

            app.main()

        self.assertIn("Export complete.", print_function.call_args.args[0])

        sync_result = app.SyncResult(
            output_dir=Path("out"),
            item_type="rfi",
            project_id=352338,
            item_count=1,
            dry_run=True,
        )
        with (
            patch.object(app, "build_parser") as build_parser,
            patch.object(app, "run_command", return_value=sync_result),
            patch("builtins.print") as print_function,
        ):
            parser = Mock()
            parser.parse_args.return_value = argparse.Namespace(command="sync-rfis")
            build_parser.return_value = parser

            app.main()

        self.assertIn("RFI sync planned.", print_function.call_args.args[0])

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

    def test_main_prints_auth_exchange_and_exits_with_result_code(self) -> None:
        """Auth exchange output controls CLI exit code."""
        result = AuthExchangeResult(
            success=True,
            message="Authorization code exchanged successfully.",
            token_store_updated=True,
            access_token_present=True,
            refresh_token_present=True,
        )

        with (
            patch.object(app, "build_parser") as build_parser,
            patch.object(app, "run_command", return_value=result),
            patch.object(app, "format_auth_exchange", return_value="exchange ok"),
            patch("builtins.print") as print_function,
        ):
            parser = Mock()
            parser.parse_args.return_value = argparse.Namespace(
                command="auth",
                auth_command="exchange-code",
                code="code-123",
            )
            build_parser.return_value = parser

            with self.assertRaises(SystemExit) as context:
                app.main()

        self.assertEqual(context.exception.code, 0)
        print_function.assert_called_once_with("exchange ok")

    def test_main_prints_auth_exchange_failure(self) -> None:
        """Auth exchange failures exit with code 1."""
        result = AuthExchangeResult(
            success=False,
            message="Authorization code exchange failed.",
            error="bad code",
        )

        with (
            patch.object(app, "build_parser") as build_parser,
            patch.object(app, "run_command", return_value=result),
            patch.object(app, "format_auth_exchange", return_value="exchange failed"),
            patch("builtins.print") as print_function,
        ):
            parser = Mock()
            parser.parse_args.return_value = argparse.Namespace(
                command="auth",
                auth_command="exchange-code",
                code="bad-code",
            )
            build_parser.return_value = parser

            with self.assertRaises(SystemExit) as context:
                app.main()

        self.assertEqual(context.exception.code, 1)
        print_function.assert_called_once_with("exchange failed")

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
