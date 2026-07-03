"""Unit tests for the PyProcore command-line interface."""

from __future__ import annotations

import argparse
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pydantic import BaseModel

from pyprocore import app


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
        self.assertEqual(parser.parse_args(["projects", "--company-id", "123"]).company_id, 123)
        self.assertEqual(parser.parse_args(["rfis", "--project", "10"]).project_id, 10)
        self.assertEqual(
            parser.parse_args(["rfi", "--project", "10", "--id", "20"]).rfi_id,
            20,
        )
        self.assertEqual(
            parser.parse_args(["submittals", "--project-id", "10"]).project_id,
            10,
        )
        self.assertEqual(
            parser.parse_args(["submittal", "--project", "10", "--id", "30"]).submittal_id,
            30,
        )

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
                argparse.Namespace(command="rfis", project_id=10),
                "list_rfis",
                (10,),
                {},
            ),
            (
                argparse.Namespace(command="rfi", project_id=10, rfi_id=20),
                "get_rfi",
                (10, 20),
                {},
            ),
            (
                argparse.Namespace(command="submittals", project_id=10),
                "list_submittals",
                (10,),
                {},
            ),
            (
                argparse.Namespace(command="submittal", project_id=10, submittal_id=30),
                "get_submittal",
                (10, 30),
                {},
            ),
        ]

        for args, function_name, expected_args, expected_kwargs in cases:
            with self.subTest(command=args.command):
                with patch.object(app, function_name, return_value="result") as function:
                    self.assertEqual(app.run_command(args), "result")
                    function.assert_called_once_with(*expected_args, **expected_kwargs)

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


if __name__ == "__main__":
    unittest.main()
