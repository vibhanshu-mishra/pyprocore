"""Unit tests for automation workflow package builders."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pyprocore
from pyprocore.automation import (
    AutomationInput,
    DownloadedFile,
    WorkflowPackage,
    build_rfi_package,
    build_submittal_package,
    build_workflow_package,
)
from pyprocore.automation.resolver import resolve_project, resolve_rfi, resolve_submittal
from pyprocore.core.exceptions import ValidationError
from pyprocore.models import RFI, Project, Submittal


class AutomationResolverTestCase(unittest.TestCase):
    """Validate automation input resolution."""

    def test_resolve_project_uses_project_id_directly(self) -> None:
        """Project IDs resolve without API or search calls."""
        with patch("pyprocore.automation.resolver.find_project") as find_project:
            project = resolve_project(AutomationInput(project_id=352338, item_type="rfi"))

        self.assertEqual(project.id, 352338)
        self.assertIsNone(project.name)
        find_project.assert_not_called()

    def test_resolve_project_by_name(self) -> None:
        """Project names delegate to the search layer."""
        expected = Project(id=1, name="Sandbox Test Project")

        with patch(
            "pyprocore.automation.resolver.find_project",
            return_value=expected,
        ) as find_project:
            project = resolve_project(
                AutomationInput(
                    company_id=10,
                    project_name="Sandbox",
                    item_type="rfi",
                )
            )

        self.assertIs(project, expected)
        find_project.assert_called_once_with("Sandbox", company_id=10)

    def test_resolve_project_by_number(self) -> None:
        """Project numbers delegate to the search layer."""
        expected = Project(id=2, name="Project 001", project_number="001")

        with patch(
            "pyprocore.automation.resolver.find_project",
            return_value=expected,
        ) as find_project:
            project = resolve_project(
                AutomationInput(
                    company_id=10,
                    project_number="001",
                    item_type="rfi",
                )
            )

        self.assertIs(project, expected)
        find_project.assert_called_once_with(number="001", company_id=10)

    def test_resolve_project_requires_identifier(self) -> None:
        """Missing project identifiers fail clearly."""
        with self.assertRaises(ValidationError):
            resolve_project(AutomationInput(item_type="rfi"))

        with self.assertRaises(ValidationError):
            resolve_project(AutomationInput(project_id=0, item_type="rfi"))

    def test_resolve_rfi_by_id_or_number(self) -> None:
        """RFI resolution supports IDs and numbers."""
        with patch("pyprocore.automation.resolver.get_rfi", return_value=RFI(id=7)) as get_rfi:
            rfi = resolve_rfi(AutomationInput(project_id=1, item_type="rfi", item_id=7), 1)

        self.assertEqual(rfi.id, 7)
        get_rfi.assert_called_once_with(1, 7)

        with patch(
            "pyprocore.automation.resolver.find_rfi",
            return_value=RFI(id=8, number="15"),
        ) as find_rfi:
            rfi = resolve_rfi(
                AutomationInput(project_id=1, item_type="rfi", item_number="15"),
                1,
            )

        self.assertEqual(rfi.id, 8)
        find_rfi.assert_called_once_with(1, number="15")

    def test_resolve_submittal_by_id_or_number(self) -> None:
        """Submittal resolution supports IDs and numbers."""
        with patch(
            "pyprocore.automation.resolver.get_submittal",
            return_value=Submittal(id=9),
        ) as get_submittal:
            submittal = resolve_submittal(
                AutomationInput(project_id=1, item_type="submittal", item_id=9),
                1,
            )

        self.assertEqual(submittal.id, 9)
        get_submittal.assert_called_once_with(1, 9)

        with patch(
            "pyprocore.automation.resolver.find_submittal",
            return_value=Submittal(id=10, number="27"),
        ) as find_submittal:
            submittal = resolve_submittal(
                AutomationInput(project_id=1, item_type="submittal", item_number="27"),
                1,
            )

        self.assertEqual(submittal.id, 10)
        find_submittal.assert_called_once_with(1, number="27")

    def test_resolve_item_requires_identifier(self) -> None:
        """Missing item identifiers fail clearly."""
        with self.assertRaises(ValidationError):
            resolve_rfi(AutomationInput(project_id=1, item_type="rfi"), 1)

        with self.assertRaises(ValidationError):
            resolve_submittal(AutomationInput(project_id=1, item_type="submittal"), 1)


class AutomationWorkflowTestCase(unittest.TestCase):
    """Validate workflow package construction."""

    def test_build_rfi_package_downloads_question_attachments(self) -> None:
        """RFI workflow packages include downloaded question attachments."""
        file_service = Mock()
        file_service.download_attachment.side_effect = [
            Path("/tmp/rfi/one.pdf"),
            Path("/tmp/rfi/two.pdf"),
        ]

        with (
            patch(
                "pyprocore.automation.workflows.resolve_project",
                return_value=Project(id=352338, name="Sandbox"),
            ),
            patch(
                "pyprocore.automation.workflows.resolve_rfi",
                return_value=RFI(id=102784, number="15"),
            ),
            patch(
                "pyprocore.automation.workflows.get_rfi",
                return_value=RFI(
                    id=102784,
                    number="15",
                    subject="Question about door hardware",
                    questions=[
                        {
                            "attachments": [
                                {
                                    "url": "https://signed.example/one.pdf",
                                    "content_type": "application/pdf",
                                },
                                {"url": "https://signed.example/two.pdf"},
                            ]
                        }
                    ],
                ),
            ) as get_rfi,
            patch("pyprocore.automation.workflows.FileDownloadService", return_value=file_service),
        ):
            package = build_workflow_package(
                AutomationInput(
                    project_name="Sandbox",
                    item_type="rfi",
                    item_number="15",
                    output_dir=Path("/tmp/rfi"),
                )
            )

        self.assertEqual(package.item_type, "rfi")
        self.assertEqual(package.project_id, 352338)
        self.assertEqual(package.project_name, "Sandbox")
        self.assertEqual(package.item_id, 102784)
        self.assertEqual(package.item_number, "15")
        self.assertEqual(package.title, "Question about door hardware")
        self.assertEqual([file.filename for file in package.attachments], ["one.pdf", "two.pdf"])
        self.assertEqual(package.attachments[0].source_url, "https://signed.example/one.pdf")
        self.assertEqual(package.attachments[0].content_type, "application/pdf")
        self.assertEqual(package.raw["id"], 102784)
        get_rfi.assert_called_once_with(352338, 102784)
        self.assertEqual(file_service.download_attachment.call_count, 2)

    def test_build_submittal_package_downloads_attachments(self) -> None:
        """Submittal workflow packages include downloaded attachments."""
        file_service = Mock()
        file_service.download_attachment.return_value = Path("/tmp/submittal/spec.pdf")

        with (
            patch(
                "pyprocore.automation.workflows.resolve_project",
                return_value=Project(id=352338, name="Sandbox"),
            ),
            patch(
                "pyprocore.automation.workflows.resolve_submittal",
                return_value=Submittal(id=309641, number="27"),
            ),
            patch(
                "pyprocore.automation.workflows.get_submittal",
                return_value=Submittal(
                    id=309641,
                    number="27",
                    title="Door hardware",
                    attachments=[
                        {
                            "url": "https://signed.example/spec.pdf",
                            "content_type": "application/pdf",
                        }
                    ],
                ),
            ) as get_submittal,
            patch("pyprocore.automation.workflows.FileDownloadService", return_value=file_service),
        ):
            package = build_workflow_package(
                AutomationInput(
                    project_id=352338,
                    item_type="submittal",
                    item_number="27",
                    output_dir="/tmp/submittal",
                )
            )

        self.assertEqual(package.item_type, "submittal")
        self.assertEqual(package.item_id, 309641)
        self.assertEqual(package.title, "Door hardware")
        self.assertEqual(package.attachments[0].filename, "spec.pdf")
        self.assertEqual(package.attachments[0].path, Path("/tmp/submittal/spec.pdf"))
        get_submittal.assert_called_once_with(352338, 309641)

    def test_id_based_package_uses_resolved_detail_without_refetch(self) -> None:
        """ID-based workflows avoid duplicate detail fetches."""
        with (
            patch(
                "pyprocore.automation.workflows.resolve_project",
                return_value=Project(id=1, name="Project"),
            ),
            patch(
                "pyprocore.automation.workflows.resolve_rfi",
                return_value=RFI(id=2, number="15", subject="Resolved detail"),
            ),
            patch("pyprocore.automation.workflows.get_rfi") as get_rfi,
        ):
            package = build_workflow_package(
                AutomationInput(
                    project_id=1,
                    item_type="rfi",
                    item_id=2,
                    download_attachments=False,
                )
            )

        self.assertEqual(package.title, "Resolved detail")
        get_rfi.assert_not_called()

    def test_downloads_can_be_disabled(self) -> None:
        """Workflow packages can return metadata without downloading attachments."""
        with (
            patch(
                "pyprocore.automation.workflows.resolve_project",
                return_value=Project(id=1, name="Project"),
            ),
            patch(
                "pyprocore.automation.workflows.resolve_rfi",
                return_value=RFI(id=2, number="15"),
            ),
            patch(
                "pyprocore.automation.workflows.get_rfi",
                return_value=RFI(
                    id=2,
                    number="15",
                    questions=[{"attachments": [{"url": "https://signed.example/file.pdf"}]}],
                ),
            ),
            patch("pyprocore.automation.workflows.FileDownloadService") as service_class,
        ):
            package = build_workflow_package(
                AutomationInput(
                    project_id=1,
                    item_type="rfi",
                    item_id=2,
                    download_attachments=False,
                )
            )

        self.assertEqual(package.attachments, [])
        service_class.assert_not_called()

    def test_default_output_dir_uses_item_number_when_available(self) -> None:
        """Workflow downloads default to downloads/{item_type}_{number_or_id}."""
        file_service = Mock()
        file_service.download_attachment.return_value = Path("/tmp/ignored/file.pdf")

        with (
            patch(
                "pyprocore.automation.workflows.resolve_project",
                return_value=Project(id=1, name="Project"),
            ),
            patch(
                "pyprocore.automation.workflows.resolve_submittal",
                return_value=Submittal(id=2, number="27"),
            ),
            patch(
                "pyprocore.automation.workflows.get_submittal",
                return_value=Submittal(
                    id=2,
                    number="27",
                    title="Submittal",
                    attachments=[{"url": "https://signed.example/file.pdf"}],
                ),
            ),
            patch("pyprocore.automation.workflows.FileDownloadService", return_value=file_service),
        ):
            build_workflow_package(
                AutomationInput(project_id=1, item_type="submittal", item_number="27")
            )

        destination_dir = file_service.download_attachment.call_args.args[1]
        self.assertEqual(Path(destination_dir).name, "submittal_27")

    def test_convenience_builders_create_expected_inputs(self) -> None:
        """Convenience builders delegate to the generic package builder."""
        expected = Mock(spec=WorkflowPackage)

        with patch(
            "pyprocore.automation.workflows.build_workflow_package",
            return_value=expected,
        ) as builder:
            rfi_package = build_rfi_package(
                company_id=10,
                project_name="Sandbox",
                rfi_id=20,
                number="15",
                download_attachments=False,
                output_dir="downloads",
            )

        self.assertIs(rfi_package, expected)
        rfi_input = builder.call_args.args[0]
        self.assertEqual(rfi_input.item_type, "rfi")
        self.assertEqual(rfi_input.item_id, 20)
        self.assertEqual(rfi_input.item_number, "15")

        with patch(
            "pyprocore.automation.workflows.build_workflow_package",
            return_value=expected,
        ) as builder:
            submittal_package = build_submittal_package(
                project_number="001",
                submittal_id=30,
                number="27",
            )

        self.assertIs(submittal_package, expected)
        submittal_input = builder.call_args.args[0]
        self.assertEqual(submittal_input.item_type, "submittal")
        self.assertEqual(submittal_input.item_id, 30)
        self.assertEqual(submittal_input.item_number, "27")

    def test_package_json_serialization(self) -> None:
        """Automation package models serialize to JSON-friendly dictionaries."""
        package = WorkflowPackage(
            item_type="rfi",
            company_id=None,
            project_id=1,
            project_name="Project",
            item_id=2,
            item_number="15",
            title="Title",
            metadata={"id": 2},
            attachments=[
                DownloadedFile(
                    filename="file.pdf",
                    path=Path("/tmp/file.pdf"),
                    source_url="https://signed.example/file.pdf",
                    content_type="application/pdf",
                )
            ],
            raw={"id": 2},
        )

        dumped = package.model_dump(mode="json")

        self.assertEqual(dumped["attachments"][0]["path"], "/tmp/file.pdf")
        self.assertEqual(dumped["metadata"], {"id": 2})

    def test_root_package_exports_automation_helpers(self) -> None:
        """Package root exposes automation helpers for convenience."""
        self.assertIs(pyprocore.AutomationInput, AutomationInput)
        self.assertIs(pyprocore.WorkflowPackage, WorkflowPackage)
        self.assertIs(pyprocore.DownloadedFile, DownloadedFile)
        self.assertIs(pyprocore.build_workflow_package, build_workflow_package)
        self.assertIs(pyprocore.build_rfi_package, build_rfi_package)
        self.assertIs(pyprocore.build_submittal_package, build_submittal_package)


if __name__ == "__main__":
    unittest.main()
