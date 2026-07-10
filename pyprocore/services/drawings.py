"""Drawing services for the Procore SDK."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.exceptions import ValidationError
from pyprocore.models import Drawing, DrawingArea, DrawingDiscipline
from pyprocore.services.files import FileDownloadService, sanitize_filename
from pyprocore.services.query_params import build_query_params

DEFAULT_DOWNLOAD_DIR = Path(__file__).resolve().parents[1] / "downloads" / "drawings"


class DrawingsService:
    """Service for Procore drawing resources."""

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

    def list_drawing_areas(
        self,
        project_id: int,
        company_id: int | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DrawingArea]:
        """Return drawing areas for a Procore project.

        Args:
            project_id: Procore project ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            params: Optional additional query parameters.
            **extra_params: Additional query parameters passed to Procore.

        Returns:
            A list of typed drawing area models.
        """
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            endpoints.drawing_areas(project_id),
            params=build_query_params(
                params=params,
                extra_params=extra_params,
                project_id=project_id,
            ),
            headers=self._company_headers(company_id),
        )
        return [DrawingArea.model_validate(area) for area in response]

    def get_drawing_area(
        self,
        project_id: int,
        drawing_area_id: int,
        company_id: int | None = None,
    ) -> DrawingArea:
        """Return one drawing area for a Procore project.

        Args:
            project_id: Procore project ID.
            drawing_area_id: Procore drawing area ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            The matching typed drawing area model.
        """
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(drawing_area_id, "drawing_area_id")
        response = self._client.get(
            endpoints.drawing_area(project_id, drawing_area_id),
            params={"project_id": project_id},
            headers=self._company_headers(company_id),
        )
        if not isinstance(response, dict):
            raise ValidationError("Expected Procore drawing area response to be an object.")
        return DrawingArea.model_validate(response)

    def list_drawing_disciplines(
        self,
        project_id: int,
        company_id: int | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DrawingDiscipline]:
        """Return drawing disciplines for a Procore project.

        Args:
            project_id: Procore project ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            params: Optional additional query parameters.
            **extra_params: Additional query parameters passed to Procore.

        Returns:
            A list of typed drawing discipline models.
        """
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            endpoints.drawing_disciplines(project_id),
            params=build_query_params(
                params=params,
                extra_params=extra_params,
                project_id=project_id,
            ),
            headers=self._company_headers(company_id),
        )
        return [DrawingDiscipline.model_validate(discipline) for discipline in response]

    def list_drawings(
        self,
        project_id: int,
        company_id: int | None = None,
        drawing_area_id: int | None = None,
        discipline_id: int | None = None,
        current: bool | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Drawing]:
        """Return drawings for a Procore project.

        Args:
            project_id: Procore project ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            drawing_area_id: Optional drawing area filter.
            discipline_id: Optional drawing discipline filter.
            current: Optional filter for current drawing revisions.
            params: Optional additional query parameters.
            **extra_params: Additional query parameters passed to Procore.

        Returns:
            A list of typed drawing models.
        """
        self._validate_positive_id(project_id, "project_id")
        self._validate_optional_id(drawing_area_id, "drawing_area_id")
        self._validate_optional_id(discipline_id, "discipline_id")

        response = self._client.get_all(
            endpoints.drawings(project_id),
            params=build_query_params(
                params=params,
                extra_params=extra_params,
                project_id=project_id,
                drawing_area_id=drawing_area_id,
                discipline_id=discipline_id,
                current=current,
            ),
            headers=self._company_headers(company_id),
        )
        return [Drawing.model_validate(drawing) for drawing in response]

    def get_drawing(
        self,
        project_id: int,
        drawing_id: int,
        company_id: int | None = None,
    ) -> Drawing:
        """Return one drawing for a Procore project.

        Args:
            project_id: Procore project ID.
            drawing_id: Procore drawing ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            The matching typed drawing model.
        """
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(drawing_id, "drawing_id")
        response = self._client.get(
            endpoints.drawing(project_id, drawing_id),
            params={"project_id": project_id},
            headers=self._company_headers(company_id),
        )
        if not isinstance(response, dict):
            raise ValidationError("Expected Procore drawing response to be an object.")
        return Drawing.model_validate(response)

    def download_drawing(
        self,
        project_id: int,
        drawing_id: int,
        output_dir: Path | str = DEFAULT_DOWNLOAD_DIR,
        filename: str | None = None,
        overwrite: bool = False,
        company_id: int | None = None,
    ) -> Path:
        """Download one Procore drawing when a direct URL is available.

        Args:
            project_id: Procore project ID.
            drawing_id: Procore drawing ID.
            output_dir: Local folder where the drawing should be saved.
            filename: Optional local filename.
            overwrite: Whether to overwrite an existing file.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            The saved drawing path.

        Raises:
            ValidationError: If Procore does not include a downloadable URL.
        """
        drawing = self.get_drawing(project_id, drawing_id, company_id=company_id)
        url = self._drawing_download_url(drawing)
        if url is None:
            raise ValidationError(
                f"Drawing {drawing_id} does not include a download URL or URL. "
                "Procore may require a separate Drawing export or file access step "
                "before the SDK can download this drawing."
            )

        destination = Path(output_dir) / self._drawing_filename(drawing, filename)
        return self._download_service.download_url(url, destination, overwrite=overwrite)

    @property
    def _download_service(self) -> FileDownloadService:
        """Return a file service, creating it only when downloads are requested."""
        if self._file_service is None:
            self._file_service = FileDownloadService()
        return self._file_service

    @staticmethod
    def _drawing_download_url(drawing: Drawing) -> str | None:
        """Return the best available drawing download URL."""
        url = drawing.download_url or drawing.url
        if url is None:
            return None
        normalized = str(url).strip()
        return normalized or None

    @staticmethod
    def _drawing_filename(drawing: Drawing, filename: str | None) -> str:
        """Return a safe local filename for a drawing."""
        for candidate in (
            filename,
            drawing.filename,
            drawing.file_name,
            drawing.title,
            drawing.name,
            drawing.number,
        ):
            if candidate is not None and str(candidate).strip():
                safe = sanitize_filename(str(candidate))
                return safe if "." in Path(safe).name else f"{safe}.pdf"
        return sanitize_filename(f"drawing-{drawing.id or 'download'}.pdf")

    @staticmethod
    def _company_headers(company_id: int | None) -> dict[str, str] | None:
        """Return optional Procore company headers for Drawings endpoints."""
        if company_id is None:
            return None
        return {"Procore-Company-Id": str(company_id)}

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


def list_drawing_areas(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    *,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> list[DrawingArea]:
    """Return drawing areas for a Procore project."""
    return DrawingsService(client=client).list_drawing_areas(
        project_id,
        company_id=company_id,
        params=params,
        **extra_params,
    )


def get_drawing_area(
    project_id: int,
    drawing_area_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
) -> DrawingArea:
    """Return one drawing area for a Procore project."""
    return DrawingsService(client=client).get_drawing_area(
        project_id,
        drawing_area_id,
        company_id=company_id,
    )


def list_drawing_disciplines(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    *,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> list[DrawingDiscipline]:
    """Return drawing disciplines for a Procore project."""
    return DrawingsService(client=client).list_drawing_disciplines(
        project_id,
        company_id=company_id,
        params=params,
        **extra_params,
    )


def list_drawings(
    project_id: int,
    company_id: int | None = None,
    drawing_area_id: int | None = None,
    discipline_id: int | None = None,
    current: bool | None = None,
    client: ProcoreClient | None = None,
    *,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> list[Drawing]:
    """Return drawings for a Procore project."""
    return DrawingsService(client=client).list_drawings(
        project_id,
        company_id=company_id,
        drawing_area_id=drawing_area_id,
        discipline_id=discipline_id,
        current=current,
        params=params,
        **extra_params,
    )


def get_drawing(
    project_id: int,
    drawing_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
) -> Drawing:
    """Return one drawing for a Procore project."""
    return DrawingsService(client=client).get_drawing(
        project_id,
        drawing_id,
        company_id=company_id,
    )


def download_drawing(
    project_id: int,
    drawing_id: int,
    output_dir: Path | str = DEFAULT_DOWNLOAD_DIR,
    filename: str | None = None,
    overwrite: bool = False,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
) -> Path:
    """Download one Procore drawing."""
    return DrawingsService(client=client).download_drawing(
        project_id,
        drawing_id,
        output_dir=output_dir,
        filename=filename,
        overwrite=overwrite,
        company_id=company_id,
    )
