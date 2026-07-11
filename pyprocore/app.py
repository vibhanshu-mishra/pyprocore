"""Command-line entrypoint for Procore SDK operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from pyprocore.auth.diagnostics import (
    AuthExchangeResult,
    AuthLoginUrlResult,
    AuthRefreshResult,
    AuthStatusReport,
    build_authorization_url,
    exchange_code_and_save,
    format_auth_exchange,
    format_auth_refresh,
    format_auth_status,
    format_login_url,
    get_auth_status,
    refresh_auth_token,
)
from pyprocore.automation import AutomationInput, build_workflow_package
from pyprocore.core.config import get_settings
from pyprocore.core.doctor import DoctorReport, format_doctor_report, run_doctor
from pyprocore.core.exceptions import (
    AuthorizationError,
    ConfigurationError,
    ProcoreAPIError,
    ResourceNotFoundError,
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
    find_rfi,
    find_specification_section,
    find_submittal,
    get_document,
    get_document_folder,
    get_drawing,
    get_drawing_area,
    get_photo,
    get_photo_album,
    get_rfi,
    get_specification_section,
    get_specification_section_revision,
    get_submittal,
    list_companies,
    list_document_folders,
    list_documents,
    list_drawing_areas,
    list_drawing_disciplines,
    list_drawings,
    list_photo_albums,
    list_photos,
    list_projects,
    list_rfis,
    list_specification_section_revisions,
    list_specification_sections,
    list_specification_sets,
    list_submittals,
)
from pyprocore.workflows import (
    ProjectSyncResult,
    SyncResult,
    export_rfis_to_csv,
    export_submittals_to_csv,
    sync_documents_to_folder,
    sync_project_to_folder,
    sync_rfis_to_folder,
    sync_submittals_to_folder,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Procore SDK utility commands")
    subcommands = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subcommands.add_parser("doctor", help="Check local SDK setup")
    doctor_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )
    doctor_parser.add_argument(
        "--live",
        action="store_true",
        help="Run one authenticated Procore API check",
    )

    auth_parser = subcommands.add_parser("auth", help="Authentication helper commands")
    auth_subcommands = auth_parser.add_subparsers(dest="auth_command", required=True)

    auth_status_parser = auth_subcommands.add_parser("status", help="Show local auth status")
    auth_status_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )

    auth_subcommands.add_parser("refresh", help="Refresh the stored access token")
    auth_subcommands.add_parser("login-url", help="Print the OAuth authorization URL")
    auth_exchange_parser = auth_subcommands.add_parser(
        "exchange-code",
        aliases=["exchange"],
        help="Exchange an OAuth authorization code and save tokens",
    )
    auth_exchange_parser.set_defaults(auth_command="exchange-code")
    auth_exchange_parser.add_argument("code", help="Authorization code returned by Procore")

    subcommands.add_parser("companies", help="List companies")

    find_company_parser = subcommands.add_parser("find-company", help="Find one company")
    find_company_parser.add_argument("name")

    projects_parser = subcommands.add_parser("projects", help="List projects")
    projects_parser.add_argument("--company-id", type=int, default=None)

    find_project_parser = subcommands.add_parser("find-project", help="Find one project")
    find_project_parser.add_argument("query", nargs="?")
    find_project_parser.add_argument("--number", default=None)
    find_project_parser.add_argument("--company-id", type=int, default=None)

    rfis_parser = subcommands.add_parser("rfis", help="List RFIs for a project")
    rfis_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    _add_filter_options(rfis_parser)

    rfi_parser = subcommands.add_parser("rfi", help="Get one RFI")
    rfi_parser.add_argument("--project", "--project-id", dest="project_id", type=int, required=True)
    rfi_parser.add_argument("--id", "--rfi-id", dest="rfi_id", type=int, required=True)

    find_rfi_parser = subcommands.add_parser("find-rfi", help="Find one RFI by number")
    find_rfi_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    find_rfi_parser.add_argument("--number", required=True)

    rfi_download_parser = _add_alias_parser(
        subcommands,
        "download-rfi",
        ["download-rfi-attachments"],
        "download-rfi-attachments",
        help="Download RFI attachments",
    )
    rfi_download_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    rfi_download_parser.add_argument("--id", "--rfi-id", dest="rfi_id", type=int, required=True)
    rfi_download_parser.add_argument("--destination-dir", type=Path, default=None)

    submittals_parser = subcommands.add_parser(
        "submittals",
        help="List submittals for a project",
    )
    submittals_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    _add_filter_options(submittals_parser)

    submittal_parser = subcommands.add_parser("submittal", help="Get one submittal")
    submittal_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    submittal_parser.add_argument(
        "--id", "--submittal-id", dest="submittal_id", type=int, required=True
    )

    find_submittal_parser = subcommands.add_parser(
        "find-submittal",
        help="Find one submittal by number",
    )
    find_submittal_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    find_submittal_parser.add_argument("--number", required=True)

    submittal_download_parser = _add_alias_parser(
        subcommands,
        "download-submittal",
        ["download-submittal-attachments"],
        "download-submittal-attachments",
        help="Download submittal attachments",
    )
    submittal_download_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    submittal_download_parser.add_argument(
        "--id", "--submittal-id", dest="submittal_id", type=int, required=True
    )
    submittal_download_parser.add_argument("--destination-dir", type=Path, default=None)

    document_folders_parser = subcommands.add_parser(
        "document-folders",
        help="List document folders for a project",
    )
    document_folders_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    document_folders_parser.add_argument("--parent", "--parent-id", dest="parent_id", type=int)
    document_folders_parser.add_argument("--company-id", type=int, default=None)

    document_folder_parser = subcommands.add_parser(
        "document-folder",
        help="Get one document folder",
    )
    document_folder_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    document_folder_parser.add_argument(
        "--id", "--folder-id", dest="folder_id", type=int, required=True
    )
    document_folder_parser.add_argument("--company-id", type=int, default=None)

    find_document_folder_parser = subcommands.add_parser(
        "find-document-folder",
        help="Find one document folder by name",
    )
    find_document_folder_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    find_document_folder_parser.add_argument("--name", required=True)

    documents_parser = subcommands.add_parser("documents", help="List documents for a project")
    documents_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    documents_parser.add_argument("--folder", "--folder-id", dest="folder_id", type=int)
    documents_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Traverse child folders discovered by the Documents API",
    )
    documents_parser.add_argument("--company-id", type=int, default=None)

    document_parser = subcommands.add_parser("document", help="Get one document")
    document_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    document_parser.add_argument(
        "--id", "--document-id", dest="document_id", type=int, required=True
    )
    document_parser.add_argument("--company-id", type=int, default=None)

    find_document_parser = subcommands.add_parser(
        "find-document",
        help="Find one document by name or filename",
    )
    find_document_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    find_document_parser.add_argument("--name", default=None)
    find_document_parser.add_argument("--filename", default=None)

    document_download_parser = subcommands.add_parser(
        "download-document",
        help="Download one document",
    )
    document_download_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    document_download_parser.add_argument(
        "--id", "--document-id", dest="document_id", type=int, required=True
    )
    document_download_parser.add_argument("--output", dest="output_dir", type=Path, default=None)
    document_download_parser.add_argument("--filename", default=None)
    document_download_parser.add_argument("--company-id", type=int, default=None)
    document_download_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the local document file if it exists",
    )

    drawing_areas_parser = subcommands.add_parser(
        "drawing-areas",
        help="List drawing areas for a project",
    )
    drawing_areas_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    drawing_areas_parser.add_argument("--company-id", type=int, default=None)

    drawing_area_parser = subcommands.add_parser(
        "drawing-area",
        help="Get one drawing area",
    )
    drawing_area_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    drawing_area_parser.add_argument(
        "--id", "--area-id", dest="drawing_area_id", type=int, required=True
    )
    drawing_area_parser.add_argument("--company-id", type=int, default=None)

    drawing_disciplines_parser = subcommands.add_parser(
        "drawing-disciplines",
        help="List drawing disciplines for a project",
    )
    drawing_disciplines_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    drawing_disciplines_parser.add_argument("--company-id", type=int, default=None)

    drawings_parser = subcommands.add_parser("drawings", help="List drawings for a project")
    drawings_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    drawings_parser.add_argument("--area", "--area-id", dest="drawing_area_id", type=int)
    drawings_parser.add_argument("--discipline", "--discipline-id", dest="discipline_id", type=int)
    drawings_parser.add_argument(
        "--current",
        action="store_true",
        default=None,
        help="Request only current drawings when supported by Procore",
    )
    drawings_parser.add_argument("--company-id", type=int, default=None)

    drawing_parser = subcommands.add_parser("drawing", help="Get one drawing")
    drawing_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    drawing_parser.add_argument("--id", "--drawing-id", dest="drawing_id", type=int, required=True)
    drawing_parser.add_argument("--area", "--area-id", dest="drawing_area_id", type=int)
    drawing_parser.add_argument("--company-id", type=int, default=None)

    find_drawing_parser = subcommands.add_parser(
        "find-drawing",
        help="Find one drawing by number or title",
    )
    find_drawing_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    find_drawing_parser.add_argument("--number", default=None)
    find_drawing_parser.add_argument("--title", default=None)
    find_drawing_parser.add_argument("--company-id", type=int, default=None)

    find_drawings_parser = subcommands.add_parser(
        "find-drawings",
        help="Find drawings containing text",
    )
    find_drawings_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    find_drawings_parser.add_argument("--contains", dest="text", required=True)
    find_drawings_parser.add_argument("--company-id", type=int, default=None)

    download_drawing_parser = subcommands.add_parser(
        "download-drawing",
        help="Download one drawing",
    )
    download_drawing_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    download_drawing_parser.add_argument(
        "--id", "--drawing-id", dest="drawing_id", type=int, required=True
    )
    download_drawing_parser.add_argument("--area", "--area-id", dest="drawing_area_id", type=int)
    download_drawing_parser.add_argument("--output", dest="output_dir", type=Path, default=None)
    download_drawing_parser.add_argument("--filename", default=None)
    download_drawing_parser.add_argument("--company-id", type=int, default=None)
    download_drawing_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the local drawing file if it exists",
    )

    photo_albums_parser = subcommands.add_parser(
        "photo-albums",
        help="List photo albums for a project",
    )
    _add_photo_project_company_options(photo_albums_parser)
    photo_albums_parser.add_argument("--page", type=int)
    photo_albums_parser.add_argument("--per-page", type=int)

    photo_album_parser = subcommands.add_parser("photo-album", help="Get one photo album")
    _add_photo_project_company_options(photo_album_parser)
    photo_album_parser.add_argument(
        "--album", "--album-id", dest="album_id", type=int, required=True
    )

    find_photo_album_parser = subcommands.add_parser(
        "find-photo-album",
        help="Find one photo album by name",
    )
    _add_photo_project_company_options(find_photo_album_parser)
    find_photo_album_parser.add_argument("--name", required=True)

    photos_parser = subcommands.add_parser("photos", help="List photos for a project or album")
    _add_photo_project_company_options(photos_parser)
    _add_photo_filter_options(photos_parser)

    photo_parser = subcommands.add_parser("photo", help="Get one photo")
    _add_photo_project_company_options(photo_parser)
    photo_parser.add_argument("--photo", "--photo-id", dest="photo_id", type=int, required=True)

    find_photo_parser = subcommands.add_parser("find-photo", help="Find one photo")
    _add_photo_project_company_options(find_photo_parser)
    find_photo_parser.add_argument("--photo", "--photo-id", dest="photo_id", type=int)
    find_photo_parser.add_argument("--filename", default=None)
    find_photo_parser.add_argument("--description", default=None)
    find_photo_parser.add_argument("--query", default=None)

    download_photo_parser = subcommands.add_parser("download-photo", help="Download one photo")
    _add_photo_project_company_options(download_photo_parser)
    download_photo_parser.add_argument(
        "--photo",
        "--photo-id",
        dest="photo_id",
        type=int,
        required=True,
    )
    download_photo_parser.add_argument("--output-dir", "--output", dest="output_dir", type=Path)
    download_photo_parser.add_argument("--filename", default=None)
    download_photo_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the local photo file if it exists",
    )

    download_photo_album_parser = subcommands.add_parser(
        "download-photo-album",
        help="Download photos from one album",
    )
    _add_photo_project_company_options(download_photo_album_parser)
    download_photo_album_parser.add_argument(
        "--album",
        "--album-id",
        dest="album_id",
        type=int,
        required=True,
    )
    download_photo_album_parser.add_argument(
        "--output-dir", "--output", dest="output_dir", type=Path
    )
    download_photo_album_parser.add_argument("--limit", type=int)
    download_photo_album_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite local photo files if they exist",
    )

    specification_sets_parser = subcommands.add_parser(
        "specification-sets",
        help="List specification sets for a project",
    )
    _add_spec_project_company_options(specification_sets_parser)

    specification_sections_parser = subcommands.add_parser(
        "specification-sections",
        help="List specification sections for a project",
    )
    _add_spec_project_company_options(specification_sections_parser)
    specification_sections_parser.add_argument("--specification-area-id", type=int)
    specification_sections_parser.add_argument("--specification-set-id", type=int)
    specification_sections_parser.add_argument("--division-id", type=int)
    specification_sections_parser.add_argument("--sort", default=None)

    specification_section_parser = subcommands.add_parser(
        "specification-section",
        help="Get one specification section",
    )
    _add_spec_project_company_options(specification_section_parser)
    specification_section_parser.add_argument(
        "--section",
        "--section-id",
        dest="specification_section_id",
        type=int,
        required=True,
    )

    find_specification_section_parser = subcommands.add_parser(
        "find-specification-section",
        help="Find one specification section by number, title, or text",
    )
    _add_spec_project_company_options(find_specification_section_parser)
    find_specification_section_parser.add_argument("--number", default=None)
    find_specification_section_parser.add_argument("--title", default=None)
    find_specification_section_parser.add_argument("--query", default=None)

    specification_revisions_parser = subcommands.add_parser(
        "specification-revisions",
        help="List specification section revisions for a project",
    )
    _add_spec_project_company_options(specification_revisions_parser)
    specification_revisions_parser.add_argument(
        "--section",
        "--section-id",
        dest="specification_section_id",
        type=int,
    )
    specification_revisions_parser.add_argument("--page", type=int)
    specification_revisions_parser.add_argument("--per-page", type=int)

    specification_revision_parser = subcommands.add_parser(
        "specification-revision",
        help="Get one specification section revision",
    )
    _add_spec_project_company_options(specification_revision_parser)
    specification_revision_parser.add_argument(
        "--revision",
        "--revision-id",
        dest="revision_id",
        type=int,
        required=True,
    )

    download_specification_revision_parser = subcommands.add_parser(
        "download-specification-revision",
        help="Download one specification section revision",
    )
    _add_spec_project_company_options(download_specification_revision_parser)
    download_specification_revision_parser.add_argument(
        "--revision",
        "--revision-id",
        dest="revision_id",
        type=int,
        required=True,
    )
    download_specification_revision_parser.add_argument(
        "--output-dir",
        "--output",
        dest="output_dir",
        type=Path,
        default=None,
    )
    download_specification_revision_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the local specification file if it exists",
    )

    package_rfi_parser = subcommands.add_parser(
        "package-rfi",
        help="Build an automation package for one RFI",
    )
    _add_package_options(package_rfi_parser)

    package_submittal_parser = subcommands.add_parser(
        "package-submittal",
        help="Build an automation package for one submittal",
    )
    _add_package_options(package_submittal_parser)

    export_rfis_parser = subcommands.add_parser(
        "export-rfis",
        help="Export project RFIs to CSV",
    )
    _add_project_output_options(export_rfis_parser, output_help="CSV output path")
    _add_filter_options(export_rfis_parser)

    export_submittals_parser = subcommands.add_parser(
        "export-submittals",
        help="Export project submittals to CSV",
    )
    _add_project_output_options(export_submittals_parser, output_help="CSV output path")
    _add_filter_options(export_submittals_parser)

    sync_rfis_parser = subcommands.add_parser(
        "sync-rfis",
        help="Sync project RFIs to a local folder",
    )
    _add_project_output_options(sync_rfis_parser, output_help="Output folder")
    _add_filter_options(sync_rfis_parser)
    _add_sync_options(sync_rfis_parser)

    sync_submittals_parser = subcommands.add_parser(
        "sync-submittals",
        help="Sync project submittals to a local folder",
    )
    _add_project_output_options(sync_submittals_parser, output_help="Output folder")
    _add_filter_options(sync_submittals_parser)
    _add_sync_options(sync_submittals_parser)

    sync_documents_parser = subcommands.add_parser(
        "sync-documents",
        help="Sync project documents to a local folder",
    )
    _add_project_output_options(sync_documents_parser, output_help="Output folder")
    sync_documents_parser.add_argument("--folder", "--folder-id", dest="folder_id", type=int)
    sync_documents_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Traverse child folders discovered by the Documents API",
    )
    sync_documents_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing downloaded documents",
    )
    sync_documents_parser.add_argument(
        "--no-tracker",
        dest="create_tracker",
        action="store_false",
        default=True,
        help="Skip tracker CSV creation",
    )
    sync_documents_parser.add_argument(
        "--no-markdown",
        dest="create_markdown",
        action="store_false",
        default=True,
        help="Skip per-document Markdown summaries",
    )
    sync_documents_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan the sync without writing files or downloading documents",
    )
    sync_documents_parser.add_argument(
        "--incremental",
        action="store_true",
        help="Skip unchanged documents using local sync state",
    )

    sync_project_parser = subcommands.add_parser(
        "sync-project",
        help="Sync project RFIs and submittals to a local folder",
    )
    _add_project_output_options(sync_project_parser, output_help="Output folder")
    _add_filter_options(sync_project_parser)
    _add_sync_options(sync_project_parser)
    sync_project_parser.add_argument(
        "--rfis-only",
        action="store_true",
        help="Sync only RFIs",
    )
    sync_project_parser.add_argument(
        "--submittals-only",
        action="store_true",
        help="Sync only submittals",
    )

    return parser


def _add_alias_parser(
    subcommands: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    aliases: list[str],
    legacy_name: str,
    **kwargs: Any,
) -> argparse.ArgumentParser:
    """Add a subcommand with aliases when supported by argparse."""
    parser = subcommands.add_parser(name, aliases=aliases, **kwargs)
    parser.set_defaults(command=name, legacy_command=legacy_name)
    return parser


def _add_package_options(parser: argparse.ArgumentParser) -> None:
    """Add shared automation package command options."""
    parser.add_argument("--company", dest="company_id", type=int, default=None)
    parser.add_argument("--project", "--project-id", dest="project_id", type=int, default=None)
    parser.add_argument("--project-name", default=None)
    parser.add_argument("--project-number", default=None)
    parser.add_argument("--id", dest="item_id", type=int, default=None)
    parser.add_argument("--number", dest="item_number", default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--no-downloads",
        dest="download_attachments",
        action="store_false",
        default=True,
    )


def _add_filter_options(parser: argparse.ArgumentParser) -> None:
    """Add shared list filter options."""
    parser.add_argument("--status", default=None)
    parser.add_argument("--updated-after", default=None)
    parser.add_argument("--updated-before", default=None)
    parser.add_argument("--created-after", default=None)
    parser.add_argument("--created-before", default=None)


def _add_spec_project_company_options(parser: argparse.ArgumentParser) -> None:
    """Add shared Specifications command options."""
    parser.add_argument("--project", "--project-id", dest="project_id", type=int, required=True)
    parser.add_argument("--company-id", "--company", dest="company_id", type=int, default=None)


def _add_photo_project_company_options(parser: argparse.ArgumentParser) -> None:
    """Add shared Photos command options."""
    parser.add_argument("--project", "--project-id", dest="project_id", type=int, required=True)
    parser.add_argument("--company-id", "--company", dest="company_id", type=int, default=None)


def _add_photo_filter_options(parser: argparse.ArgumentParser) -> None:
    """Add shared Photos list filter options."""
    parser.add_argument("--album", "--album-id", dest="album_id", type=int)
    parser.add_argument("--image-category-id", type=int)
    parser.add_argument("--private", action="store_true", default=None)
    parser.add_argument("--starred", action="store_true", default=None)
    parser.add_argument("--created-at", default=None)
    parser.add_argument("--updated-at", default=None)
    parser.add_argument("--log-date", default=None)
    parser.add_argument("--query", default=None)
    parser.add_argument("--uploader-id", dest="uploader_ids", type=int, action="append")
    parser.add_argument("--location-id", dest="location_ids", type=int, action="append")
    parser.add_argument("--trade-id", dest="trade_ids", type=int, action="append")
    parser.add_argument("--projection", default=None)
    parser.add_argument("--serializer-view", default=None)
    parser.add_argument("--sort", default=None)
    parser.add_argument("--page", type=int)
    parser.add_argument("--per-page", type=int)


def _add_project_output_options(parser: argparse.ArgumentParser, *, output_help: str) -> None:
    """Add shared project and output options."""
    parser.add_argument("--project", "--project-id", dest="project_id", type=int, required=True)
    parser.add_argument("--output", dest="output_path", type=Path, required=True, help=output_help)


def _add_sync_options(parser: argparse.ArgumentParser) -> None:
    """Add shared local folder sync options."""
    parser.add_argument(
        "--no-attachments",
        dest="download_attachments",
        action="store_false",
        default=True,
        help="Skip attachment downloads",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing downloaded attachments",
    )
    parser.add_argument(
        "--no-tracker",
        dest="create_tracker",
        action="store_false",
        default=True,
        help="Skip tracker CSV creation",
    )
    parser.add_argument(
        "--no-markdown",
        dest="create_markdown",
        action="store_false",
        default=True,
        help="Skip per-item Markdown summaries",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan the sync without writing files or downloading attachments",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Skip unchanged items using local sync state",
    )


def run_command(args: argparse.Namespace) -> Any:
    """Run a parsed CLI command and return serializable output."""
    if args.command == "doctor":
        return run_doctor(live=args.live)

    if args.command == "auth":
        if args.auth_command == "status":
            return get_auth_status()
        if args.auth_command == "refresh":
            return refresh_auth_token()
        if args.auth_command == "login-url":
            return build_authorization_url()
        if args.auth_command == "exchange-code":
            return exchange_code_and_save(args.code)
        raise ValueError(f"Unsupported auth command: {args.auth_command}")

    if args.command == "companies":
        return list_companies()

    if args.command == "find-company":
        return find_company(args.name)

    if args.command == "projects":
        company_id = args.company_id or get_settings().company_id
        return list_projects(company_id)

    if args.command == "find-project":
        return find_project(args.query, number=args.number, company_id=args.company_id)

    if args.command == "rfis":
        return list_rfis(
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "rfi":
        return get_rfi(args.project_id, args.rfi_id)

    if args.command == "find-rfi":
        return find_rfi(args.project_id, number=args.number)

    if args.command == "download-rfi":
        return [
            str(path)
            for path in download_rfi_attachments(
                args.project_id,
                args.rfi_id,
                args.destination_dir,
            )
        ]

    if args.command == "submittals":
        return list_submittals(
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "submittal":
        return get_submittal(args.project_id, args.submittal_id)

    if args.command == "find-submittal":
        return find_submittal(args.project_id, number=args.number)

    if args.command == "download-submittal":
        return [
            str(path)
            for path in download_submittal_attachments(
                args.project_id,
                args.submittal_id,
                args.destination_dir,
            )
        ]

    if args.command == "document-folders":
        return list_document_folders(
            args.project_id,
            parent_id=args.parent_id,
            company_id=args.company_id,
        )

    if args.command == "document-folder":
        return get_document_folder(
            args.project_id,
            args.folder_id,
            company_id=args.company_id,
        )

    if args.command == "find-document-folder":
        return find_document_folder(args.project_id, args.name)

    if args.command == "documents":
        return list_documents(
            args.project_id,
            folder_id=args.folder_id,
            recursive=args.recursive,
            company_id=args.company_id,
        )

    if args.command == "document":
        return get_document(args.project_id, args.document_id, company_id=args.company_id)

    if args.command == "find-document":
        return find_document(args.project_id, name=args.name, filename=args.filename)

    if args.command == "download-document":
        output_dir = args.output_dir if args.output_dir is not None else "downloads/documents"
        return download_document(
            args.project_id,
            args.document_id,
            output_dir=output_dir,
            filename=args.filename,
            company_id=args.company_id,
            overwrite=args.overwrite,
        )

    if args.command == "drawing-areas":
        return list_drawing_areas(args.project_id, company_id=args.company_id)

    if args.command == "drawing-area":
        return get_drawing_area(
            args.project_id,
            args.drawing_area_id,
            company_id=args.company_id,
        )

    if args.command == "drawing-disciplines":
        return list_drawing_disciplines(args.project_id, company_id=args.company_id)

    if args.command == "drawings":
        return list_drawings(
            args.project_id,
            company_id=args.company_id,
            drawing_area_id=args.drawing_area_id,
            discipline_id=args.discipline_id,
            current=args.current,
        )

    if args.command == "drawing":
        return get_drawing(
            args.project_id,
            args.drawing_id,
            company_id=args.company_id,
            drawing_area_id=args.drawing_area_id,
        )

    if args.command == "find-drawing":
        return find_drawing(
            args.project_id,
            number=args.number,
            title=args.title,
            company_id=args.company_id,
        )

    if args.command == "find-drawings":
        return find_drawings_contains(args.project_id, args.text, company_id=args.company_id)

    if args.command == "download-drawing":
        output_dir = args.output_dir if args.output_dir is not None else "downloads/drawings"
        return download_drawing(
            args.project_id,
            args.drawing_id,
            output_dir=output_dir,
            filename=args.filename,
            company_id=args.company_id,
            overwrite=args.overwrite,
            drawing_area_id=args.drawing_area_id,
        )

    if args.command == "photo-albums":
        return list_photo_albums(
            args.project_id,
            company_id=args.company_id,
            page=args.page,
            per_page=args.per_page,
        )

    if args.command == "photo-album":
        return get_photo_album(args.project_id, args.album_id, company_id=args.company_id)

    if args.command == "find-photo-album":
        return find_photo_album(args.project_id, name=args.name, company_id=args.company_id)

    if args.command == "photos":
        return list_photos(
            args.project_id,
            company_id=args.company_id,
            album_id=args.album_id,
            image_category_id=args.image_category_id,
            private=args.private,
            starred=args.starred,
            created_at=args.created_at,
            updated_at=args.updated_at,
            log_date=args.log_date,
            query=args.query,
            uploader_ids=args.uploader_ids,
            location_ids=args.location_ids,
            trade_ids=args.trade_ids,
            projection=args.projection,
            serializer_view=args.serializer_view,
            sort=args.sort,
            page=args.page,
            per_page=args.per_page,
        )

    if args.command == "photo":
        return get_photo(args.project_id, args.photo_id, company_id=args.company_id)

    if args.command == "find-photo":
        return find_photo(
            args.project_id,
            photo_id=args.photo_id,
            filename=args.filename,
            description=args.description,
            query=args.query,
            company_id=args.company_id,
        )

    if args.command == "download-photo":
        output_dir = args.output_dir if args.output_dir is not None else "downloads/photos"
        return download_photo(
            args.project_id,
            args.photo_id,
            output_dir=output_dir,
            company_id=args.company_id,
            overwrite=args.overwrite,
            filename=args.filename,
        )

    if args.command == "download-photo-album":
        output_dir = args.output_dir if args.output_dir is not None else "downloads/photos"
        return download_photo_album(
            args.project_id,
            args.album_id,
            output_dir=output_dir,
            company_id=args.company_id,
            overwrite=args.overwrite,
            limit=args.limit,
        )

    if args.command == "specification-sets":
        return list_specification_sets(args.project_id, company_id=args.company_id)

    if args.command == "specification-sections":
        return list_specification_sections(
            args.project_id,
            company_id=args.company_id,
            specification_area_id=args.specification_area_id,
            specification_set_id=args.specification_set_id,
            division_id=args.division_id,
            sort=args.sort,
        )

    if args.command == "specification-section":
        return get_specification_section(
            args.project_id,
            args.specification_section_id,
            company_id=args.company_id,
        )

    if args.command == "find-specification-section":
        return find_specification_section(
            args.project_id,
            number=args.number,
            title=args.title,
            query=args.query,
            company_id=args.company_id,
        )

    if args.command == "specification-revisions":
        return list_specification_section_revisions(
            args.project_id,
            company_id=args.company_id,
            specification_section_id=args.specification_section_id,
            page=args.page,
            per_page=args.per_page,
        )

    if args.command == "specification-revision":
        return get_specification_section_revision(
            args.project_id,
            args.revision_id,
            company_id=args.company_id,
        )

    if args.command == "download-specification-revision":
        output_dir = args.output_dir if args.output_dir is not None else "downloads/specifications"
        return download_specification_section_revision(
            args.project_id,
            args.revision_id,
            output_dir=output_dir,
            company_id=args.company_id,
            overwrite=args.overwrite,
        )

    if args.command == "package-rfi":
        return build_workflow_package(_automation_input(args, item_type="rfi"))

    if args.command == "package-submittal":
        return build_workflow_package(_automation_input(args, item_type="submittal"))

    if args.command == "export-rfis":
        return export_rfis_to_csv(
            args.project_id,
            args.output_path,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "export-submittals":
        return export_submittals_to_csv(
            args.project_id,
            args.output_path,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "sync-rfis":
        return sync_rfis_to_folder(
            args.project_id,
            args.output_path,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
            download_attachments=args.download_attachments,
            overwrite=args.overwrite,
            create_tracker=args.create_tracker,
            create_markdown=args.create_markdown,
            dry_run=args.dry_run,
            incremental=getattr(args, "incremental", False),
        )

    if args.command == "sync-submittals":
        return sync_submittals_to_folder(
            args.project_id,
            args.output_path,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
            download_attachments=args.download_attachments,
            overwrite=args.overwrite,
            create_tracker=args.create_tracker,
            create_markdown=args.create_markdown,
            dry_run=args.dry_run,
            incremental=getattr(args, "incremental", False),
        )

    if args.command == "sync-documents":
        return sync_documents_to_folder(
            args.project_id,
            args.output_path,
            folder_id=args.folder_id,
            recursive=args.recursive,
            overwrite=args.overwrite,
            create_tracker=args.create_tracker,
            create_markdown=args.create_markdown,
            dry_run=args.dry_run,
            incremental=args.incremental,
        )

    if args.command == "sync-project":
        if args.rfis_only and args.submittals_only:
            raise ValueError("Use either --rfis-only or --submittals-only, not both.")
        return sync_project_to_folder(
            args.project_id,
            args.output_path,
            include_rfis=not args.submittals_only,
            include_submittals=not args.rfis_only,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
            download_attachments=args.download_attachments,
            overwrite=args.overwrite,
            create_tracker=args.create_tracker,
            create_markdown=args.create_markdown,
            dry_run=args.dry_run,
            incremental=args.incremental,
        )

    raise ValueError(f"Unsupported command: {args.command}")


def _automation_input(
    args: argparse.Namespace,
    *,
    item_type: Literal["rfi", "submittal"],
) -> AutomationInput:
    """Build automation workflow input from CLI arguments."""
    return AutomationInput(
        company_id=args.company_id,
        project_id=args.project_id,
        project_name=args.project_name,
        project_number=args.project_number,
        item_type=item_type,
        item_id=args.item_id,
        item_number=args.item_number,
        download_attachments=args.download_attachments,
        output_dir=args.output_dir,
    )


def to_serializable(value: Any) -> Any:
    """Convert SDK output into JSON-serializable data."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [to_serializable(item) for item in value]
    if isinstance(value, tuple):
        return [to_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_serializable(item) for key, item in value.items()}
    if isinstance(value, Path):
        return str(value)
    return value


def format_export_summary(path: Path) -> str:
    """Return a human-readable export summary."""
    return f"Export complete.\nOutput: {path}"


def format_sync_summary(result: SyncResult) -> str:
    """Return a human-readable folder sync summary."""
    action = "planned" if result.dry_run else "complete"
    item_word = "planned" if result.dry_run else "synced"
    lines = [
        f"{result.item_type.upper()} sync {action}.",
        f"Project: {result.project_id}",
        f"Items {item_word}: {result.item_count}",
        f"Output: {result.output_dir}",
    ]
    if result.tracker_path is not None:
        tracker_label = "Tracker (planned)" if result.dry_run else "Tracker"
        lines.append(f"{tracker_label}: {result.tracker_path}")
    if result.manifest_path is not None:
        lines.append(f"Manifest: {result.manifest_path}")
    elif result.dry_run:
        lines.append("Manifest: not written during dry run")
    lines.append(f"Attachments downloaded: {len(result.downloaded_files)}")
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in result.warnings)
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in result.errors)
    return "\n".join(lines)


def format_project_sync_summary(result: ProjectSyncResult) -> str:
    """Return a human-readable project sync summary."""
    action = "planned" if result.dry_run else "complete"
    return "\n".join(
        [
            f"Project sync {action}.",
            f"Project: {result.project_id}",
            f"Items synced: {result.synced_count}",
            f"Items skipped: {result.skipped_count}",
            f"Output: {result.output_dir}",
            f"Manifest: {result.manifest_path or 'not written during dry run'}",
            f"Summary: {result.summary_path or 'not written during dry run'}",
            f"Warnings: {result.warning_count}",
            f"Errors: {result.error_count}",
        ]
    )


def main() -> None:
    """Run the CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run_command(args)
    except ConfigurationError as exc:
        print(format_configuration_error(exc))
        raise SystemExit(1) from exc
    except (AuthorizationError, ResourceNotFoundError, ProcoreAPIError) as exc:
        print(format_cli_error(exc))
        raise SystemExit(1) from exc
    if isinstance(result, DoctorReport):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_doctor_report(result))
        raise SystemExit(result.exit_code)

    if isinstance(result, AuthStatusReport):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_auth_status(result))
        raise SystemExit(result.exit_code)

    if isinstance(result, AuthRefreshResult):
        print(format_auth_refresh(result))
        raise SystemExit(result.exit_code)

    if isinstance(result, AuthExchangeResult):
        print(format_auth_exchange(result))
        raise SystemExit(result.exit_code)

    if isinstance(result, AuthLoginUrlResult):
        print(format_login_url(result))
        raise SystemExit(0)

    if isinstance(result, SyncResult):
        print(format_sync_summary(result))
        return

    if isinstance(result, ProjectSyncResult):
        print(format_project_sync_summary(result))
        return

    if isinstance(result, Path) and args.command in {"export-rfis", "export-submittals"}:
        print(format_export_summary(result))
        return

    if isinstance(result, Path) and args.command in {
        "download-document",
        "download-drawing",
        "download-photo",
        "download-specification-revision",
    }:
        print(f"Download complete.\nOutput: {result}")
        return

    print(json.dumps(to_serializable(result), indent=2, default=str))


def _main() -> int:
    """Run the CLI entrypoint and return an operating-system exit code."""
    main()
    return 0


def format_configuration_error(exc: ConfigurationError) -> str:
    """Format configuration errors without exposing secrets."""
    return "\n".join(
        [
            "PyProcore configuration is missing or invalid.",
            "",
            "Next steps:",
            "1. Confirm `.env` exists in your current working directory.",
            "2. Run `procore-sdk doctor` to inspect local setup.",
            "3. Fill in the required Procore OAuth settings.",
            "4. Run this command again.",
            "",
            "Required values:",
            "- PROCORE_CLIENT_ID",
            "- PROCORE_CLIENT_SECRET",
            "- PROCORE_REDIRECT_URI",
            "- PROCORE_LOGIN_URL",
            "- PROCORE_API_BASE",
            "- PROCORE_COMPANY_ID",
            "",
            f"Details: {exc}",
        ]
    )


def format_cli_error(exc: AuthorizationError | ResourceNotFoundError | ProcoreAPIError) -> str:
    """Format common SDK errors for safe CLI output."""
    if isinstance(exc, AuthorizationError):
        return format_authorization_error(exc)
    if isinstance(exc, ProcoreAPIError) and exc.status_code == 403:
        return format_authorization_error(exc)
    if isinstance(exc, ResourceNotFoundError):
        return format_not_found_error(exc)
    return format_procore_api_error(exc)


def format_authorization_error(exc: AuthorizationError | ProcoreAPIError) -> str:
    """Format Procore authorization failures without a traceback."""
    if _is_app_not_connected_error(exc):
        return "\n".join(
            [
                "Procore rejected this request.",
                "Reason:",
                "Your OAuth app is not connected to this Procore company.",
                "",
                "Suggested fixes:",
                "- Run `procore-sdk companies` to see companies available to this token",
                "- Confirm the company ID is correct",
                "- Connect/install the OAuth app to that Procore company",
                "- Confirm the OAuth user has access to the company/project",
                "- Confirm production vs sandbox environment",
                "- Try again after reconnecting the app",
            ]
        )

    return "\n".join(
        [
            "Procore rejected this request.",
            "Reason:",
            "Your token is valid, but Procore denied access to this resource.",
            "",
            "Suggested fixes:",
            "- Confirm company_id/project_id are correct",
            "- Confirm the OAuth user has permission",
            "- Confirm the app is connected to the company",
            "- Confirm production vs sandbox environment",
        ]
    )


def format_not_found_error(exc: ResourceNotFoundError) -> str:
    """Format not-found API errors without a traceback."""
    return "\n".join(
        [
            "Procore could not find this resource.",
            "Reason:",
            "The requested company, project, or resource was not found.",
            "",
            "Suggested fixes:",
            "- Confirm the ID values are correct",
            "- Confirm production vs sandbox environment",
            "- Confirm the OAuth user has access to the resource",
            "",
            f"Details: {exc}",
        ]
    )


def format_procore_api_error(exc: ProcoreAPIError) -> str:
    """Format generic Procore API errors without a traceback."""
    status = f"HTTP status: {exc.status_code}" if exc.status_code is not None else None
    lines = [
        "Procore API request failed.",
        "Reason:",
        "Procore returned an error for this request.",
    ]
    if status is not None:
        lines.extend(["", status])
    lines.extend(["", f"Details: {exc}"])
    return "\n".join(lines)


def _is_app_not_connected_error(exc: AuthorizationError | ProcoreAPIError) -> bool:
    """Return whether Procore reported a disconnected OAuth app."""
    return "app is not connected to this company" in _error_text(exc).casefold()


def _error_text(exc: AuthorizationError | ProcoreAPIError) -> str:
    """Return searchable error text from an SDK exception."""
    parts = [str(exc)]
    if isinstance(exc, ProcoreAPIError) and exc.response_body is not None:
        parts.append(json.dumps(exc.response_body, default=str))
    return " ".join(parts)


if __name__ == "__main__":
    raise SystemExit(_main())
