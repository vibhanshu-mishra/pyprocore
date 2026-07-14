"""Unit tests for PyProcore diagnostics."""

from __future__ import annotations

import json
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from pyprocore.core.doctor import DoctorReport, format_doctor_report, run_doctor
from pyprocore.core.exceptions import AuthenticationError


def required_environment() -> dict[str, str]:
    """Return a complete test Procore environment."""
    return {
        "PROCORE_CLIENT_ID": "client-id",
        "PROCORE_CLIENT_SECRET": "client-secret",
        "PROCORE_REDIRECT_URI": "http://localhost/callback",
        "PROCORE_LOGIN_URL": "https://login.procore.com",
        "PROCORE_API_BASE": "https://api.procore.com",
        "PROCORE_COMPANY_ID": "123",
    }


def write_token(path: Path, **overrides: object) -> None:
    """Write a token store payload for doctor tests."""
    payload: dict[str, object] = {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "expires_at": int(time.time()) + 3600,
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload), encoding="utf-8")


class DoctorTestCase(unittest.TestCase):
    """Validate local setup diagnostics without live Procore access."""

    def test_all_required_configuration_present(self) -> None:
        """Complete configuration and token data produce no failures."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            env_path = root / ".env"
            token_path = root / "token_store.json"
            env_path.write_text("", encoding="utf-8")
            write_token(token_path)

            report = run_doctor(
                env_path=env_path,
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ=required_environment(),
            )

        self.assertEqual(report.summary.failed, 0)
        self.assertEqual(report.exit_code, 0)
        self.assertIn("Required configuration", _statuses(report))
        self.assertEqual(_statuses(report)["Required configuration"], "pass")
        self.assertEqual(_statuses(report)["Auth mode"], "pass")

    def test_missing_required_environment_fails(self) -> None:
        """Missing required Procore settings are reported clearly."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token_store.json"
            write_token(token_path)

            report = run_doctor(
                env_path=root / ".env",
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ={},
            )

        checks = {check.name: check for check in report.checks}
        self.assertEqual(checks["Required configuration"].status, "fail")
        self.assertIn("PROCORE_CLIENT_ID", checks["Required configuration"].details or "")
        self.assertEqual(report.exit_code, 1)

    def test_env_file_values_are_used_when_environment_is_empty(self) -> None:
        """A local .env file can satisfy required configuration checks."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            env_path = root / ".env"
            token_path = root / "token_store.json"
            env_path.write_text(
                "\n".join(f"{key}={value}" for key, value in required_environment().items()),
                encoding="utf-8",
            )
            write_token(token_path)

            report = run_doctor(
                env_path=env_path,
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ={},
            )

        self.assertEqual(_statuses(report)["Required configuration"], "pass")

    def test_token_store_missing_fails(self) -> None:
        """A missing token store means authenticated calls are not ready."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)

            report = run_doctor(
                env_path=root / ".env",
                token_store_path=root / "missing-token.json",
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ=required_environment(),
            )

        self.assertEqual(_statuses(report)["Token store"], "fail")
        self.assertEqual(report.exit_code, 1)

    def test_token_store_missing_refresh_token_warns(self) -> None:
        """A missing refresh token warns because expired tokens cannot refresh."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token_store.json"
            write_token(token_path, refresh_token=None)

            report = run_doctor(
                env_path=root / ".env",
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ=required_environment(),
            )

        self.assertEqual(_statuses(report)["Refresh token"], "warn")

    def test_client_credentials_config_does_not_require_redirect_uri(self) -> None:
        """Client credentials mode does not require redirect URI config."""
        environment = required_environment()
        environment.pop("PROCORE_REDIRECT_URI")
        environment["PROCORE_AUTH_MODE"] = "client_credentials"
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token_store.json"
            write_token(token_path, refresh_token=None, auth_mode="client_credentials")

            report = run_doctor(
                env_path=root / ".env",
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ=environment,
            )

        statuses = _statuses(report)
        self.assertEqual(statuses["Auth mode"], "pass")
        self.assertEqual(statuses["Required configuration"], "pass")
        self.assertEqual(statuses["Refresh token"], "pass")

    def test_expired_client_credentials_token_warns_without_refresh_token(self) -> None:
        """Expired client credentials tokens can be renewed without refresh tokens."""
        environment = required_environment()
        environment["PROCORE_AUTH_MODE"] = "client_credentials"
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token_store.json"
            write_token(
                token_path,
                refresh_token=None,
                expires_at=int(time.time()) - 60,
                auth_mode="client_credentials",
            )

            report = run_doctor(
                env_path=root / ".env",
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ=environment,
            )

        self.assertEqual(_statuses(report)["Token expiry"], "warn")
        self.assertNotEqual(_statuses(report)["Token expiry"], "fail")

    def test_invalid_url_values_fail(self) -> None:
        """Malformed URL settings are reported as failed checks."""
        environment = required_environment()
        environment["PROCORE_API_BASE"] = "not-a-url"

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token_store.json"
            write_token(token_path)

            report = run_doctor(
                env_path=root / ".env",
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ=environment,
            )

        self.assertEqual(_statuses(report)["PROCORE_API_BASE URL"], "fail")

    def test_expired_token_without_refresh_token_fails(self) -> None:
        """Expired access tokens fail when no refresh token is available."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token_store.json"
            write_token(token_path, refresh_token=None, expires_at=int(time.time()) - 60)

            report = run_doctor(
                env_path=root / ".env",
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ=required_environment(),
            )

        self.assertEqual(_statuses(report)["Token expiry"], "fail")

    def test_invalid_token_expiry_fails(self) -> None:
        """Unparseable token expiry values are reported clearly."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token_store.json"
            write_token(token_path, expires_at="not-a-number")

            report = run_doctor(
                env_path=root / ".env",
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ=required_environment(),
            )

        self.assertEqual(_statuses(report)["Token expiry"], "fail")

    def test_python_version_check(self) -> None:
        """Python 3.12+ is reported as passing in this test environment."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token_store.json"
            write_token(token_path)

            report = run_doctor(
                env_path=root / ".env",
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ=required_environment(),
            )

        self.assertGreaterEqual(sys.version_info, (3, 12))
        self.assertEqual(_statuses(report)["Python version"], "pass")

    def test_writable_directory_checks(self) -> None:
        """Doctor creates and verifies writable SDK directories."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "auth" / "token_store.json"
            token_path.parent.mkdir()
            write_token(token_path)

            report = run_doctor(
                env_path=root / ".env",
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ=required_environment(),
            )

            self.assertTrue((root / "logs").exists())
            self.assertTrue((root / "downloads").exists())

        statuses = _statuses(report)
        self.assertEqual(statuses["logs directory"], "pass")
        self.assertEqual(statuses["downloads directory"], "pass")
        self.assertEqual(statuses["Token store parent"], "pass")

    def test_json_serialization_and_human_formatting(self) -> None:
        """Doctor reports serialize to JSON and format readable CLI text."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token_store.json"
            write_token(token_path)

            report = run_doctor(
                env_path=root / ".env",
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ=required_environment(),
            )

        serialized = json.loads(report.model_dump_json())
        self.assertIn("checks", serialized)
        self.assertIn("summary", serialized)
        self.assertIn("PyProcore Doctor", format_doctor_report(report))

    def test_live_check_success_and_failure(self) -> None:
        """Live checks use an injected callable and normalize SDK failures."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token_store.json"
            write_token(token_path)
            live_check = Mock(return_value=[])

            report = run_doctor(
                live=True,
                env_path=root / ".env",
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ=required_environment(),
                live_check=live_check,
            )

            failing_report = run_doctor(
                live=True,
                env_path=root / ".env",
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ=required_environment(),
                live_check=Mock(side_effect=AuthenticationError("bad token")),
            )

        live_check.assert_called_once_with()
        self.assertEqual(_statuses(report)["Live Procore API check"], "pass")
        self.assertEqual(_statuses(failing_report)["Live Procore API check"], "fail")


def _statuses(report: DoctorReport) -> dict[str, str]:
    """Return check statuses by name."""
    return {check.name: check.status for check in report.checks}


if __name__ == "__main__":
    unittest.main()
