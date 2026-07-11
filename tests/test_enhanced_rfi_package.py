"""Unit tests for enhanced RFI package workflows."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from pyprocore.core.exceptions import ValidationError
from pyprocore.models import RFI, RFIQuestion, Submittal
from pyprocore.workflows import EnhancedRFIPackageResult, build_enhanced_rfi_package


class EnhancedRFIPackageTestCase(unittest.TestCase):
    """Validate enhanced AI-ready RFI package creation."""

    @patch("pyprocore.workflows.enhanced_rfi.get_rfi")
    def test_rfi_lookup_by_id_writes_core_and_ai_files(self, get_rfi: Mock) -> None:
        """RFI ID lookup writes primary package artifacts."""
        get_rfi.return_value = RFI(
            id=10,
            number="15",
            subject="Door hardware",
            questions=[RFIQuestion(plain_text_body="Which hardware set should be used?")],
        )

        with TemporaryDirectory() as temporary_directory:
            result = build_enhanced_rfi_package(
                352338,
                rfi_id=10,
                output_dir=temporary_directory,
                include_related=False,
            )
            root = Path(temporary_directory)

            self.assertIsInstance(result, EnhancedRFIPackageResult)
            self.assertTrue((root / "manifest.json").exists())
            self.assertTrue((root / "summary.md").exists())
            self.assertTrue((root / "rfi.json").exists())
            self.assertTrue((root / "rfi.md").exists())
            self.assertTrue((root / "ai" / "review_context.md").exists())
            self.assertTrue((root / "ai" / "review_context.json").exists())
            self.assertTrue((root / "ai" / "questions_to_answer.md").exists())
            self.assertTrue((root / "ai" / "risk_flags.md").exists())

        get_rfi.assert_called_once_with(352338, 10)

    @patch("pyprocore.workflows.enhanced_rfi.find_rfi")
    def test_rfi_lookup_by_number(self, find_rfi: Mock) -> None:
        """RFI number lookup uses the resolver."""
        find_rfi.return_value = RFI(id=10, number="15", subject="Door hardware")

        with TemporaryDirectory() as temporary_directory:
            result = build_enhanced_rfi_package(
                352338,
                rfi_number="15",
                output_dir=temporary_directory,
                include_related=False,
            )

        self.assertEqual(result.rfi_number, "15")
        find_rfi.assert_called_once_with(352338, number="15")

    def test_invalid_inputs_raise_validation_error(self) -> None:
        """Missing RFI identifiers and unknown related sections fail clearly."""
        with TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(ValidationError, "Provide rfi_id or rfi_number"):
                build_enhanced_rfi_package(352338, output_dir=temporary_directory)
            with self.assertRaisesRegex(ValidationError, "Unknown related section"):
                build_enhanced_rfi_package(
                    352338,
                    rfi_id=10,
                    output_dir=temporary_directory,
                    related_sections=["weather"],
                )

    @patch("pyprocore.workflows.enhanced_rfi.list_submittals")
    @patch("pyprocore.workflows.enhanced_rfi.get_rfi")
    def test_keyword_matching_and_max_related_items(
        self,
        get_rfi: Mock,
        list_submittals: Mock,
    ) -> None:
        """Related items are matched with simple keyword scoring and limited."""
        get_rfi.return_value = RFI(id=10, number="15", subject="Door hardware")
        list_submittals.return_value = [
            Submittal(id=1, number="1", title="Door hardware set"),
            Submittal(id=2, number="2", title="Unrelated concrete mix"),
        ]

        with TemporaryDirectory() as temporary_directory:
            build_enhanced_rfi_package(
                352338,
                rfi_id=10,
                output_dir=temporary_directory,
                related_sections=["submittals"],
                max_related_items=1,
            )
            related = json.loads(
                (Path(temporary_directory) / "related" / "submittals.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(len(related), 1)
        self.assertEqual(related[0]["title"], "Door hardware set")

    @patch("pyprocore.workflows.enhanced_rfi.list_submittals")
    @patch("pyprocore.workflows.enhanced_rfi.list_documents")
    @patch("pyprocore.workflows.enhanced_rfi.get_rfi")
    def test_related_include_and_exclude(
        self,
        get_rfi: Mock,
        list_documents: Mock,
        list_submittals: Mock,
    ) -> None:
        """include/exclude controls related section attempts."""
        get_rfi.return_value = RFI(id=10, number="15", subject="Door hardware")
        list_documents.return_value = [{"id": 1, "name": "Door hardware plan"}]
        list_submittals.return_value = [Submittal(id=2, title="Door hardware")]

        with TemporaryDirectory() as temporary_directory:
            result = build_enhanced_rfi_package(
                352338,
                rfi_id=10,
                output_dir=temporary_directory,
                related_sections=["documents", "submittals"],
                exclude_related=["submittals"],
            )

        self.assertEqual(result.manifest.sections_attempted, ["documents"])
        list_documents.assert_called_once()
        list_submittals.assert_not_called()

    @patch("pyprocore.workflows.enhanced_rfi.list_daily_logs_for_date")
    @patch("pyprocore.workflows.enhanced_rfi.list_daily_log_headers")
    @patch("pyprocore.workflows.enhanced_rfi.get_daily_log_counts")
    @patch("pyprocore.workflows.enhanced_rfi.list_photos")
    @patch("pyprocore.workflows.enhanced_rfi.list_photo_albums")
    @patch("pyprocore.workflows.enhanced_rfi.list_specification_sections")
    @patch("pyprocore.workflows.enhanced_rfi.list_drawings")
    @patch("pyprocore.workflows.enhanced_rfi.list_drawing_areas")
    @patch("pyprocore.workflows.enhanced_rfi.list_documents")
    @patch("pyprocore.workflows.enhanced_rfi.get_rfi")
    def test_related_project_context_sections_are_written(
        self,
        get_rfi: Mock,
        list_documents: Mock,
        list_drawing_areas: Mock,
        list_drawings: Mock,
        list_specification_sections: Mock,
        list_photo_albums: Mock,
        list_photos: Mock,
        get_daily_log_counts: Mock,
        list_daily_log_headers: Mock,
        list_daily_logs_for_date: Mock,
    ) -> None:
        """Related project tools are fetched, matched, and written safely."""
        get_rfi.return_value = RFI(
            id=10,
            number="15",
            subject="Door hardware",
            status="open",
            due_date="2020-01-01",
            questions=[RFIQuestion(plain_text_body="Door hardware needs review.")],
        )
        list_documents.return_value = [{"id": 1, "name": "Door hardware.pdf"}]
        list_drawing_areas.return_value = [{"id": 7, "name": "Architectural"}]
        list_drawings.return_value = [{"id": 8, "number": "A-101", "title": "Door hardware"}]
        list_specification_sections.return_value = [
            {"id": 9, "number": "08 7100", "title": "Door Hardware"}
        ]
        list_photo_albums.return_value = [{"id": 11, "name": "Punch"}]
        list_photos.return_value = [{"id": 12, "filename": "door-hardware.jpg"}]
        get_daily_log_counts.return_value = [
            {"log_type": "notes", "name": "Door hardware", "count": 1}
        ]
        list_daily_log_headers.return_value = [{"id": 13, "log_date": "2020-01-01"}]
        list_daily_logs_for_date.return_value = Mock(
            logs={"notes": [{"id": 14, "comments": "Door hardware discussion"}]}
        )

        with TemporaryDirectory() as temporary_directory:
            result = build_enhanced_rfi_package(
                352338,
                rfi_id=10,
                company_id=123,
                output_dir=temporary_directory,
                related_sections=[
                    "documents",
                    "drawings",
                    "specifications",
                    "photos",
                    "daily_logs",
                ],
                log_date="2020-01-01",
            )
            root = Path(temporary_directory)
            risk_flags = (root / "ai" / "risk_flags.md").read_text(encoding="utf-8")

            self.assertTrue((root / "related" / "documents.md").exists())
            self.assertTrue((root / "related" / "drawings.json").exists())
            self.assertTrue((root / "related" / "specifications.json").exists())
            self.assertTrue((root / "related" / "photos.json").exists())
            self.assertTrue((root / "related" / "daily_logs.json").exists())
            self.assertEqual(result.manifest.sections_failed, [])
            self.assertEqual(result.manifest.related_item_counts["drawings"], 1)
            self.assertIn("Possible overdue RFI", risk_flags)
            self.assertIn("No official answer", risk_flags)

        list_drawings.assert_called_once_with(
            352338,
            company_id=123,
            drawing_area_id=7,
        )
        list_photos.assert_called_once_with(352338, company_id=123, album_id=11)
        list_daily_logs_for_date.assert_called_once_with(
            352338,
            company_id=123,
            log_date="2020-01-01",
        )

    @patch("pyprocore.workflows.enhanced_rfi.download_rfi_attachments")
    @patch("pyprocore.workflows.enhanced_rfi.get_rfi")
    def test_download_files_false_does_not_download(
        self,
        get_rfi: Mock,
        download_rfi_attachments: Mock,
    ) -> None:
        """RFI attachment downloads are off by default."""
        get_rfi.return_value = RFI(id=10, number="15")

        with TemporaryDirectory() as temporary_directory:
            build_enhanced_rfi_package(
                352338,
                rfi_id=10,
                output_dir=temporary_directory,
                include_related=False,
            )

        download_rfi_attachments.assert_not_called()

    @patch("pyprocore.workflows.enhanced_rfi.download_rfi_attachments")
    @patch("pyprocore.workflows.enhanced_rfi.get_rfi")
    def test_download_files_true_downloads(
        self,
        get_rfi: Mock,
        download_rfi_attachments: Mock,
    ) -> None:
        """RFI attachment downloads run only when requested."""
        get_rfi.return_value = RFI(id=10, number="15")
        download_rfi_attachments.return_value = [Path("one.pdf")]

        with TemporaryDirectory() as temporary_directory:
            result = build_enhanced_rfi_package(
                352338,
                rfi_id=10,
                output_dir=temporary_directory,
                include_related=False,
                download_files=True,
                overwrite=True,
            )

        self.assertTrue(result.manifest.downloads_enabled)
        download_rfi_attachments.assert_called_once()
        self.assertTrue(download_rfi_attachments.call_args.kwargs["overwrite"])

    @patch("pyprocore.workflows.enhanced_rfi.list_submittals")
    @patch("pyprocore.workflows.enhanced_rfi.get_rfi")
    def test_continue_on_error_records_related_error(
        self,
        get_rfi: Mock,
        list_submittals: Mock,
    ) -> None:
        """Related section errors are recorded when continue_on_error is true."""
        get_rfi.return_value = RFI(id=10, number="15", subject="Door hardware")
        list_submittals.side_effect = RuntimeError("no submittal access")

        with TemporaryDirectory() as temporary_directory:
            result = build_enhanced_rfi_package(
                352338,
                rfi_id=10,
                output_dir=temporary_directory,
                related_sections=["submittals"],
            )

        self.assertEqual(result.manifest.sections_failed, ["submittals"])
        self.assertTrue(result.errors_path)

    @patch("pyprocore.workflows.enhanced_rfi.list_submittals")
    @patch("pyprocore.workflows.enhanced_rfi.get_rfi")
    def test_fail_fast_raises_related_error(
        self,
        get_rfi: Mock,
        list_submittals: Mock,
    ) -> None:
        """Related section errors raise when continue_on_error is false."""
        get_rfi.return_value = RFI(id=10, number="15", subject="Door hardware")
        list_submittals.side_effect = RuntimeError("stop")

        with TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(RuntimeError, "stop"):
                build_enhanced_rfi_package(
                    352338,
                    rfi_id=10,
                    output_dir=temporary_directory,
                    related_sections=["submittals"],
                    continue_on_error=False,
                )


if __name__ == "__main__":
    unittest.main()
