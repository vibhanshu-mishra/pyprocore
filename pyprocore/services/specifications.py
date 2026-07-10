"""Specification services for the Procore SDK."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.config import get_settings
from pyprocore.core.exceptions import MultipleResultsError, NotFoundError, ValidationError
from pyprocore.models import (
    SpecificationRevisionDownload,
    SpecificationSection,
    SpecificationSectionRevision,
    SpecificationSet,
)
from pyprocore.services.files import FileDownloadService, sanitize_filename
from pyprocore.services.query_params import build_query_params

DEFAULT_DOWNLOAD_DIR = Path(__file__).resolve().parents[1] / "downloads" / "specifications"


class SpecificationsService:
    """Service for Procore specification resources."""

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

    def list_specification_sets(
        self,
        project_id: int,
        company_id: int | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[SpecificationSet]:
        """Return specification sets for a Procore project.

        Args:
            project_id: Procore project ID.
            company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.
            params: Optional additional query parameters.
            **extra_params: Additional query parameters passed to Procore.

        Returns:
            A list of typed specification set models.
        """
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            endpoints.specification_sets(resolved_company_id, project_id),
            params=build_query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return [
            SpecificationSet.model_validate(item)
            for item in self._extract_items(response, "specification sets")
        ]

    def list_specification_sections(
        self,
        project_id: int,
        company_id: int | None = None,
        specification_area_id: int | None = None,
        specification_set_id: int | None = None,
        division_id: int | None = None,
        sort: str | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[SpecificationSection]:
        """Return specification sections for a Procore project.

        Args:
            project_id: Procore project ID.
            company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.
            specification_area_id: Optional specification area filter.
            specification_set_id: Optional specification set filter.
            division_id: Optional division filter.
            sort: Optional sort value, such as ``number`` or ``-number``.
            params: Optional additional query parameters.
            **extra_params: Additional query parameters passed to Procore.

        Returns:
            A list of typed specification section models.
        """
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_optional_id(specification_area_id, "specification_area_id")
        self._validate_optional_id(specification_set_id, "specification_set_id")
        self._validate_optional_id(division_id, "division_id")
        response = self._client.get_all(
            endpoints.specification_sections(resolved_company_id, project_id),
            params=build_query_params(
                params=params,
                extra_params=extra_params,
                specification_area_id=specification_area_id,
                filter_set_id=specification_set_id,
                filter_division_id=division_id,
                sort=sort,
            ),
            headers=self._company_headers(resolved_company_id),
        )
        return [
            SpecificationSection.model_validate(item)
            for item in self._extract_items(response, "specification sections")
        ]

    def get_specification_section(
        self,
        project_id: int,
        specification_section_id: int,
        company_id: int | None = None,
    ) -> SpecificationSection:
        """Return one specification section by searching the section list.

        Procore's documented section list endpoint is verified. A direct show
        endpoint was not confirmed in the source material, so this method keeps
        behavior conservative by listing sections and matching the ID locally.

        Args:
            project_id: Procore project ID.
            specification_section_id: Procore specification section ID.
            company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.

        Returns:
            The matching typed specification section model.
        """
        self._validate_positive_id(specification_section_id, "specification_section_id")
        for section in self.list_specification_sections(project_id, company_id=company_id):
            if section.id == specification_section_id:
                return section
        raise NotFoundError(
            f"Specification section {specification_section_id} was not found "
            f"in project {project_id}."
        )

    def find_specification_section(
        self,
        project_id: int,
        number: str | int | None = None,
        title: str | None = None,
        query: str | None = None,
        company_id: int | None = None,
    ) -> SpecificationSection:
        """Find one specification section by number, title, or search text.

        Args:
            project_id: Procore project ID.
            number: Optional section number or number fragment.
            title: Optional section title or title fragment.
            query: Optional text matched against number or title.
            company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.

        Returns:
            The matching typed specification section model.
        """
        criteria = [value is not None and str(value).strip() for value in (number, title, query)]
        if not any(criteria):
            raise ValidationError(
                "Provide number, title, or query to find a specification section."
            )

        sections = self.list_specification_sections(project_id, company_id=company_id)
        fields = self._search_fields(number=number, title=title, query=query)
        exact_matches = [
            section for section in sections if self._matches(section, fields, exact=True)
        ]
        if len(exact_matches) == 1:
            return exact_matches[0]
        if len(exact_matches) > 1:
            raise MultipleResultsError("Multiple specification sections matched exactly.")

        partial_matches = [
            section for section in sections if self._matches(section, fields, exact=False)
        ]
        if len(partial_matches) == 1:
            return partial_matches[0]
        if len(partial_matches) > 1:
            raise MultipleResultsError("Multiple specification sections matched the search text.")

        raise NotFoundError("No specification section matched the provided search criteria.")

    def list_specification_section_revisions(
        self,
        project_id: int,
        company_id: int | None = None,
        specification_section_id: int | None = None,
        page: int | None = None,
        per_page: int | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[SpecificationSectionRevision]:
        """Return specification section revisions for a Procore project.

        Args:
            project_id: Procore project ID.
            company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.
            specification_section_id: Optional section ID filter.
            page: Optional starting page.
            per_page: Optional page size. Procore supports up to 1000.
            params: Optional additional query parameters.
            **extra_params: Additional query parameters passed to Procore.

        Returns:
            A list of typed specification section revision models.
        """
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_optional_id(specification_section_id, "specification_section_id")
        self._validate_optional_id(page, "page")
        self._validate_optional_id(per_page, "per_page")
        response = self._client.get_all(
            endpoints.specification_section_revisions(resolved_company_id, project_id),
            params=build_query_params(
                params=params,
                extra_params=extra_params,
                specification_section_id=specification_section_id,
                page=page,
                per_page=per_page,
            ),
            headers=self._company_headers(resolved_company_id),
        )
        return [
            SpecificationSectionRevision.model_validate(item)
            for item in self._extract_items(response, "specification section revisions")
        ]

    def get_specification_section_revision(
        self,
        project_id: int,
        revision_id: int,
        company_id: int | None = None,
    ) -> SpecificationSectionRevision:
        """Return one specification section revision.

        Args:
            project_id: Procore project ID.
            revision_id: Procore specification section revision ID.
            company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.

        Returns:
            The matching typed specification section revision model.
        """
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(revision_id, "revision_id")
        response = self._client.get(
            endpoints.specification_section_revision(
                resolved_company_id,
                project_id,
                revision_id,
            ),
            headers=self._company_headers(resolved_company_id),
        )
        item = self._extract_item(response, "specification section revision")
        return SpecificationSectionRevision.model_validate(item)

    def download_specification_section_revision(
        self,
        project_id: int,
        revision_id: int,
        output_dir: Path | str = DEFAULT_DOWNLOAD_DIR,
        company_id: int | None = None,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Download a specification section revision PDF.

        Args:
            project_id: Procore project ID.
            revision_id: Procore specification section revision ID.
            output_dir: Local folder where the PDF should be saved.
            company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.
            overwrite: Whether to overwrite an existing local file.

        Returns:
            The saved file path.

        Raises:
            ValidationError: If Procore does not include a downloadable URL.
        """
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(revision_id, "revision_id")
        response = self._client.get(
            endpoints.specification_section_revision_download(
                resolved_company_id,
                project_id,
                revision_id,
            ),
            headers=self._company_headers(resolved_company_id),
        )
        download_info = SpecificationRevisionDownload.model_validate(
            self._extract_item(response, "specification revision download")
        )
        url = self._download_url(download_info)
        if url is None:
            raise ValidationError(
                f"Specification revision {revision_id} does not include a download URL."
            )
        destination = Path(output_dir) / self._download_filename(download_info, revision_id)
        return self._download_service.download_url(url, destination, overwrite=overwrite)

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
        SpecificationsService._validate_positive_id(resolved_company_id, "company_id")
        return resolved_company_id

    @staticmethod
    def _company_headers(company_id: int) -> dict[str, str]:
        """Return required Procore company headers for Specifications endpoints."""
        return {"Procore-Company-Id": str(company_id)}

    @classmethod
    def _extract_items(cls, payload: object, resource_name: str) -> list[Mapping[str, Any]]:
        """Extract a list from direct or V2-envelope Procore responses."""
        if isinstance(payload, list):
            items: list[Mapping[str, Any]] = []
            for item in payload:
                if isinstance(item, Mapping):
                    envelope_items = cls._envelope_items(item, resource_name)
                    if envelope_items is not None:
                        items.extend(envelope_items)
                    else:
                        items.append(item)
                    continue
                raise ValidationError(f"Expected Procore {resource_name} item to be an object.")
            return items
        if isinstance(payload, dict):
            envelope_items = cls._envelope_items(payload, resource_name)
            if envelope_items is not None:
                return envelope_items
            return [payload]
        raise ValidationError(f"Expected Procore {resource_name} response to be a list or object.")

    @classmethod
    def _envelope_items(
        cls,
        payload: Mapping[str, Any],
        resource_name: str,
    ) -> list[Mapping[str, Any]] | None:
        """Extract list items from known V2 envelope keys."""
        for key in ("data", "items", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [cls._ensure_mapping(item, resource_name) for item in value]
        return None

    @classmethod
    def _extract_item(cls, payload: object, resource_name: str) -> Mapping[str, Any]:
        """Extract one object from a direct or V2-envelope Procore response."""
        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, dict):
                return data
            return payload
        raise ValidationError(f"Expected Procore {resource_name} response to be an object.")

    @staticmethod
    def _ensure_mapping(item: object, resource_name: str) -> Mapping[str, Any]:
        """Validate that an item is a mapping."""
        if not isinstance(item, Mapping):
            raise ValidationError(f"Expected Procore {resource_name} item to be an object.")
        return item

    @staticmethod
    def _search_fields(
        *,
        number: str | int | None,
        title: str | None,
        query: str | None,
    ) -> dict[str, str]:
        """Build normalized search fields."""
        fields: dict[str, str] = {}
        if number is not None and str(number).strip():
            fields["number"] = str(number).strip().casefold()
        if title is not None and title.strip():
            fields["title"] = title.strip().casefold()
        if query is not None and query.strip():
            fields["query"] = query.strip().casefold()
        return fields

    @staticmethod
    def _matches(
        section: SpecificationSection,
        fields: Mapping[str, str],
        *,
        exact: bool,
    ) -> bool:
        """Return whether a section matches all requested fields."""
        for field, needle in fields.items():
            if field == "query":
                haystacks = (
                    str(section.number or "").casefold(),
                    (section.title or "").casefold(),
                )
                if exact:
                    if needle not in haystacks:
                        return False
                elif not any(needle in haystack for haystack in haystacks):
                    return False
                continue

            value = getattr(section, field)
            haystack = str(value or "").casefold()
            if exact and haystack != needle:
                return False
            if not exact and needle not in haystack:
                return False
        return True

    @staticmethod
    def _download_url(download_info: SpecificationRevisionDownload) -> str | None:
        """Return the best available download URL."""
        url = download_info.download_url or download_info.url or download_info.file_url
        if url is None:
            return None
        normalized = str(url).strip()
        return normalized or None

    @staticmethod
    def _download_filename(
        download_info: SpecificationRevisionDownload,
        revision_id: int,
    ) -> str:
        """Return a safe local filename for a specification revision."""
        for candidate in (
            download_info.filename,
            download_info.file_name,
            download_info.name,
            download_info.title,
            download_info.number,
        ):
            if candidate is not None and str(candidate).strip():
                safe = sanitize_filename(str(candidate))
                return safe if "." in Path(safe).name else f"{safe}.pdf"
        return sanitize_filename(f"specification-revision-{revision_id}.pdf")

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


def list_specification_sets(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    *,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> list[SpecificationSet]:
    """Return specification sets for a Procore project."""
    return SpecificationsService(client=client).list_specification_sets(
        project_id,
        company_id=company_id,
        params=params,
        **extra_params,
    )


def list_specification_sections(
    project_id: int,
    company_id: int | None = None,
    specification_area_id: int | None = None,
    specification_set_id: int | None = None,
    division_id: int | None = None,
    sort: str | None = None,
    client: ProcoreClient | None = None,
    *,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> list[SpecificationSection]:
    """Return specification sections for a Procore project."""
    return SpecificationsService(client=client).list_specification_sections(
        project_id,
        company_id=company_id,
        specification_area_id=specification_area_id,
        specification_set_id=specification_set_id,
        division_id=division_id,
        sort=sort,
        params=params,
        **extra_params,
    )


def get_specification_section(
    project_id: int,
    specification_section_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
) -> SpecificationSection:
    """Return one specification section by searching the section list."""
    return SpecificationsService(client=client).get_specification_section(
        project_id,
        specification_section_id,
        company_id=company_id,
    )


def find_specification_section(
    project_id: int,
    number: str | int | None = None,
    title: str | None = None,
    query: str | None = None,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
) -> SpecificationSection:
    """Find one specification section by number, title, or search text."""
    return SpecificationsService(client=client).find_specification_section(
        project_id,
        number=number,
        title=title,
        query=query,
        company_id=company_id,
    )


def list_specification_section_revisions(
    project_id: int,
    company_id: int | None = None,
    specification_section_id: int | None = None,
    page: int | None = None,
    per_page: int | None = None,
    client: ProcoreClient | None = None,
    *,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> list[SpecificationSectionRevision]:
    """Return specification section revisions for a Procore project."""
    return SpecificationsService(client=client).list_specification_section_revisions(
        project_id,
        company_id=company_id,
        specification_section_id=specification_section_id,
        page=page,
        per_page=per_page,
        params=params,
        **extra_params,
    )


def get_specification_section_revision(
    project_id: int,
    revision_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
) -> SpecificationSectionRevision:
    """Return one specification section revision."""
    return SpecificationsService(client=client).get_specification_section_revision(
        project_id,
        revision_id,
        company_id=company_id,
    )


def download_specification_section_revision(
    project_id: int,
    revision_id: int,
    output_dir: Path | str = DEFAULT_DOWNLOAD_DIR,
    company_id: int | None = None,
    overwrite: bool = False,
    client: ProcoreClient | None = None,
) -> Path:
    """Download one specification section revision."""
    return SpecificationsService(client=client).download_specification_section_revision(
        project_id,
        revision_id,
        output_dir=output_dir,
        company_id=company_id,
        overwrite=overwrite,
    )
