"""Manually inspect Procore Photos endpoint responses."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pyprocore
from pyprocore.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ProcoreAPIError,
)
from pyprocore.services.photos import PhotosService


def build_parser() -> argparse.ArgumentParser:
    """Build the smoke-test command parser."""
    parser = argparse.ArgumentParser(description="Smoke-test Procore Photos endpoints")
    parser.add_argument(
        "--project",
        "--project-id",
        dest="project_id",
        type=int,
        default=_env_int("PROCORE_PROJECT_ID"),
    )
    parser.add_argument(
        "--company",
        "--company-id",
        dest="company_id",
        type=int,
        default=_env_int("PROCORE_COMPANY_ID"),
    )
    parser.add_argument(
        "--album",
        "--album-id",
        dest="album_id",
        type=int,
        default=_env_int("PROCORE_PHOTO_ALBUM_ID"),
    )
    parser.add_argument(
        "--photo", "--photo-id", dest="photo_id", type=int, default=_env_int("PROCORE_PHOTO_ID")
    )
    parser.add_argument(
        "--download", action="store_true", help="Download --photo. Downloads are off by default."
    )
    parser.add_argument("--output-dir", type=Path, default=Path("downloads/photos"))
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    """Run the manual Photos smoke test."""
    args = build_parser().parse_args()
    try:
        return _run(args)
    except ConfigurationError as exc:
        print("Photos smoke test cannot run yet.")
        print(f"Details: {exc}")
        print("Run `procore-sdk doctor` and complete OAuth first.")
        return 1
    except AuthenticationError as exc:
        print("Photos smoke test could not authenticate with Procore.")
        print(f"Details: {exc}")
        print("Run `procore-sdk auth status` or `procore-sdk auth refresh`.")
        return 1
    except AuthorizationError as exc:
        print("Authenticated successfully, but Procore rejected the project/company context.")
        print(f"\nDetails: {exc}")
        print("\nSuggested fixes:")
        print("- Confirm project_id belongs to company_id")
        print("- Confirm production vs sandbox environment")
        print("- Confirm the OAuth app is connected to the company")
        print("- Confirm the OAuth user has access to the company/project")
        print("- Confirm the Photos tool is enabled and the user can view Photos")
        return 1
    except ProcoreAPIError as exc:
        print("Photos smoke test reached Procore, but the API returned an error.")
        print(f"Details: {exc}")
        print("Confirm project/company IDs, Photos permissions, and sandbox vs production.")
        return 1


def _run(args: argparse.Namespace) -> int:
    """Run the smoke-test implementation."""
    if args.project_id is None:
        print("Set PROCORE_PROJECT_ID or pass --project before running this smoke test.")
        return 1
    if args.company_id is None:
        print("Set PROCORE_COMPANY_ID or pass --company before running this smoke test.")
        return 1
    if args.verbose:
        print(f"Imported pyprocore from: {pyprocore.__file__}")
        print(f"Project ID: {args.project_id}")
        print(f"Company ID: {args.company_id}")

    service = PhotosService()
    print("Request: GET /rest/v1.0/image_categories?project_id=...")
    albums = service.list_photo_albums(args.project_id, company_id=args.company_id)
    print(_safe_json([album.model_dump(mode="json") for album in albums[:3]]))
    if not albums:
        print(
            "No photo albums/photos found. Confirm the Photos tool is enabled and the user has access."
        )
        return 1

    album_id = args.album_id or _first_album_id(albums)
    if album_id is not None:
        print(f"\nRequest: GET /rest/v1.0/images?project_id=...&image_category_id={album_id}")
        photos = service.list_photos(args.project_id, company_id=args.company_id, album_id=album_id)
        print(_safe_json([photo.model_dump(mode="json") for photo in photos[:3]]))
        if not photos:
            print(
                "No photo albums/photos found. Confirm the Photos tool is enabled and the user has access."
            )
            return 1

    if args.photo_id is not None:
        print(f"\nRequest: GET /rest/v1.0/images/{args.photo_id}?project_id=...")
        photo = service.get_photo(args.project_id, args.photo_id, company_id=args.company_id)
        print(_safe_json(photo.model_dump(mode="json")))
        if args.download:
            saved_path = service.download_photo(
                args.project_id,
                args.photo_id,
                output_dir=args.output_dir,
                company_id=args.company_id,
            )
            print(f"\nDownload complete: {saved_path}")
    elif args.download:
        print("Pass --photo before using --download.")
        return 1
    return 0


def _env_int(name: str) -> int | None:
    """Read an optional integer environment variable."""
    value = os.getenv(name)
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _first_album_id(albums: list[Any]) -> int | None:
    """Return the first album ID from typed album models."""
    for album in albums:
        if isinstance(album.id, int):
            return album.id
    return None


def _safe_json(value: object) -> str:
    """Serialize output without exposing common secrets."""
    return json.dumps(_redact(value), indent=2, default=str, sort_keys=True)


def _redact(value: object) -> object:
    """Redact common secret-like keys from nested output."""
    if isinstance(value, Mapping):
        return {
            str(key): (
                "<redacted>"
                if str(key).casefold()
                in {"authorization", "access_token", "refresh_token", "client_secret"}
                else _redact(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
