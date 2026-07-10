"""Manually inspect Procore Documents folder/file endpoint responses.

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

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient


def build_parser() -> argparse.ArgumentParser:
    """Build the smoke-test command parser."""
    parser = argparse.ArgumentParser(description="Smoke-test Procore Documents endpoints")
    parser.add_argument(
        "--project",
        "--project-id",
        dest="project_id",
        type=int,
        default=_env_int("PROCORE_PROJECT_ID"),
        help="Procore project ID. Defaults to PROCORE_PROJECT_ID.",
    )
    parser.add_argument(
        "--folder",
        "--folder-id",
        dest="folder_id",
        type=int,
        default=_env_int("PROCORE_DOCUMENT_FOLDER_ID"),
        help="Optional Procore folder ID to inspect.",
    )
    parser.add_argument(
        "--company-id",
        type=int,
        default=_env_int("PROCORE_COMPANY_ID"),
        help="Optional Procore company ID sent as Procore-Company-Id.",
    )
    return parser


def main() -> int:
    """Run the manual Documents smoke test."""
    args = build_parser().parse_args()
    if args.project_id is None:
        print("Set PROCORE_PROJECT_ID or pass --project before running this smoke test.")
        return 1

    client = ProcoreClient()
    headers = _company_headers(args.company_id)
    collection_params: dict[str, object] = {"project_id": args.project_id}
    if args.folder_id is not None:
        collection_params["filters[folder_id]"] = args.folder_id

    print("Request: GET /rest/v1.0/folders")
    print(f"Params: {_safe_json(collection_params)}")
    if headers:
        print("Headers: Procore-Company-Id=<set>")
    collection = client.get_all(
        endpoints.document_folders(args.project_id),
        params=collection_params,
        headers=headers,
    )
    print("Collection response sample:")
    print(_safe_json(_sample(collection)))

    if args.folder_id is not None:
        print(f"\nRequest: GET /rest/v1.0/folders/{args.folder_id}")
        folder = client.get(
            endpoints.document_folder(args.project_id, args.folder_id),
            params={"project_id": args.project_id},
            headers=headers,
        )
        print("Folder response sample:")
        print(_safe_json(folder))

    print("\nReview the payload for folders, files, and any url/download_url fields.")
    return 0


def _company_headers(company_id: int | None) -> dict[str, str] | None:
    """Return optional company header for Documents endpoints."""
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
