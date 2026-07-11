"""Unit tests for project context package workflows."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from pyprocore.core.exceptions import ValidationError
from pyprocore.models import (
    RFI,
    DailyLogCount,
    DailyLogEntry,
    DailyLogHeader,
    DailyLogsByType,
    Submittal,
)
from pyprocore.workflows import ProjectContextResult, build_project_context_package


class ProjectContextWorkflowTestCase(unittest.TestCase):
    """Validate AI-ready project context package creation."""

    @patch("pyprocore.workflows.project_context.get_project")
    @patch("pyprocore.workflows.project_context.list_rfis")
    def test_include_rfis_writes_json_jsonl_markdown_and_manifest(
        self,
        list_rfis: Mock,
        get_project: Mock,
    ) -> None:
        """Included sections write expected artifacts and manifest metadata."""
        get_project.return_value = {"id": 352338, "name": "Sandbox"}
        list_rfis.return_value = [RFI(id=10, number="15", subject="Door hardware")]

        with TemporaryDirectory() as temporary_directory:
            result = build_project_context_package(
                352338,
                company_id=123,
                output_dir=temporary_directory,
                include=["project", "rfis"],
            )
            root = Path(temporary_directory)
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))

            self.assertIsInstance(result, ProjectContextResult)
            self.assertTrue((root / "summary.md").exists())
            self.assertTrue((root / "project.json").exists())
            self.assertTrue((root / "rfis" / "rfis.json").exists())
            self.assertTrue((root / "rfis" / "rfis.jsonl").exists())
            self.assertTrue((root / "rfis" / "rfis.md").exists())
            self.assertEqual(manifest["project_id"], 352338)
            self.assertEqual(manifest["company_id"], 123)
            self.assertEqual(manifest["sections_completed"], ["project", "rfis"])
            self.assertEqual(manifest["item_counts"]["rfis"], 1)
            self.assertFalse(manifest["live_downloads_enabled"])

        list_rfis.assert_called_once_with(
            352338,
            updated_after=None,
            updated_before=None,
        )

    @patch("pyprocore.workflows.project_context.list_submittals")
    @patch("pyprocore.workflows.project_context.list_rfis")
    def test_exclude_skips_sections(self, list_rfis: Mock, list_submittals: Mock) -> None:
        """Excluded sections are not attempted."""
        list_rfis.return_value = [RFI(id=1)]
        list_submittals.return_value = [Submittal(id=2)]

        with TemporaryDirectory() as temporary_directory:
            result = build_project_context_package(
                352338,
                output_dir=temporary_directory,
                include=["rfis", "submittals"],
                exclude=["submittals"],
            )

        self.assertEqual(result.manifest.sections_attempted, ["rfis"])
        list_rfis.assert_called_once()
        list_submittals.assert_not_called()

    def test_invalid_section_names_raise_validation_error(self) -> None:
        """Unknown section names fail before writing service calls."""
        with TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(ValidationError, "Unknown project context section"):
                build_project_context_package(
                    352338,
                    output_dir=temporary_directory,
                    include=["weather"],
                )

    @patch("pyprocore.workflows.project_context.list_submittals")
    @patch("pyprocore.workflows.project_context.list_rfis")
    def test_continue_on_error_records_section_error_and_continues(
        self,
        list_rfis: Mock,
        list_submittals: Mock,
    ) -> None:
        """A failed section is recorded when continue_on_error is enabled."""
        list_rfis.side_effect = RuntimeError("no rfi access")
        list_submittals.return_value = [Submittal(id=2, number="27", title="Concrete")]

        with TemporaryDirectory() as temporary_directory:
            result = build_project_context_package(
                352338,
                output_dir=temporary_directory,
                include=["rfis", "submittals"],
            )

        self.assertEqual(result.manifest.sections_failed, ["rfis"])
        self.assertEqual(result.manifest.sections_completed, ["submittals"])
        self.assertTrue(result.errors_path)

    @patch("pyprocore.workflows.project_context.list_rfis")
    def test_fail_fast_raises_section_error(self, list_rfis: Mock) -> None:
        """A failed section raises when continue_on_error is disabled."""
        list_rfis.side_effect = RuntimeError("stop now")

        with TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(RuntimeError, "stop now"):
                build_project_context_package(
                    352338,
                    output_dir=temporary_directory,
                    include=["rfis"],
                    continue_on_error=False,
                )

    @patch("pyprocore.workflows.project_context.download_rfi_attachments")
    @patch("pyprocore.workflows.project_context.list_rfis")
    def test_download_files_false_does_not_call_downloads(
        self,
        list_rfis: Mock,
        download_rfi_attachments: Mock,
    ) -> None:
        """Downloads are off by default."""
        list_rfis.return_value = [RFI(id=10)]

        with TemporaryDirectory() as temporary_directory:
            build_project_context_package(
                352338,
                output_dir=temporary_directory,
                include=["rfis"],
            )

        download_rfi_attachments.assert_not_called()

    @patch("pyprocore.workflows.project_context.download_rfi_attachments")
    @patch("pyprocore.workflows.project_context.list_rfis")
    def test_download_files_true_calls_safe_download_helpers(
        self,
        list_rfis: Mock,
        download_rfi_attachments: Mock,
    ) -> None:
        """Downloads are called only when explicitly requested."""
        list_rfis.return_value = [RFI(id=10)]
        download_rfi_attachments.return_value = [Path("one.pdf")]

        with TemporaryDirectory() as temporary_directory:
            result = build_project_context_package(
                352338,
                output_dir=temporary_directory,
                include=["rfis"],
                download_files=True,
                overwrite=True,
            )

        self.assertTrue(result.manifest.live_downloads_enabled)
        download_rfi_attachments.assert_called_once()
        self.assertTrue(download_rfi_attachments.call_args.kwargs["overwrite"])

    @patch("pyprocore.workflows.project_context.list_submittals")
    def test_max_items_limits_exported_items(self, list_submittals: Mock) -> None:
        """max_items limits section collection output."""
        list_submittals.return_value = [Submittal(id=1), Submittal(id=2)]

        with TemporaryDirectory() as temporary_directory:
            build_project_context_package(
                352338,
                output_dir=temporary_directory,
                include=["submittals"],
                max_items=1,
            )
            data = json.loads(
                (Path(temporary_directory) / "submittals" / "submittals.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(len(data), 1)

    @patch("pyprocore.workflows.project_context.list_daily_logs_for_date")
    @patch("pyprocore.workflows.project_context.list_daily_log_headers")
    @patch("pyprocore.workflows.project_context.get_daily_log_counts")
    def test_daily_logs_section_writes_counts_headers_and_logs(
        self,
        get_daily_log_counts: Mock,
        list_daily_log_headers: Mock,
        list_daily_logs_for_date: Mock,
    ) -> None:
        """Daily Logs section writes all requested files."""
        get_daily_log_counts.return_value = [DailyLogCount(log_type="manpower", count=1)]
        list_daily_log_headers.return_value = [DailyLogHeader(id=1, log_date="2026-07-10")]
        list_daily_logs_for_date.return_value = DailyLogsByType(
            project_id=352338,
            log_date="2026-07-10",
            logs={"manpower": [DailyLogEntry(id=5)]},
        )

        with TemporaryDirectory() as temporary_directory:
            result = build_project_context_package(
                352338,
                output_dir=temporary_directory,
                include=["daily_logs"],
                log_date="2026-07-10",
            )
            root = Path(temporary_directory) / "daily-logs"

            self.assertEqual(result.manifest.item_counts["daily_logs"], 3)
            self.assertTrue((root / "counts.json").exists())
            self.assertTrue((root / "headers.json").exists())
            self.assertTrue((root / "logs.json").exists())
            self.assertTrue((root / "daily_logs.md").exists())

    @patch("pyprocore.workflows.project_context.list_photo_albums")
    @patch("pyprocore.workflows.project_context.list_photos")
    @patch("pyprocore.workflows.project_context.list_specification_section_revisions")
    @patch("pyprocore.workflows.project_context.list_specification_sections")
    @patch("pyprocore.workflows.project_context.list_specification_sets")
    @patch("pyprocore.workflows.project_context.list_drawings")
    @patch("pyprocore.workflows.project_context.list_drawing_areas")
    @patch("pyprocore.workflows.project_context.list_documents")
    @patch("pyprocore.workflows.project_context.list_document_folders")
    def test_project_resource_sections_write_stubbed_outputs(
        self,
        list_document_folders: Mock,
        list_documents: Mock,
        list_drawing_areas: Mock,
        list_drawings: Mock,
        list_specification_sets: Mock,
        list_specification_sections: Mock,
        list_specification_section_revisions: Mock,
        list_photo_albums: Mock,
        list_photos: Mock,
    ) -> None:
        """Documents, Drawings, Specifications, and Photos sections use mocked services."""
        list_document_folders.return_value = [{"id": 1, "name": "Root"}]
        list_documents.return_value = [{"id": 2, "name": "Plan"}]
        list_drawing_areas.return_value = [{"id": 3, "name": "Current"}]
        list_drawings.return_value = [{"id": 4, "title": "A-101"}]
        list_specification_sets.return_value = [{"id": 5, "name": "Set"}]
        list_specification_sections.return_value = [{"id": 6, "title": "Concrete"}]
        list_specification_section_revisions.return_value = [{"id": 7}]
        list_photo_albums.return_value = [{"id": 8, "name": "Progress"}]
        list_photos.return_value = [{"id": 9, "filename": "site.jpg"}]

        with TemporaryDirectory() as temporary_directory:
            result = build_project_context_package(
                352338,
                company_id=123,
                output_dir=temporary_directory,
                include=["documents", "drawings", "specifications", "photos"],
            )
            root = Path(temporary_directory)

            self.assertTrue((root / "documents" / "documents.json").exists())
            self.assertTrue((root / "drawings" / "drawings.json").exists())
            self.assertTrue((root / "specifications" / "specification_sections.json").exists())
            self.assertTrue((root / "photos" / "photos.json").exists())

        self.assertEqual(
            result.manifest.sections_completed,
            [
                "documents",
                "drawings",
                "specifications",
                "photos",
            ],
        )


if __name__ == "__main__":
    unittest.main()
