"""Command-line entrypoint for Procore SDK operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from pyprocore.core.config import get_settings
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


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Procore SDK utility commands")
    subcommands = parser.add_subparsers(dest="command", required=True)

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


def run_command(args: argparse.Namespace) -> Any:
    """Run a parsed CLI command and return serializable output."""
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
        return list_rfis(args.project_id)

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
        return list_submittals(args.project_id)

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

    raise ValueError(f"Unsupported command: {args.command}")


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


def main() -> None:
    """Run the CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()
    result = run_command(args)
    print(json.dumps(to_serializable(result), indent=2, default=str))


if __name__ == "__main__":
    main()
