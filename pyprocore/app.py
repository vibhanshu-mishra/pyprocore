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
from pyprocore.services import (
    download_rfi_attachments,
    download_submittal_attachments,
    find_company,
    find_project,
    find_rfi,
    find_submittal,
    get_rfi,
    get_submittal,
    list_companies,
    list_projects,
    list_rfis,
    list_submittals,
)
from pyprocore.workflows import (
    ProjectSyncResult,
    SyncResult,
    export_rfis_to_csv,
    export_submittals_to_csv,
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
    result = run_command(args)
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

    print(json.dumps(to_serializable(result), indent=2, default=str))


if __name__ == "__main__":
    main()
