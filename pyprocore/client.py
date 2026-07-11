"""Object-oriented client interface for PyProcore services."""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal

from pyprocore.automation import (
    AutomationInput,
    WorkflowPackage,
    build_rfi_package,
    build_submittal_package,
    build_workflow_package,
)
from pyprocore.core.config import get_settings
from pyprocore.core.exceptions import ValidationError
from pyprocore.models import (
    RFI,
    Company,
    DailyLogCount,
    DailyLogEntry,
    DailyLogHeader,
    DailyLogsByType,
    DelayLogType,
    Document,
    DocumentFolder,
    Drawing,
    DrawingArea,
    DrawingDiscipline,
    PhotoAlbum,
    PhotoAlbumDownloadResult,
    PhotoImage,
    Project,
    SpecificationSection,
    SpecificationSectionRevision,
    SpecificationSet,
    Submittal,
)
from pyprocore.services import (
    download_document,
    download_drawing,
    download_photo,
    download_photo_album,
    download_rfi_attachments,
    download_specification_section_revision,
    download_submittal_attachments,
    find_company,
    find_document,
    find_document_folder,
    find_drawing,
    find_drawings_contains,
    find_photo,
    find_photo_album,
    find_project,
    find_project_contains,
    find_rfi,
    find_specification_section,
    find_submittal,
    get_daily_log,
    get_daily_log_counts,
    get_daily_log_header,
    get_document,
    get_document_folder,
    get_drawing,
    get_drawing_area,
    get_photo,
    get_photo_album,
    get_project,
    get_rfi,
    get_specification_section,
    get_specification_section_revision,
    get_submittal,
    list_accident_logs,
    list_call_logs,
    list_companies,
    list_daily_construction_report_logs,
    list_daily_log_headers,
    list_daily_logs,
    list_daily_logs_for_date,
    list_delay_log_types,
    list_delay_logs,
    list_delivery_logs,
    list_document_folders,
    list_documents,
    list_drawing_areas,
    list_drawing_disciplines,
    list_drawings,
    list_dumpster_logs,
    list_manpower_logs,
    list_notes_logs,
    list_photo_albums,
    list_photos,
    list_plan_revision_logs,
    list_productivity_logs,
    list_projects,
    list_rfis,
    list_specification_section_revisions,
    list_specification_sections,
    list_specification_sets,
    list_submittals,
    list_visitor_logs,
)
from pyprocore.workflows import (
    ProjectContextResult,
    ProjectSyncResult,
    SyncResult,
    build_project_context_package,
    export_rfis_to_csv,
    export_rfis_to_jsonl,
    export_submittals_to_csv,
    export_submittals_to_jsonl,
    sync_documents_to_folder,
    sync_project_to_folder,
    sync_rfis_to_folder,
    sync_submittals_to_folder,
)


class CompaniesClient:
    """Convenience methods for Procore company resources."""

    def list(self) -> list[Company]:
        """List companies available to the authenticated Procore user.

        Returns:
            A list of typed company models.
        """
        return list_companies()

    def find(self, name: str) -> Company:
        """Find one company by name or name fragment.

        Args:
            name: Company name or partial name.

        Returns:
            The matching typed company model.
        """
        return find_company(name)


class ProjectsClient:
    """Convenience methods for Procore project resources."""

    def list(self, company_id: int | None = None) -> list[Project]:
        """List projects for a Procore company.

        Args:
            company_id: Optional Procore company ID. Defaults to
                ``PROCORE_COMPANY_ID``.

        Returns:
            A list of typed project models.
        """
        resolved_company_id = company_id or get_settings().company_id
        return list_projects(company_id=resolved_company_id)

    def get(self, project_id: int) -> Project:
        """Get one project from the configured company.

        Args:
            project_id: Procore project ID.

        Returns:
            The matching typed project model.
        """
        return get_project(project_id=project_id)

    def find(
        self,
        name: str | None = None,
        *,
        number: str | int | None = None,
        company_id: int | None = None,
    ) -> Project:
        """Find one project by name or project number.

        Args:
            name: Project name or name fragment.
            number: Project number.
            company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.

        Returns:
            The matching typed project model.
        """
        return find_project(name=name, number=number, company_id=company_id)

    def find_contains(self, text: str, *, company_id: int | None = None) -> Project:
        """Find one project whose name or number contains text.

        Args:
            text: Text to search for in project names or numbers.
            company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.

        Returns:
            The matching typed project model.
        """
        return find_project_contains(text, company_id=company_id)


class RFIsClient:
    """Convenience methods for Procore RFI resources."""

    def list(
        self,
        project_id: int,
        *,
        status: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[RFI]:
        """List RFIs for a Procore project.

        Args:
            project_id: Procore project ID.
            status: Optional RFI status filter.
            updated_after: Optional lower bound for updated date filtering.
            updated_before: Optional upper bound for updated date filtering.
            created_after: Optional lower bound for created date filtering.
            created_before: Optional upper bound for created date filtering.
            params: Optional additional query parameters.
            **extra_params: Additional query parameters passed to Procore.

        Returns:
            A list of typed RFI models.
        """
        return list_rfis(
            project_id=project_id,
            status=status,
            updated_after=updated_after,
            updated_before=updated_before,
            created_after=created_after,
            created_before=created_before,
            params=params,
            **extra_params,
        )

    def get(self, project_id: int, rfi_id: int) -> RFI:
        """Get one RFI by project ID and RFI ID.

        Args:
            project_id: Procore project ID.
            rfi_id: Procore RFI ID.

        Returns:
            The matching typed RFI model.
        """
        return get_rfi(project_id=project_id, rfi_id=rfi_id)

    def find(self, project_id: int, *, number: str | int) -> RFI:
        """Find one RFI by number within a project.

        Args:
            project_id: Procore project ID.
            number: RFI number.

        Returns:
            The matching typed RFI model.
        """
        return find_rfi(project_id=project_id, number=number)

    def download_attachments(
        self,
        project_id: int,
        rfi_id: int,
        output_dir: Path | str | None = None,
        *,
        overwrite: bool = False,
    ) -> builtins.list[Path]:
        """Download all attachments from one RFI.

        Args:
            project_id: Procore project ID.
            rfi_id: Procore RFI ID.
            output_dir: Optional local directory for downloaded files.
            overwrite: Whether to overwrite existing files.

        Returns:
            Paths to downloaded files.
        """
        return download_rfi_attachments(
            project_id=project_id,
            rfi_id=rfi_id,
            destination_dir=output_dir,
            overwrite=overwrite,
        )


class SubmittalsClient:
    """Convenience methods for Procore submittal resources."""

    def list(
        self,
        project_id: int,
        *,
        status: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Submittal]:
        """List submittals for a Procore project.

        Args:
            project_id: Procore project ID.
            status: Optional submittal status filter.
            updated_after: Optional lower bound for updated date filtering.
            updated_before: Optional upper bound for updated date filtering.
            created_after: Optional lower bound for created date filtering.
            created_before: Optional upper bound for created date filtering.
            params: Optional additional query parameters.
            **extra_params: Additional query parameters passed to Procore.

        Returns:
            A list of typed submittal models.
        """
        return list_submittals(
            project_id=project_id,
            status=status,
            updated_after=updated_after,
            updated_before=updated_before,
            created_after=created_after,
            created_before=created_before,
            params=params,
            **extra_params,
        )

    def get(self, project_id: int, submittal_id: int) -> Submittal:
        """Get one submittal by project ID and submittal ID.

        Args:
            project_id: Procore project ID.
            submittal_id: Procore submittal ID.

        Returns:
            The matching typed submittal model.
        """
        return get_submittal(project_id=project_id, submittal_id=submittal_id)

    def find(self, project_id: int, *, number: str | int) -> Submittal:
        """Find one submittal by number within a project.

        Args:
            project_id: Procore project ID.
            number: Submittal number.

        Returns:
            The matching typed submittal model.
        """
        return find_submittal(project_id=project_id, number=number)

    def download_attachments(
        self,
        project_id: int,
        submittal_id: int,
        output_dir: Path | str | None = None,
        *,
        overwrite: bool = False,
    ) -> builtins.list[Path]:
        """Download all attachments from one submittal.

        Args:
            project_id: Procore project ID.
            submittal_id: Procore submittal ID.
            output_dir: Optional local directory for downloaded files.
            overwrite: Whether to overwrite existing files.

        Returns:
            Paths to downloaded files.
        """
        return download_submittal_attachments(
            project_id=project_id,
            submittal_id=submittal_id,
            destination_dir=output_dir,
            overwrite=overwrite,
        )


class DocumentsClient:
    """Convenience methods for Procore document resources."""

    def list_folders(
        self,
        project_id: int,
        parent_id: int | None = None,
        *,
        params: Mapping[str, Any] | None = None,
        company_id: int | None = None,
        **filters: Any,
    ) -> list[DocumentFolder]:
        """List document folders for a Procore project.

        Args:
            project_id: Procore project ID.
            parent_id: Optional parent folder ID filter.
            params: Optional additional query parameters.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            **filters: Additional query parameters passed to Procore.

        Returns:
            A list of typed document folder models.
        """
        return list_document_folders(
            project_id=project_id,
            parent_id=parent_id,
            params=params,
            company_id=company_id,
            **filters,
        )

    def get_folder(
        self,
        project_id: int,
        folder_id: int,
        *,
        company_id: int | None = None,
    ) -> DocumentFolder:
        """Get one document folder.

        Args:
            project_id: Procore project ID.
            folder_id: Procore document folder ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            The matching typed document folder model.
        """
        return get_document_folder(
            project_id=project_id,
            folder_id=folder_id,
            company_id=company_id,
        )

    def find_folder(self, project_id: int, name: str) -> DocumentFolder:
        """Find one document folder by name.

        Args:
            project_id: Procore project ID.
            name: Folder name or name fragment.

        Returns:
            The matching typed document folder model.
        """
        return find_document_folder(project_id=project_id, name=name)

    def list(
        self,
        project_id: int,
        folder_id: int | None = None,
        *,
        params: Mapping[str, Any] | None = None,
        recursive: bool = False,
        company_id: int | None = None,
        **filters: Any,
    ) -> list[Document]:
        """List documents for a Procore project.

        Args:
            project_id: Procore project ID.
            folder_id: Optional document folder ID filter.
            params: Optional additional query parameters.
            recursive: Whether to traverse discovered child folders.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            **filters: Additional query parameters passed to Procore.

        Returns:
            A list of typed document models.
        """
        return list_documents(
            project_id=project_id,
            folder_id=folder_id,
            params=params,
            recursive=recursive,
            company_id=company_id,
            **filters,
        )

    def get(
        self,
        project_id: int,
        document_id: int,
        *,
        company_id: int | None = None,
    ) -> Document:
        """Get one document.

        Args:
            project_id: Procore project ID.
            document_id: Procore document ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            The matching typed document model.
        """
        return get_document(
            project_id=project_id,
            document_id=document_id,
            company_id=company_id,
        )

    def find(
        self,
        project_id: int,
        *,
        name: str | None = None,
        filename: str | None = None,
    ) -> Document:
        """Find one document by name or filename.

        Args:
            project_id: Procore project ID.
            name: Document name or name fragment.
            filename: Document filename or filename fragment.

        Returns:
            The matching typed document model.
        """
        return find_document(project_id=project_id, name=name, filename=filename)

    def download(
        self,
        project_id: int,
        document_id: int,
        output_dir: Path | str = "downloads/documents",
        filename: str | None = None,
        *,
        company_id: int | None = None,
        overwrite: bool = False,
    ) -> Path:
        """Download one document.

        Args:
            project_id: Procore project ID.
            document_id: Procore document ID.
            output_dir: Local folder where the document should be saved.
            filename: Optional local filename.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            overwrite: Whether to overwrite an existing file.

        Returns:
            The saved document path.
        """
        return download_document(
            project_id=project_id,
            document_id=document_id,
            output_dir=output_dir,
            filename=filename,
            company_id=company_id,
            overwrite=overwrite,
        )


class DrawingsClient:
    """Convenience methods for Procore drawing resources."""

    def list_areas(
        self,
        project_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> list[DrawingArea]:
        """List drawing areas for a Procore project.

        Args:
            project_id: Procore project ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            **filters: Additional query parameters passed to Procore.

        Returns:
            A list of typed drawing area models.
        """
        return list_drawing_areas(project_id, company_id=company_id, **filters)

    def get_area(
        self,
        project_id: int,
        drawing_area_id: int,
        company_id: int | None = None,
    ) -> DrawingArea:
        """Get one drawing area.

        Args:
            project_id: Procore project ID.
            drawing_area_id: Procore drawing area ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            The matching typed drawing area model.
        """
        return get_drawing_area(project_id, drawing_area_id, company_id=company_id)

    def list_disciplines(
        self,
        project_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> list[DrawingDiscipline]:
        """List drawing disciplines for a Procore project.

        Args:
            project_id: Procore project ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            **filters: Additional query parameters passed to Procore.

        Returns:
            A list of typed drawing discipline models.
        """
        return list_drawing_disciplines(project_id, company_id=company_id, **filters)

    def list(
        self,
        project_id: int,
        company_id: int | None = None,
        drawing_area_id: int | None = None,
        discipline_id: int | None = None,
        current: bool | None = None,
        **filters: Any,
    ) -> builtins.list[Drawing]:
        """List drawings for a Procore project.

        Args:
            project_id: Procore project ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            drawing_area_id: Optional drawing area filter.
            discipline_id: Optional drawing discipline filter.
            current: Optional filter for current drawing revisions.
            **filters: Additional query parameters passed to Procore.

        Returns:
            A list of typed drawing models.
        """
        return list_drawings(
            project_id,
            company_id=company_id,
            drawing_area_id=drawing_area_id,
            discipline_id=discipline_id,
            current=current,
            **filters,
        )

    def get(
        self,
        project_id: int,
        drawing_id: int,
        company_id: int | None = None,
        drawing_area_id: int | None = None,
    ) -> Drawing:
        """Get one drawing.

        Args:
            project_id: Procore project ID.
            drawing_id: Procore drawing ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            drawing_area_id: Optional drawing area ID. When omitted, the
                service searches drawing areas to locate the drawing.

        Returns:
            The matching typed drawing model.
        """
        return get_drawing(
            project_id,
            drawing_id,
            company_id=company_id,
            drawing_area_id=drawing_area_id,
        )

    def find(
        self,
        project_id: int,
        *,
        number: str | int | None = None,
        title: str | None = None,
        company_id: int | None = None,
    ) -> Drawing:
        """Find one drawing by number or title.

        Args:
            project_id: Procore project ID.
            number: Drawing number or number fragment.
            title: Drawing title or title fragment.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            The matching typed drawing model.
        """
        return find_drawing(project_id, number=number, title=title, company_id=company_id)

    def find_contains(
        self,
        project_id: int,
        text: str,
        company_id: int | None = None,
    ) -> builtins.list[Drawing]:
        """Find drawings whose number or title contains text.

        Args:
            project_id: Procore project ID.
            text: Search text.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            Matching typed drawing models.
        """
        return find_drawings_contains(project_id, text, company_id=company_id)

    def download(
        self,
        project_id: int,
        drawing_id: int,
        output_dir: Path | str = "downloads/drawings",
        filename: str | None = None,
        *,
        overwrite: bool = False,
        company_id: int | None = None,
        drawing_area_id: int | None = None,
    ) -> Path:
        """Download one drawing.

        Args:
            project_id: Procore project ID.
            drawing_id: Procore drawing ID.
            output_dir: Local folder where the drawing should be saved.
            filename: Optional local filename.
            overwrite: Whether to overwrite an existing file.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            drawing_area_id: Optional drawing area ID. When omitted, the
                service searches drawing areas to locate the drawing.

        Returns:
            The saved drawing path.
        """
        return download_drawing(
            project_id,
            drawing_id,
            output_dir=output_dir,
            filename=filename,
            overwrite=overwrite,
            company_id=company_id,
            drawing_area_id=drawing_area_id,
        )


class SpecificationsClient:
    """Convenience methods for Procore specification resources."""

    def list_sets(
        self,
        project_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> list[SpecificationSet]:
        """List specification sets for a Procore project."""
        return list_specification_sets(project_id, company_id=company_id, **filters)

    def list_sections(
        self,
        project_id: int,
        company_id: int | None = None,
        specification_area_id: int | None = None,
        specification_set_id: int | None = None,
        division_id: int | None = None,
        sort: str | None = None,
        **filters: Any,
    ) -> list[SpecificationSection]:
        """List specification sections for a Procore project."""
        return list_specification_sections(
            project_id,
            company_id=company_id,
            specification_area_id=specification_area_id,
            specification_set_id=specification_set_id,
            division_id=division_id,
            sort=sort,
            **filters,
        )

    def get_section(
        self,
        project_id: int,
        specification_section_id: int,
        company_id: int | None = None,
    ) -> SpecificationSection:
        """Get one specification section."""
        return get_specification_section(
            project_id,
            specification_section_id,
            company_id=company_id,
        )

    def find_section(
        self,
        project_id: int,
        *,
        number: str | int | None = None,
        title: str | None = None,
        query: str | None = None,
        company_id: int | None = None,
    ) -> SpecificationSection:
        """Find one specification section by number, title, or search text."""
        return find_specification_section(
            project_id,
            number=number,
            title=title,
            query=query,
            company_id=company_id,
        )

    def list_revisions(
        self,
        project_id: int,
        company_id: int | None = None,
        specification_section_id: int | None = None,
        page: int | None = None,
        per_page: int | None = None,
        **filters: Any,
    ) -> list[SpecificationSectionRevision]:
        """List specification section revisions for a Procore project."""
        return list_specification_section_revisions(
            project_id,
            company_id=company_id,
            specification_section_id=specification_section_id,
            page=page,
            per_page=per_page,
            **filters,
        )

    def get_revision(
        self,
        project_id: int,
        revision_id: int,
        company_id: int | None = None,
    ) -> SpecificationSectionRevision:
        """Get one specification section revision."""
        return get_specification_section_revision(
            project_id,
            revision_id,
            company_id=company_id,
        )

    def download_revision(
        self,
        project_id: int,
        revision_id: int,
        output_dir: Path | str = "downloads/specifications",
        *,
        company_id: int | None = None,
        overwrite: bool = False,
    ) -> Path:
        """Download one specification section revision."""
        return download_specification_section_revision(
            project_id,
            revision_id,
            output_dir=output_dir,
            company_id=company_id,
            overwrite=overwrite,
        )


class PhotosClient:
    """Convenience methods for Procore photo resources."""

    def list_albums(
        self,
        project_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> list[PhotoAlbum]:
        """List photo albums for a Procore project."""
        return list_photo_albums(project_id, company_id=company_id, **filters)

    def get_album(
        self,
        project_id: int,
        album_id: int,
        company_id: int | None = None,
    ) -> PhotoAlbum:
        """Get one photo album."""
        return get_photo_album(project_id, album_id, company_id=company_id)

    def find_album(
        self,
        project_id: int,
        name: str | None = None,
        company_id: int | None = None,
    ) -> PhotoAlbum:
        """Find one photo album by name."""
        return find_photo_album(project_id, name=name, company_id=company_id)

    def list(
        self,
        project_id: int,
        company_id: int | None = None,
        album_id: int | None = None,
        **filters: Any,
    ) -> list[PhotoImage]:
        """List photos for a Procore project or album."""
        return list_photos(project_id, company_id=company_id, album_id=album_id, **filters)

    def get(
        self,
        project_id: int,
        photo_id: int,
        company_id: int | None = None,
    ) -> PhotoImage:
        """Get one photo."""
        return get_photo(project_id, photo_id, company_id=company_id)

    def find(
        self,
        project_id: int,
        photo_id: int | None = None,
        filename: str | None = None,
        description: str | None = None,
        query: str | None = None,
        company_id: int | None = None,
    ) -> PhotoImage:
        """Find one photo."""
        return find_photo(
            project_id,
            photo_id=photo_id,
            filename=filename,
            description=description,
            query=query,
            company_id=company_id,
        )

    def download(
        self,
        project_id: int,
        photo_id: int,
        output_dir: Path | str = "downloads/photos",
        company_id: int | None = None,
        *,
        overwrite: bool = False,
        filename: str | None = None,
    ) -> Path:
        """Download one photo."""
        return download_photo(
            project_id,
            photo_id,
            output_dir=output_dir,
            company_id=company_id,
            overwrite=overwrite,
            filename=filename,
        )

    def download_album(
        self,
        project_id: int,
        album_id: int,
        output_dir: Path | str = "downloads/photos",
        company_id: int | None = None,
        *,
        overwrite: bool = False,
        limit: int | None = None,
    ) -> PhotoAlbumDownloadResult:
        """Download photos from one album."""
        return download_photo_album(
            project_id,
            album_id,
            output_dir=output_dir,
            company_id=company_id,
            overwrite=overwrite,
            limit=limit,
        )


class DailyLogsClient:
    """Convenience methods for Procore Daily Logs resources."""

    def counts(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogCount]:
        """Return Daily Log counts."""
        return get_daily_log_counts(project_id, company_id=company_id, **filters)

    def headers(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogHeader]:
        """Return Daily Log headers."""
        return list_daily_log_headers(project_id, company_id=company_id, **filters)

    def get_header(
        self,
        project_id: int,
        header_id: int | None = None,
        log_date: str | None = None,
        company_id: int | None = None,
    ) -> DailyLogHeader:
        """Return one Daily Log header."""
        return get_daily_log_header(
            project_id, header_id=header_id, log_date=log_date, company_id=company_id
        )

    def list(
        self, project_id: int, log_type: str, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return Daily Log entries for a supported log type."""
        return list_daily_logs(project_id, log_type, company_id=company_id, **filters)

    def get(
        self,
        project_id: int,
        log_type: str,
        log_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> DailyLogEntry:
        """Return one Daily Log entry."""
        return get_daily_log(project_id, log_type, log_id, company_id=company_id, **filters)

    def list_for_date(
        self,
        project_id: int,
        company_id: int | None = None,
        log_date: str | None = None,
        log_types: Sequence[str] | None = None,
    ) -> DailyLogsByType:
        """Return multiple Daily Log types for one date."""
        return list_daily_logs_for_date(
            project_id, company_id=company_id, log_date=log_date, log_types=log_types
        )

    def delay_types(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DelayLogType]:
        """Return delay log types."""
        return list_delay_log_types(project_id, company_id=company_id, **filters)

    def manpower(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return manpower logs."""
        return list_manpower_logs(project_id, company_id=company_id, **filters)

    def notes(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return notes logs."""
        return list_notes_logs(project_id, company_id=company_id, **filters)

    def daily_construction_reports(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return daily construction report logs."""
        return list_daily_construction_report_logs(project_id, company_id=company_id, **filters)

    def delays(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return delay logs."""
        return list_delay_logs(project_id, company_id=company_id, **filters)

    def deliveries(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return delivery logs."""
        return list_delivery_logs(project_id, company_id=company_id, **filters)

    def calls(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return call logs."""
        return list_call_logs(project_id, company_id=company_id, **filters)

    def accidents(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return accident logs."""
        return list_accident_logs(project_id, company_id=company_id, **filters)

    def dumpsters(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return dumpster logs."""
        return list_dumpster_logs(project_id, company_id=company_id, **filters)

    def visitors(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return visitor logs."""
        return list_visitor_logs(project_id, company_id=company_id, **filters)

    def productivity(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return productivity logs."""
        return list_productivity_logs(project_id, company_id=company_id, **filters)

    def plan_revisions(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return plan revision logs."""
        return list_plan_revision_logs(project_id, company_id=company_id, **filters)


class AutomationClient:
    """Convenience methods for AI-ready automation workflow packages."""

    def build_package(
        self,
        input_data: AutomationInput | None = None,
        *,
        company_id: int | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        item_type: Literal["rfi", "submittal"] | None = None,
        item_id: int | None = None,
        item_number: str | None = None,
        download_attachments: bool = True,
        output_dir: Path | str | None = None,
    ) -> WorkflowPackage:
        """Build an automation package from a typed input model.

        Args:
            input_data: Optional workflow package input. When omitted, keyword
                arguments are used to build one.
            company_id: Optional company ID used for project search.
            project_id: Optional project ID.
            project_name: Optional project name or name fragment.
            project_number: Optional project number.
            item_type: Workflow target type, such as ``rfi`` or ``submittal``.
            item_id: Optional item ID.
            item_number: Optional item number.
            download_attachments: Whether to download attachments.
            output_dir: Optional attachment output directory.

        Returns:
            A resolved workflow package.
        """
        if input_data is None:
            if item_type is None:
                raise ValidationError(
                    "item_type is required when build_package is called without input_data."
                )
            input_data = AutomationInput(
                company_id=company_id,
                project_id=project_id,
                project_name=project_name,
                project_number=project_number,
                item_type=item_type,
                item_id=item_id,
                item_number=item_number,
                download_attachments=download_attachments,
                output_dir=output_dir,
            )
        return build_workflow_package(input_data)

    def build_rfi_package(
        self,
        *,
        company_id: int | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        rfi_id: int | None = None,
        number: str | None = None,
        download_attachments: bool = True,
        output_dir: Path | str | None = None,
    ) -> WorkflowPackage:
        """Build an automation package for one RFI.

        Args:
            company_id: Optional company ID used for project search.
            project_id: Optional project ID.
            project_name: Optional project name or name fragment.
            project_number: Optional project number.
            rfi_id: Optional RFI ID.
            number: Optional RFI number.
            download_attachments: Whether to download attachments.
            output_dir: Optional attachment output directory.

        Returns:
            A resolved RFI workflow package.
        """
        return build_rfi_package(
            company_id=company_id,
            project_id=project_id,
            project_name=project_name,
            project_number=project_number,
            rfi_id=rfi_id,
            number=number,
            download_attachments=download_attachments,
            output_dir=output_dir,
        )

    def build_submittal_package(
        self,
        *,
        company_id: int | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        submittal_id: int | None = None,
        number: str | None = None,
        download_attachments: bool = True,
        output_dir: Path | str | None = None,
    ) -> WorkflowPackage:
        """Build an automation package for one submittal.

        Args:
            company_id: Optional company ID used for project search.
            project_id: Optional project ID.
            project_name: Optional project name or name fragment.
            project_number: Optional project number.
            submittal_id: Optional submittal ID.
            number: Optional submittal number.
            download_attachments: Whether to download attachments.
            output_dir: Optional attachment output directory.

        Returns:
            A resolved submittal workflow package.
        """
        return build_submittal_package(
            company_id=company_id,
            project_id=project_id,
            project_name=project_name,
            project_number=project_number,
            submittal_id=submittal_id,
            number=number,
            download_attachments=download_attachments,
            output_dir=output_dir,
        )


class WorkflowsClient:
    """Convenience methods for local exports and folder sync workflows."""

    def export_rfis_to_csv(
        self,
        project_id: int,
        output_path: Path | str,
        *,
        status: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        params: dict[str, object] | None = None,
        **extra_params: Any,
    ) -> Path:
        """Export RFIs to CSV.

        Args:
            project_id: Procore project ID.
            output_path: CSV path to create.
            status: Optional status filter.
            updated_after: Optional lower bound for updated date filtering.
            updated_before: Optional upper bound for updated date filtering.
            created_after: Optional lower bound for created date filtering.
            created_before: Optional upper bound for created date filtering.
            params: Optional additional query parameters.
            **extra_params: Additional Procore query parameters.

        Returns:
            The created CSV path.
        """
        return export_rfis_to_csv(
            project_id,
            output_path,
            status=status,
            updated_after=updated_after,
            updated_before=updated_before,
            created_after=created_after,
            created_before=created_before,
            params=params,
            **extra_params,
        )

    def export_submittals_to_csv(
        self,
        project_id: int,
        output_path: Path | str,
        *,
        status: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        params: dict[str, object] | None = None,
        **extra_params: Any,
    ) -> Path:
        """Export submittals to CSV.

        Args:
            project_id: Procore project ID.
            output_path: CSV path to create.
            status: Optional status filter.
            updated_after: Optional lower bound for updated date filtering.
            updated_before: Optional upper bound for updated date filtering.
            created_after: Optional lower bound for created date filtering.
            created_before: Optional upper bound for created date filtering.
            params: Optional additional query parameters.
            **extra_params: Additional Procore query parameters.

        Returns:
            The created CSV path.
        """
        return export_submittals_to_csv(
            project_id,
            output_path,
            status=status,
            updated_after=updated_after,
            updated_before=updated_before,
            created_after=created_after,
            created_before=created_before,
            params=params,
            **extra_params,
        )

    def export_rfis_to_jsonl(
        self,
        project_id: int,
        output_path: Path | str,
        *,
        status: str | None = None,
        **filters: Any,
    ) -> Path:
        """Export RFIs to newline-delimited JSON."""
        return export_rfis_to_jsonl(project_id, output_path, status=status, **filters)

    def export_submittals_to_jsonl(
        self,
        project_id: int,
        output_path: Path | str,
        *,
        status: str | None = None,
        **filters: Any,
    ) -> Path:
        """Export submittals to newline-delimited JSON."""
        return export_submittals_to_jsonl(project_id, output_path, status=status, **filters)

    def sync_rfis_to_folder(
        self,
        project_id: int,
        output_dir: Path | str,
        *,
        status: str | None = None,
        download_attachments: bool = True,
        overwrite: bool = False,
        create_tracker: bool = True,
        create_markdown: bool = True,
        dry_run: bool = False,
        incremental: bool = False,
        **filters: Any,
    ) -> SyncResult:
        """Sync RFIs into a local folder tree."""
        return sync_rfis_to_folder(
            project_id,
            output_dir,
            status=status,
            download_attachments=download_attachments,
            overwrite=overwrite,
            create_tracker=create_tracker,
            create_markdown=create_markdown,
            dry_run=dry_run,
            incremental=incremental,
            **filters,
        )

    def sync_submittals_to_folder(
        self,
        project_id: int,
        output_dir: Path | str,
        *,
        status: str | None = None,
        download_attachments: bool = True,
        overwrite: bool = False,
        create_tracker: bool = True,
        create_markdown: bool = True,
        dry_run: bool = False,
        incremental: bool = False,
        **filters: Any,
    ) -> SyncResult:
        """Sync submittals into a local folder tree."""
        return sync_submittals_to_folder(
            project_id,
            output_dir,
            status=status,
            download_attachments=download_attachments,
            overwrite=overwrite,
            create_tracker=create_tracker,
            create_markdown=create_markdown,
            dry_run=dry_run,
            incremental=incremental,
            **filters,
        )

    def sync_documents_to_folder(
        self,
        project_id: int,
        output_dir: Path | str,
        *,
        folder_id: int | None = None,
        recursive: bool = False,
        overwrite: bool = False,
        dry_run: bool = False,
        incremental: bool = False,
        create_tracker: bool = True,
        create_markdown: bool = True,
        **filters: Any,
    ) -> SyncResult:
        """Sync documents into a local folder tree."""
        return sync_documents_to_folder(
            project_id,
            output_dir,
            folder_id=folder_id,
            recursive=recursive,
            overwrite=overwrite,
            dry_run=dry_run,
            incremental=incremental,
            create_tracker=create_tracker,
            create_markdown=create_markdown,
            **filters,
        )

    def sync_project_to_folder(
        self,
        project_id: int,
        output_dir: Path | str,
        *,
        include_rfis: bool = True,
        include_submittals: bool = True,
        status: str | None = None,
        download_attachments: bool = True,
        overwrite: bool = False,
        create_tracker: bool = True,
        create_markdown: bool = True,
        dry_run: bool = False,
        incremental: bool = False,
        **filters: Any,
    ) -> ProjectSyncResult:
        """Sync RFIs and/or submittals into one project folder."""
        return sync_project_to_folder(
            project_id,
            output_dir,
            include_rfis=include_rfis,
            include_submittals=include_submittals,
            status=status,
            download_attachments=download_attachments,
            overwrite=overwrite,
            create_tracker=create_tracker,
            create_markdown=create_markdown,
            dry_run=dry_run,
            incremental=incremental,
            **filters,
        )

    def build_project_context_package(
        self,
        project_id: int,
        output_dir: Path | str | None = None,
        *,
        company_id: int | None = None,
        include: Sequence[str] | str | None = None,
        exclude: Sequence[str] | str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        log_date: str | None = None,
        max_items: int | None = None,
        download_files: bool = False,
        overwrite: bool = False,
        continue_on_error: bool = True,
    ) -> ProjectContextResult:
        """Build an AI-ready read-only project context package."""
        return build_project_context_package(
            project_id,
            company_id=company_id,
            output_dir=output_dir,
            include=include,
            exclude=exclude,
            start_date=start_date,
            end_date=end_date,
            log_date=log_date,
            max_items=max_items,
            download_files=download_files,
            overwrite=overwrite,
            continue_on_error=continue_on_error,
        )


class Procore:
    """Beginner-friendly object-oriented entry point for PyProcore.

    The grouped clients call the same service functions that PyProcore already
    exposes. Use this interface when you prefer discoverable dot notation such
    as ``client.projects.list(company_id=123456)``.
    """

    def __init__(self) -> None:
        """Create grouped service clients."""
        self.companies = CompaniesClient()
        self.projects = ProjectsClient()
        self.rfis = RFIsClient()
        self.submittals = SubmittalsClient()
        self.documents = DocumentsClient()
        self.drawings = DrawingsClient()
        self.specifications = SpecificationsClient()
        self.photos = PhotosClient()
        self.daily_logs = DailyLogsClient()
        self.automation = AutomationClient()
        self.workflows = WorkflowsClient()


__all__ = [
    "AutomationClient",
    "CompaniesClient",
    "DailyLogsClient",
    "DocumentsClient",
    "DrawingsClient",
    "Procore",
    "ProjectsClient",
    "PhotosClient",
    "RFIsClient",
    "SpecificationsClient",
    "SubmittalsClient",
    "WorkflowsClient",
]
