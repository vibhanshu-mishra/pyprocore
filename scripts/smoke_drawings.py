"""Manually inspect Procore Drawings endpoint responses.

This script is intentionally not used by unit tests or CI. It makes live
Procore API calls only when a developer runs it manually with valid sandbox
credentials.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from typing import Any

import pyprocore
from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ProcoreAPIError,
)

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
    parser = argparse.ArgumentParser(description="Smoke-test Procore Drawings endpoints")
    parser.add_argument(
        "--project",
        "--project-id",
        dest="project_id",
        type=int,
        default=_env_int("PROCORE_PROJECT_ID"),
        help="Procore project ID. Defaults to PROCORE_PROJECT_ID.",
    )
    parser.add_argument(
        "--company-id",
        type=int,
        default=_env_int("PROCORE_COMPANY_ID"),
        help="Optional Procore company ID sent as Procore-Company-Id.",
    )
    parser.add_argument(
        "--area",
        "--area-id",
        dest="drawing_area_id",
        type=int,
        default=_env_int("PROCORE_DRAWING_AREA_ID"),
        help="Optional drawing area ID to filter drawings.",
    )
    parser.add_argument(
        "--drawing",
        "--drawing-id",
        dest="drawing_id",
        type=int,
        default=_env_int("PROCORE_DRAWING_ID"),
        help="Optional drawing ID to inspect.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print local SDK import and endpoint details without secrets.",
    )
    return parser


def main() -> int:
    """Run the manual Drawings smoke test."""
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
        _print_auth_error("authorization", exc)
        return 1
    except ProcoreAPIError as exc:
        _print_api_error(exc)
        return 1
    except Exception as exc:  # pragma: no cover - defensive manual smoke guard
        print("Drawings smoke test failed unexpectedly.")
        print(f"Reason: {type(exc).__name__}: {exc}")
        print("\nRun again with --verbose, then check `procore-sdk doctor`.")
        return 1


def _run(args: argparse.Namespace) -> int:
    """Run the manual Drawings smoke test implementation."""
    if args.project_id is None:
        print("Set PROCORE_PROJECT_ID or pass --project before running this smoke test.")
        return 1

    if args.verbose:
        _print_verbose_details(args)

    client = ProcoreClient()
    headers = _company_headers(args.company_id)
    params: dict[str, object] = {"project_id": args.project_id}
    if args.drawing_area_id is not None:
        params["drawing_area_id"] = args.drawing_area_id

    print("Request: GET /rest/v1.0/drawing_areas")
    print(f"Params: {_safe_json({'project_id': args.project_id})}")
    areas = client.get_all(
        endpoints.drawing_areas(args.project_id),
        params={"project_id": args.project_id},
        headers=headers,
    )
    print("Drawing areas sample:")
    print(_safe_json(_sample(areas)))

    print("\nRequest: GET /rest/v1.0/drawing_disciplines")
    disciplines = client.get_all(
        endpoints.drawing_disciplines(args.project_id),
        params={"project_id": args.project_id},
        headers=headers,
    )
    print("Drawing disciplines sample:")
    print(_safe_json(_sample(disciplines)))

    print("\nRequest: GET /rest/v1.0/drawings")
    print(f"Params: {_safe_json(params)}")
    drawings = client.get_all(endpoints.drawings(args.project_id), params=params, headers=headers)
    print("Drawings sample:")
    print(_safe_json(_sample(drawings)))

    if args.drawing_id is not None:
        print(f"\nRequest: GET /rest/v1.0/drawings/{args.drawing_id}")
        drawing = client.get(
            endpoints.drawing(args.project_id, args.drawing_id),
            params={"project_id": args.project_id},
            headers=headers,
        )
        print("Drawing response sample:")
        print(_safe_json(drawing))

    print("\nReview the payload for drawing numbers, titles, url, or download_url fields.")
    return 0


def _print_configuration_error(exc: ConfigurationError) -> None:
    """Print a beginner-friendly configuration failure."""
    print("Drawings smoke test cannot run yet.")
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
    """Print a beginner-friendly authentication or authorization failure."""
    print("Drawings smoke test could not authenticate with Procore.")
    print(f"\nReason: Procore {kind} failed.")
    print(f"Details: {exc}")
    print("\nNext steps:")
    print("1. Run `procore-sdk auth status`")
    print("2. If needed, run `procore-sdk auth refresh`")
    print("3. Confirm your Procore user can access this company's Drawings tool")


def _print_api_error(exc: ProcoreAPIError) -> None:
    """Print a safe summary of a Procore API failure."""
    print("Drawings smoke test reached Procore, but the API returned an error.")
    print(f"\nReason: {type(exc).__name__}")
    print(f"Details: {exc}")
    print("\nNext steps:")
    print("1. Confirm PROCORE_PROJECT_ID is correct")
    print("2. Confirm your user has access to the project's Drawings tool")
    print("3. If filtering by area or drawing, confirm those IDs are correct")


def _print_verbose_details(args: argparse.Namespace) -> None:
    """Print non-secret local runtime details."""
    print("Verbose diagnostics:")
    print(f"- Imported pyprocore from: {pyprocore.__file__}")
    print(f"- Project ID: {args.project_id}")
    print(f"- Drawing area ID: {args.drawing_area_id or '<not set>'}")
    print(f"- Drawing ID: {args.drawing_id or '<not set>'}")
    print(f"- Company header: {'set' if args.company_id is not None else '<not set>'}")
    print(f"- Areas endpoint: {endpoints.drawing_areas(args.project_id or 0)}")
    print(f"- Disciplines endpoint: {endpoints.drawing_disciplines(args.project_id or 0)}")
    print(f"- Drawings endpoint: {endpoints.drawings(args.project_id or 0)}")
    if args.drawing_id is not None:
        print(f"- Drawing endpoint: {endpoints.drawing(args.project_id or 0, args.drawing_id)}")
    print()


def _company_headers(company_id: int | None) -> dict[str, str] | None:
    """Return optional company header for Drawings endpoints."""
    if company_id is None:
        return None
    return {"Procore-Company-Id": str(company_id)}


def _env_int(name: str) -> int | None:
    """Read an optional integer environment variable."""
    value = os.getenv(name)
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


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
