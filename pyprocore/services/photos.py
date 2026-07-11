"""Photo services for the Procore SDK."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.config import get_settings
from pyprocore.core.exceptions import MultipleResultsError, NotFoundError, ValidationError
from pyprocore.models import PhotoAlbum, PhotoAlbumDownloadResult, PhotoImage
from pyprocore.services.files import FileDownloadService, sanitize_filename
from pyprocore.services.query_params import build_query_params

DEFAULT_DOWNLOAD_DIR = Path(__file__).resolve().parents[1] / "downloads" / "photos"


class PhotosService:
    """Service for Procore Photos resources.

    Procore's REST API names photo albums ``image_categories`` and photos
    ``images``. Public SDK methods use album/photo terminology.
    """

    def __init__(
        self,
        client: ProcoreClient | None = None,
        file_service: FileDownloadService | None = None,
    ) -> None:
        """Initialize the service.

        Args:
            client: Optional shared Procore HTTP client.
            file_service: Optional shared file download service.
        """
        self._client = client or ProcoreClient()
        self._file_service = file_service

    def list_photo_albums(
        self,
        project_id: int,
        company_id: int | None = None,
        page: int | None = None,
        per_page: int | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[PhotoAlbum]:
        """Return photo albums/image categories for a project."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_optional_id(page, "page")
        self._validate_optional_id(per_page, "per_page")
        response = self._client.get_all(
            endpoints.image_categories(),
            params=build_query_params(
                params=params,
                extra_params=extra_params,
                project_id=project_id,
                page=page,
                per_page=per_page,
            ),
            headers=self._company_headers(resolved_company_id),
        )
        return [PhotoAlbum.model_validate(item) for item in self._extract_items(response)]

    def get_photo_album(
        self,
        project_id: int,
        album_id: int,
        company_id: int | None = None,
    ) -> PhotoAlbum:
        """Return one photo album/image category."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(album_id, "album_id")
        response = self._client.get(
            endpoints.image_category(album_id),
            params={"project_id": project_id},
            headers=self._company_headers(resolved_company_id),
        )
        return PhotoAlbum.model_validate(self._extract_item(response, "photo album"))

    def find_photo_album(
        self,
        project_id: int,
        name: str | None = None,
        company_id: int | None = None,
    ) -> PhotoAlbum:
        """Find one photo album by name or name fragment."""
        if name is None or not name.strip():
            raise ValidationError("Provide name to find a photo album.")
        albums = self.list_photo_albums(project_id, company_id=company_id)
        needle = name.strip().casefold()
        exact = [album for album in albums if (album.name or "").casefold() == needle]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            raise MultipleResultsError("Multiple photo albums matched exactly.")
        partial = [album for album in albums if needle in (album.name or "").casefold()]
        if len(partial) == 1:
            return partial[0]
        if len(partial) > 1:
            raise MultipleResultsError("Multiple photo albums matched the search text.")
        raise NotFoundError(f"No photo album matched {name!r}.")

    def list_photos(
        self,
        project_id: int,
        company_id: int | None = None,
        album_id: int | None = None,
        image_category_id: int | None = None,
        private: bool | None = None,
        starred: bool | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        log_date: str | None = None,
        query: str | None = None,
        uploader_ids: Iterable[int] | None = None,
        location_ids: Iterable[int] | None = None,
        trade_ids: Iterable[int] | None = None,
        image_ids: Iterable[int] | None = None,
        projection: str | None = None,
        serializer_view: str | None = None,
        sort: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[PhotoImage]:
        """Return photos/images for a project or album."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        category_id = image_category_id if image_category_id is not None else album_id
        self._validate_optional_id(category_id, "image_category_id")
        self._validate_optional_id(page, "page")
        self._validate_optional_id(per_page, "per_page")
        response = self._client.get_all(
            endpoints.images(),
            params=build_query_params(
                params=params,
                extra_params=extra_params,
                project_id=project_id,
                image_category_id=category_id,
                serializer_view=serializer_view,
                sort=sort,
                page=page,
                per_page=per_page,
                **self._photo_filters(
                    private=private,
                    starred=starred,
                    created_at=created_at,
                    updated_at=updated_at,
                    log_date=log_date,
                    query=query,
                    uploader_ids=uploader_ids,
                    location_ids=location_ids,
                    trade_ids=trade_ids,
                    image_ids=image_ids,
                    projection=projection,
                ),
            ),
            headers=self._company_headers(resolved_company_id),
        )
        return [PhotoImage.model_validate(item) for item in self._extract_items(response)]

    def get_photo(
        self,
        project_id: int,
        photo_id: int,
        company_id: int | None = None,
    ) -> PhotoImage:
        """Return one photo/image."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(photo_id, "photo_id")
        response = self._client.get(
            endpoints.image(photo_id),
            params={"project_id": project_id},
            headers=self._company_headers(resolved_company_id),
        )
        return PhotoImage.model_validate(self._extract_item(response, "photo"))

    def find_photo(
        self,
        project_id: int,
        photo_id: int | None = None,
        filename: str | None = None,
        description: str | None = None,
        query: str | None = None,
        company_id: int | None = None,
    ) -> PhotoImage:
        """Find one photo by ID, filename, description, or search text."""
        if photo_id is not None:
            return self.get_photo(project_id, photo_id, company_id=company_id)
        fields = self._search_fields(filename=filename, description=description, query=query)
        if not fields:
            raise ValidationError("Provide photo_id, filename, description, or query.")
        photos = self.list_photos(project_id, company_id=company_id, query=query)
        exact = [photo for photo in photos if self._photo_matches(photo, fields, exact=True)]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            raise MultipleResultsError("Multiple photos matched exactly.")
        partial = [photo for photo in photos if self._photo_matches(photo, fields, exact=False)]
        if len(partial) == 1:
            return partial[0]
        if len(partial) > 1:
            raise MultipleResultsError("Multiple photos matched the search text.")
        raise NotFoundError("No photo matched the provided search criteria.")

    def download_photo(
        self,
        project_id: int,
        photo_id: int,
        output_dir: Path | str = DEFAULT_DOWNLOAD_DIR,
        company_id: int | None = None,
        *,
        overwrite: bool = False,
        filename: str | None = None,
    ) -> Path:
        """Download one photo using URL fields from the image payload."""
        photo = self.get_photo(project_id, photo_id, company_id=company_id)
        url = self._photo_download_url(photo)
        if url is None:
            raise ValidationError(
                "No downloadable photo URL was found in the Procore image payload."
            )
        destination = Path(output_dir) / self._photo_filename(photo, filename)
        return self._download_service.download_url(url, destination, overwrite=overwrite)

    def download_photo_album(
        self,
        project_id: int,
        album_id: int,
        output_dir: Path | str = DEFAULT_DOWNLOAD_DIR,
        company_id: int | None = None,
        *,
        overwrite: bool = False,
        limit: int | None = None,
    ) -> PhotoAlbumDownloadResult:
        """Download photos from one album and return a summary."""
        self._validate_positive_id(album_id, "album_id")
        self._validate_optional_id(limit, "limit")
        photos = self.list_photos(project_id, company_id=company_id, album_id=album_id)
        selected = photos[:limit] if limit is not None else photos
        result = PhotoAlbumDownloadResult(album_id=album_id, requested=len(selected))
        for photo in selected:
            if photo.id is None:
                result.errors.append("Photo without an ID was skipped.")
                continue
            try:
                url = self._photo_download_url(photo)
                if url is None:
                    raise ValidationError(
                        "No downloadable photo URL was found in the Procore image payload."
                    )
                destination = Path(output_dir) / self._photo_filename(photo, None)
                existed_before = destination.exists()
                saved_path = self._download_service.download_url(
                    url,
                    destination,
                    overwrite=overwrite,
                )
            except Exception as exc:
                result.errors.append(f"Photo {photo.id}: {exc}")
                continue
            if existed_before and not overwrite:
                result.skipped.append(str(saved_path))
            else:
                result.downloaded_files.append(str(saved_path))
        return result

    @property
    def _download_service(self) -> FileDownloadService:
        """Return a file service, creating it only when downloads are requested."""
        if self._file_service is None:
            self._file_service = FileDownloadService()
        return self._file_service

    @staticmethod
    def _resolve_company_id(company_id: int | None) -> int:
        """Return an explicit or configured company ID."""
        resolved_company_id = company_id or get_settings().company_id
        PhotosService._validate_positive_id(resolved_company_id, "company_id")
        return resolved_company_id

    @staticmethod
    def _company_headers(company_id: int) -> dict[str, str]:
        """Return required Procore company headers for Photos endpoints."""
        return {"Procore-Company-Id": str(company_id)}

    @classmethod
    def _extract_items(cls, payload: object) -> list[Mapping[str, Any]]:
        """Extract collection items from direct or envelope responses."""
        if isinstance(payload, list):
            items: list[Mapping[str, Any]] = []
            for item in payload:
                if isinstance(item, Mapping):
                    data = item.get("data")
                    if isinstance(data, list):
                        items.extend(cls._ensure_mapping(value) for value in data)
                    else:
                        items.append(item)
                    continue
                raise ValidationError("Expected Procore Photos item to be an object.")
            return items
        if isinstance(payload, Mapping):
            for key in ("data", "items", "results"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [cls._ensure_mapping(item) for item in value]
            return [payload]
        raise ValidationError("Expected Procore Photos response to be a list or object.")

    @staticmethod
    def _extract_item(payload: object, resource_name: str) -> Mapping[str, Any]:
        """Extract one object from a direct or envelope response."""
        if isinstance(payload, Mapping):
            data = payload.get("data")
            if isinstance(data, Mapping):
                return data
            return payload
        raise ValidationError(f"Expected Procore {resource_name} response to be an object.")

    @staticmethod
    def _ensure_mapping(item: object) -> Mapping[str, Any]:
        """Validate that a payload item is a mapping."""
        if not isinstance(item, Mapping):
            raise ValidationError("Expected Procore Photos item to be an object.")
        return item

    @staticmethod
    def _photo_filters(
        *,
        private: bool | None,
        starred: bool | None,
        created_at: str | None,
        updated_at: str | None,
        log_date: str | None,
        query: str | None,
        uploader_ids: Iterable[int] | None,
        location_ids: Iterable[int] | None,
        trade_ids: Iterable[int] | None,
        image_ids: Iterable[int] | None,
        projection: str | None,
    ) -> dict[str, Any]:
        """Map Python-friendly filters to Procore Photos query keys."""
        return {
            "filters[private]": private,
            "filters[starred]": starred,
            "filters[created_at]": created_at,
            "filters[updated_at]": updated_at,
            "filters[log_date]": log_date,
            "filters[query]": query,
            "filters[uploader_id][]": list(uploader_ids) if uploader_ids is not None else None,
            "filters[location_id][]": list(location_ids) if location_ids is not None else None,
            "filters[trade_ids][]": list(trade_ids) if trade_ids is not None else None,
            "filters[id][]": list(image_ids) if image_ids is not None else None,
            "filters[projection]": projection,
        }

    @staticmethod
    def _search_fields(
        *,
        filename: str | None,
        description: str | None,
        query: str | None,
    ) -> dict[str, str]:
        """Build normalized photo search fields."""
        fields: dict[str, str] = {}
        if filename is not None and filename.strip():
            fields["filename"] = filename.strip().casefold()
        if description is not None and description.strip():
            fields["description"] = description.strip().casefold()
        if query is not None and query.strip():
            fields["query"] = query.strip().casefold()
        return fields

    @staticmethod
    def _photo_matches(photo: PhotoImage, fields: Mapping[str, str], *, exact: bool) -> bool:
        """Return whether a photo matches all requested fields."""
        for field, needle in fields.items():
            if field == "query":
                haystacks = (
                    photo.filename,
                    photo.file_name,
                    photo.image_name,
                    photo.original_filename,
                    photo.name,
                    photo.description,
                )
                normalized = [str(value or "").casefold() for value in haystacks]
                if exact and needle not in normalized:
                    return False
                if not exact and not any(needle in value for value in normalized):
                    return False
                continue
            values = [getattr(photo, field), photo.file_name, photo.original_filename]
            normalized_values = [str(value or "").casefold() for value in values]
            if exact and needle not in normalized_values:
                return False
            if not exact and not any(needle in value for value in normalized_values):
                return False
        return True

    @classmethod
    def _photo_download_url(cls, photo: PhotoImage) -> str | None:
        """Return the best available full-size photo URL."""
        payload = photo.model_dump(mode="python")
        for key in ("url", "download_url", "file_url", "original_url", "full_size_url"):
            url = cls._string_value(payload.get(key))
            if url:
                return url
        links = payload.get("links")
        if isinstance(links, Mapping):
            for key in ("download", "retrieve"):
                url = cls._string_value(links.get(key))
                if url:
                    return url
        images = payload.get("images")
        if isinstance(images, Mapping):
            original = images.get("original")
            if isinstance(original, Mapping):
                url = cls._string_value(original.get("url"))
                if url:
                    return url
        return cls._string_value(payload.get("thumbnail_url"))

    @staticmethod
    def _string_value(value: object) -> str | None:
        """Return a non-empty string value."""
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def _photo_filename(photo: PhotoImage, filename: str | None) -> str:
        """Return a safe local filename for a photo."""
        for candidate in (
            filename,
            photo.filename,
            photo.file_name,
            photo.image_name,
            photo.original_filename,
            photo.name,
        ):
            if candidate is not None and str(candidate).strip():
                safe = sanitize_filename(str(candidate))
                return safe if "." in Path(safe).name else f"{safe}.jpg"
        return sanitize_filename(f"photo-{photo.id or 'download'}.jpg")

    @classmethod
    def _validate_optional_id(cls, value: int | None, name: str) -> None:
        """Validate optional Procore integer identifiers."""
        if value is not None:
            cls._validate_positive_id(value, name)

    @staticmethod
    def _validate_positive_id(value: int, name: str) -> None:
        """Validate Procore integer identifiers."""
        if value <= 0:
            raise ValidationError(f"{name} must be a positive integer.")


def list_photo_albums(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    *,
    page: int | None = None,
    per_page: int | None = None,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> list[PhotoAlbum]:
    """Return photo albums for a Procore project."""
    return PhotosService(client=client).list_photo_albums(
        project_id,
        company_id=company_id,
        page=page,
        per_page=per_page,
        params=params,
        **extra_params,
    )


def get_photo_album(
    project_id: int,
    album_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
) -> PhotoAlbum:
    """Return one photo album."""
    return PhotosService(client=client).get_photo_album(
        project_id,
        album_id,
        company_id=company_id,
    )


def find_photo_album(
    project_id: int,
    name: str | None = None,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
) -> PhotoAlbum:
    """Find one photo album by name."""
    return PhotosService(client=client).find_photo_album(
        project_id,
        name=name,
        company_id=company_id,
    )


def list_photos(
    project_id: int,
    company_id: int | None = None,
    album_id: int | None = None,
    image_category_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[PhotoImage]:
    """Return photos for a Procore project or album."""
    return PhotosService(client=client).list_photos(
        project_id,
        company_id=company_id,
        album_id=album_id,
        image_category_id=image_category_id,
        **filters,
    )


def get_photo(
    project_id: int,
    photo_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
) -> PhotoImage:
    """Return one photo."""
    return PhotosService(client=client).get_photo(project_id, photo_id, company_id=company_id)


def find_photo(
    project_id: int,
    photo_id: int | None = None,
    filename: str | None = None,
    description: str | None = None,
    query: str | None = None,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
) -> PhotoImage:
    """Find one photo."""
    return PhotosService(client=client).find_photo(
        project_id,
        photo_id=photo_id,
        filename=filename,
        description=description,
        query=query,
        company_id=company_id,
    )


def download_photo(
    project_id: int,
    photo_id: int,
    output_dir: Path | str = DEFAULT_DOWNLOAD_DIR,
    company_id: int | None = None,
    overwrite: bool = False,
    filename: str | None = None,
    client: ProcoreClient | None = None,
) -> Path:
    """Download one photo."""
    return PhotosService(client=client).download_photo(
        project_id,
        photo_id,
        output_dir=output_dir,
        company_id=company_id,
        overwrite=overwrite,
        filename=filename,
    )


def download_photo_album(
    project_id: int,
    album_id: int,
    output_dir: Path | str = DEFAULT_DOWNLOAD_DIR,
    company_id: int | None = None,
    overwrite: bool = False,
    limit: int | None = None,
    client: ProcoreClient | None = None,
) -> PhotoAlbumDownloadResult:
    """Download photos from one album."""
    return PhotosService(client=client).download_photo_album(
        project_id,
        album_id,
        output_dir=output_dir,
        company_id=company_id,
        overwrite=overwrite,
        limit=limit,
    )
