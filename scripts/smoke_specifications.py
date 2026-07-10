"""Manually inspect Procore Specifications endpoint responses.

This script is intentionally not used by unit tests or CI. It makes live
Procore API calls only when a developer runs it manually with valid sandbox
or production credentials.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pyprocore
from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ProcoreAPIError,
    ValidationError,
)
from pyprocore.services.specifications import SpecificationsService

REQUIRED_CONFIG = (
    "PROCORE_CLIENT_ID",
    "PROCORE_CLIENT_SECRET",
    "PROCORE_REDIRECT_URI",
    "PROCORE_LOGIN_URL",
    "PROCORE_API_BASE",
    "PROCORE_COMPANY_ID",
)


def build_parser() -> argparse.ArgumentParser:
    """Build the smoke-test command parser."""
    parser = argparse.ArgumentParser(description="Smoke-test Procore Specifications endpoints")
    parser.add_argument(
        "--project",
        "--project-id",
        dest="project_id",
        type=int,
        default=_env_int("PROCORE_PROJECT_ID"),
        help="Procore project ID. Defaults to PROCORE_PROJECT_ID.",
    )
    parser.add_argument(
        "--company",
        "--company-id",
        dest="company_id",
        type=int,
        default=_env_int("PROCORE_COMPANY_ID"),
        help="Procore company ID. Defaults to PROCORE_COMPANY_ID.",
    )
    parser.add_argument(
        "--section",
        "--section-id",
        dest="specification_section_id",
        type=int,
        default=_env_int("PROCORE_SPECIFICATION_SECTION_ID"),
        help="Optional specification section ID to inspect.",
    )
    parser.add_argument(
        "--revision",
        "--revision-id",
        dest="revision_id",
        type=int,
        default=_env_int("PROCORE_SPECIFICATION_REVISION_ID"),
        help="Optional specification revision ID to inspect.",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download --revision to --output-dir. Downloads are off by default.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("downloads/specifications"),
        help="Folder used only when --download is passed.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print local SDK import and endpoint details without secrets.",
    )
    return parser


def main() -> int:
    """Run the manual Specifications smoke test."""
    args = build_parser().parse_args()
    try:
        return _run(args)
    except ConfigurationError as exc:
        _print_configuration_error(exc)
        return 1
    except AuthenticationError as exc:
        _print_auth_error("authentication", exc)
        return 1
    except AuthorizationError as exc:
        _print_context_rejected_error(exc)
        return 1
    except ProcoreAPIError as exc:
        _print_api_error(exc)
        return 1
    except ValidationError as exc:
        print("Specifications smoke test could not continue.")
        print(f"\nReason: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive manual smoke guard
        print("Specifications smoke test failed unexpectedly.")
        print(f"Reason: {type(exc).__name__}: {exc}")
        print("\nRun again with --verbose, then check `procore-sdk doctor`.")
        return 1


def _run(args: argparse.Namespace) -> int:
    """Run the manual Specifications smoke test implementation."""
    if args.project_id is None:
        print("Set PROCORE_PROJECT_ID or pass --project before running this smoke test.")
        return 1
    if args.company_id is None:
        print("Set PROCORE_COMPANY_ID or pass --company before running this smoke test.")
        return 1

    if args.verbose:
        _print_verbose_details(args)

    client = ProcoreClient()
    service = SpecificationsService(client=client)
    headers = {"Procore-Company-Id": str(args.company_id)}

    print(
        "Request: GET "
        f"/rest/v2.0/companies/{args.company_id}/projects/{args.project_id}"
        "/specification_sets"
    )
    sets = client.get_all(
        endpoints.specification_sets(args.company_id, args.project_id),
        headers=headers,
    )
    print("Specification sets sample:")
    print(_safe_json(_sample(_items(sets))))

    print(
        "\nRequest: GET "
        f"/rest/v2.1/companies/{args.company_id}/projects/{args.project_id}"
        "/specification_sections"
    )
    sections = service.list_specification_sections(args.project_id, company_id=args.company_id)
    print("Specification sections sample:")
    print(_safe_json(_sample([section.model_dump(mode="json") for section in sections])))
    if not sections:
        print(
            "\nNo specification sections found. Confirm the Specifications tool is enabled "
            "and the user has access."
        )
        return 1

    if args.specification_section_id is not None:
        print(f"\nInspecting specification section ID: {args.specification_section_id}")
        section = service.get_specification_section(
            args.project_id,
            args.specification_section_id,
            company_id=args.company_id,
        )
        print(_safe_json(section.model_dump(mode="json")))

    print(
        "\nRequest: GET "
        f"/rest/v2.1/companies/{args.company_id}/projects/{args.project_id}"
        "/specification_section_revisions"
    )
    revisions = service.list_specification_section_revisions(
        args.project_id,
        company_id=args.company_id,
        specification_section_id=args.specification_section_id,
        per_page=1000,
    )
    print("Specification revisions sample:")
    print(_safe_json(_sample([revision.model_dump(mode="json") for revision in revisions])))

    if args.revision_id is not None:
        print(f"\nInspecting specification revision ID: {args.revision_id}")
        revision = service.get_specification_section_revision(
            args.project_id,
            args.revision_id,
            company_id=args.company_id,
        )
        print(_safe_json(revision.model_dump(mode="json")))
        if args.download:
            saved_path = service.download_specification_section_revision(
                args.project_id,
                args.revision_id,
                output_dir=args.output_dir,
                company_id=args.company_id,
            )
            print(f"\nDownload complete: {saved_path}")
    elif args.download:
        print("\nPass --revision before using --download.")
        return 1

    print("\nReview the payload for section numbers, titles, revisions, and download URLs.")
    return 0


def _print_configuration_error(exc: ConfigurationError) -> None:
    """Print a beginner-friendly configuration failure."""
    print("Specifications smoke test cannot run yet.")
    print("\nReason:")
    print("PyProcore configuration is missing or invalid.")
    if str(exc):
        print(f"\nDetails: {exc}")
    print("\nNext steps:")
    print("1. Run `procore-sdk doctor`")
    print("2. Fill in `.env` with your Procore OAuth settings")
    print("3. Run `procore-sdk auth login-url`")
    print("4. Run `procore-sdk auth exchange-code YOUR_AUTHORIZATION_CODE`")
    print("5. Run this smoke test again")
    print("\nRequired values:")
    for name in REQUIRED_CONFIG:
        print(f"- {name}")


def _print_auth_error(kind: str, exc: Exception) -> None:
    """Print a beginner-friendly authentication failure."""
    print("Specifications smoke test could not authenticate with Procore.")
    print(f"\nReason: Procore {kind} failed.")
    print(f"Details: {exc}")
    print("\nNext steps:")
    print("1. Run `procore-sdk auth status`")
    print("2. If needed, run `procore-sdk auth refresh`")
    print("3. Confirm your Procore user can access this company's Specifications tool")


def _print_context_rejected_error(exc: AuthorizationError) -> None:
    """Print a beginner-friendly project/company authorization failure."""
    print("Authenticated successfully, but Procore rejected the project/company context.")
    print(f"\nDetails: {exc}")
    print("\nNext steps:")
    print("1. Confirm project_id belongs to company_id")
    print("2. Confirm production vs sandbox environment")
    print("3. Confirm the OAuth user has access to the company/project")
    print("4. Confirm the Specifications tool is enabled for the project")
    print("5. Confirm the user has permission to view Specifications")


def _print_api_error(exc: ProcoreAPIError) -> None:
    """Print a safe summary of a Procore API failure."""
    print("Specifications smoke test reached Procore, but the API returned an error.")
    print(f"\nReason: {type(exc).__name__}")
    print(f"Details: {exc}")
    print("\nNext steps:")
    print("1. Confirm PROCORE_PROJECT_ID and PROCORE_COMPANY_ID are correct")
    print("2. Confirm production vs sandbox environment")
    print("3. Confirm your user has access to the project's Specifications tool")
    print("4. For 404s, confirm the Specifications tool is enabled and sections exist")


def _print_verbose_details(args: argparse.Namespace) -> None:
    """Print non-secret local runtime details."""
    print("Verbose diagnostics:")
    print(f"- Imported pyprocore from: {pyprocore.__file__}")
    print(f"- Project ID: {args.project_id}")
    print(f"- Company ID: {args.company_id}")
    print(f"- Specification section ID: {args.specification_section_id or '<not set>'}")
    print(f"- Specification revision ID: {args.revision_id or '<not set>'}")
    company_id = args.company_id or 0
    project_id = args.project_id or 0
    print(f"- Sets endpoint: {endpoints.specification_sets(company_id, project_id)}")
    print(f"- Sections endpoint: {endpoints.specification_sections(company_id, project_id)}")
    print(
        "- Revisions endpoint: "
        f"{endpoints.specification_section_revisions(company_id, project_id)}"
    )
    if args.revision_id is not None:
        print(
            "- Revision endpoint: "
            f"{endpoints.specification_section_revision(company_id, project_id, args.revision_id)}"
        )
    print()


def _env_int(name: str) -> int | None:
    """Read an optional integer environment variable."""
    value = os.getenv(name)
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _items(value: object) -> list[object]:
    """Extract display items from a direct or V2-envelope response."""
    if isinstance(value, list):
        return value
    if isinstance(value, Mapping):
        data = value.get("data")
        if isinstance(data, list):
            return data
    return [value]


def _sample(value: object) -> object:
    """Return a small payload sample for terminal output."""
    if isinstance(value, list):
        return value[:3]
    return value


def _safe_json(value: object) -> str:
    """Serialize output without exposing auth headers or secrets."""
    return json.dumps(_redact(value), indent=2, default=str, sort_keys=True)


def _redact(value: object) -> object:
    """Redact common secret-like keys from nested output."""
    if isinstance(value, Mapping):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).casefold() in {
                "authorization",
                "access_token",
                "refresh_token",
                "client_secret",
            }:
                redacted[str(key)] = "<redacted>"
            else:
                redacted[str(key)] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
