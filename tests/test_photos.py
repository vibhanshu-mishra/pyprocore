"""Unit tests for Procore photo services."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pyprocore.core.exceptions import MultipleResultsError, NotFoundError, ValidationError
from pyprocore.models import PhotoImage
from pyprocore.services.photos import (
    PhotosService,
    download_photo,
    download_photo_album,
    find_photo,
    find_photo_album,
    get_photo,
    get_photo_album,
    list_photo_albums,
    list_photos,
)


class PhotosServiceTestCase(unittest.TestCase):
    """Validate photo services without live Procore access."""

    def test_list_photo_albums_uses_project_query_and_company_header(self) -> None:
        """Photo albums use image_categories with project_id query params."""
        client = Mock()
        client.get_all.return_value = [{"id": 1, "name": "Site Progress"}]

        result = PhotosService(client=client).list_photo_albums(
            456,
            company_id=123,
            page=2,
            per_page=50,
        )

        self.assertEqual(result[0].name, "Site Progress")
        client.get_all.assert_called_once_with(
            "/rest/v1.0/image_categories",
            params={"project_id": 456, "page": 2, "per_page": 50},
            headers={"Procore-Company-Id": "123"},
        )

    @patch("pyprocore.services.photos.get_settings")
    def test_company_id_defaults_to_settings(self, get_settings: Mock) -> None:
        """Photo services default to PROCORE_COMPANY_ID when omitted."""
        get_settings.return_value.company_id = 321
        client = Mock()
        client.get_all.return_value = [{"id": 1, "name": "Album"}]

        PhotosService(client=client).list_photo_albums(456)

        client.get_all.assert_called_once_with(
            "/rest/v1.0/image_categories",
            params={"project_id": 456},
            headers={"Procore-Company-Id": "321"},
        )

    def test_get_photo_album_uses_show_endpoint(self) -> None:
        """Photo album retrieval sends project_id as a query parameter."""
        client = Mock()
        client.get.return_value = {"id": 1, "name": "Punch"}

        result = PhotosService(client=client).get_photo_album(456, 1, company_id=123)

        self.assertEqual(result.id, 1)
        client.get.assert_called_once_with(
            "/rest/v1.0/image_categories/1",
            params={"project_id": 456},
            headers={"Procore-Company-Id": "123"},
        )

    def test_find_photo_album_matches_name(self) -> None:
        """Album lookup supports exact and partial matching."""
        client = Mock()
        client.get_all.return_value = [
            {"id": 1, "name": "Site Progress"},
            {"id": 2, "name": "Punch Photos"},
        ]
        service = PhotosService(client=client)

        self.assertEqual(service.find_photo_album(456, name="site progress", company_id=123).id, 1)
        self.assertEqual(service.find_photo_album(456, name="Punch", company_id=123).id, 2)

    def test_find_photo_album_raises_for_missing_or_duplicate(self) -> None:
        """Album lookup raises clear resolver errors."""
        client = Mock()
        client.get_all.return_value = [
            {"id": 1, "name": "Progress"},
            {"id": 2, "name": "Progress"},
        ]
        service = PhotosService(client=client)

        with self.assertRaises(MultipleResultsError):
            service.find_photo_album(456, name="Progress", company_id=123)
        client.get_all.return_value = []
        with self.assertRaises(NotFoundError):
            service.find_photo_album(456, name="Progress", company_id=123)
        with self.assertRaises(ValidationError):
            service.find_photo_album(456, name="", company_id=123)

    def test_list_photos_maps_album_and_filters(self) -> None:
        """Photo listing maps Python-friendly filters to Procore keys."""
        client = Mock()
        client.get_all.return_value = [{"id": 9, "filename": "site.jpg"}]

        result = PhotosService(client=client).list_photos(
            456,
            company_id=123,
            album_id=1,
            private=False,
            starred=True,
            created_at="2026-07-01",
            updated_at="2026-07-02",
            log_date="2026-07-03",
            query="site",
            uploader_ids=[7],
            location_ids=[8],
            trade_ids=[9],
            image_ids=[10],
            projection="full",
            serializer_view="normal",
            sort="-created_at",
            page=1,
            per_page=100,
        )

        self.assertEqual(result[0].filename, "site.jpg")
        client.get_all.assert_called_once_with(
            "/rest/v1.0/images",
            params={
                "project_id": 456,
                "image_category_id": 1,
                "serializer_view": "normal",
                "sort": "-created_at",
                "page": 1,
                "per_page": 100,
                "filters[private]": False,
                "filters[starred]": True,
                "filters[created_at]": "2026-07-01",
                "filters[updated_at]": "2026-07-02",
                "filters[log_date]": "2026-07-03",
                "filters[query]": "site",
                "filters[uploader_id][]": [7],
                "filters[location_id][]": [8],
                "filters[trade_ids][]": [9],
                "filters[id][]": [10],
                "filters[projection]": "full",
            },
            headers={"Procore-Company-Id": "123"},
        )

    def test_get_photo_returns_typed_model(self) -> None:
        """Photo retrieval uses /images/{id} with project query params."""
        client = Mock()
        client.get.return_value = {"data": {"id": 9, "filename": "site.jpg"}}

        result = PhotosService(client=client).get_photo(456, 9, company_id=123)

        self.assertEqual(result.filename, "site.jpg")
        client.get.assert_called_once_with(
            "/rest/v1.0/images/9",
            params={"project_id": 456},
            headers={"Procore-Company-Id": "123"},
        )

    def test_find_photo_supports_id_and_text(self) -> None:
        """Photo lookup can use direct ID or text matching."""
        client = Mock()
        client.get.return_value = {"id": 9, "filename": "site.jpg"}
        service = PhotosService(client=client)

        self.assertEqual(service.find_photo(456, photo_id=9, company_id=123).id, 9)

        client.get_all.return_value = [
            {"id": 10, "filename": "roof.jpg", "description": "Roof progress"},
            {"id": 11, "filename": "site.jpg", "description": "Site"},
        ]
        self.assertEqual(service.find_photo(456, filename="roof", company_id=123).id, 10)

    def test_find_photo_raises_for_ambiguous_or_missing_criteria(self) -> None:
        """Photo lookup raises clear errors."""
        client = Mock()
        client.get_all.return_value = [
            {"id": 10, "filename": "site.jpg"},
            {"id": 11, "filename": "site.jpg"},
        ]
        service = PhotosService(client=client)

        with self.assertRaises(MultipleResultsError):
            service.find_photo(456, filename="site.jpg", company_id=123)
        with self.assertRaises(ValidationError):
            service.find_photo(456, company_id=123)

    def test_download_photo_uses_full_size_url_and_safe_filename(self) -> None:
        """Photo downloads use URL fields and sanitize filenames."""
        client = Mock()
        client.get.return_value = {
            "id": 9,
            "filename": "site?.jpg",
            "links": {"download": "https://signed.example/site.jpg"},
        }
        file_service = Mock()
        file_service.download_url.return_value = Path("photos/site_.jpg")

        result = PhotosService(client=client, file_service=file_service).download_photo(
            456,
            9,
            output_dir="photos",
            company_id=123,
            overwrite=True,
        )

        self.assertEqual(result, Path("photos/site_.jpg"))
        file_service.download_url.assert_called_once_with(
            "https://signed.example/site.jpg",
            Path("photos") / "site_.jpg",
            overwrite=True,
        )

    def test_download_photo_requires_url(self) -> None:
        """Photos without a full-size URL fail before download."""
        client = Mock()
        client.get.return_value = {"id": 9, "filename": "site.jpg"}
        file_service = Mock()

        with self.assertRaisesRegex(ValidationError, "No downloadable photo URL"):
            PhotosService(client=client, file_service=file_service).download_photo(
                456,
                9,
                company_id=123,
            )

        file_service.download_url.assert_not_called()

    def test_download_photo_album_records_partial_failures(self) -> None:
        """Album downloads continue when one photo cannot be downloaded."""
        file_service = Mock()
        file_service.download_url.return_value = Path("photos/one.jpg")
        service = PhotosService(client=Mock(), file_service=file_service)
        with patch.object(
            service,
            "list_photos",
            return_value=[
                PhotoImage(
                    id=1,
                    download_url="https://signed.example/one.jpg",
                    filename="one.jpg",
                ),
                PhotoImage(id=2, filename="two.jpg"),
            ],
        ):
            result = service.download_photo_album(456, 7, company_id=123, limit=2)

        self.assertEqual(result.album_id, 7)
        self.assertEqual(result.requested, 2)
        self.assertEqual(result.downloaded_files, ["photos/one.jpg"])
        self.assertEqual(len(result.errors), 1)

    def test_module_level_helpers_delegate_to_service(self) -> None:
        """Module-level helpers preserve the existing service style."""
        with patch("pyprocore.services.photos.PhotosService") as service_cls:
            service = service_cls.return_value
            service.list_photo_albums.return_value = ["album"]
            service.get_photo_album.return_value = "album"
            service.find_photo_album.return_value = "album"
            service.list_photos.return_value = ["photo"]
            service.get_photo.return_value = "photo"
            service.find_photo.return_value = "photo"
            service.download_photo.return_value = Path("photo.jpg")
            service.download_photo_album.return_value = "summary"

            self.assertEqual(list_photo_albums(456), ["album"])
            self.assertEqual(get_photo_album(456, 1), "album")
            self.assertEqual(find_photo_album(456, name="Site"), "album")
            self.assertEqual(list_photos(456, album_id=1), ["photo"])
            self.assertEqual(get_photo(456, 9), "photo")
            self.assertEqual(find_photo(456, filename="site.jpg"), "photo")
            self.assertEqual(download_photo(456, 9), Path("photo.jpg"))
            self.assertEqual(download_photo_album(456, 1), "summary")


if __name__ == "__main__":
    unittest.main()
