"""Unit tests for auth diagnostic helpers."""

from __future__ import annotations

import json
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from pyprocore.auth.diagnostics import (
    build_authorization_url,
    exchange_code_and_save,
    format_auth_exchange,
    format_auth_refresh,
    format_auth_status,
    format_login_url,
    get_auth_status,
    refresh_auth_token,
)
from pyprocore.auth.token_store import StoredToken, TokenStore
from pyprocore.core.config import ProcoreSettings
from pyprocore.core.exceptions import AuthenticationError


def required_environment() -> dict[str, str]:
    """Return complete auth configuration for tests."""
    return {
        "PROCORE_CLIENT_ID": "client-id",
        "PROCORE_CLIENT_SECRET": "client-secret",
        "PROCORE_REDIRECT_URI": "http://localhost:8080/callback",
        "PROCORE_LOGIN_URL": "https://login.procore.com",
        "PROCORE_API_BASE": "https://api.procore.com",
        "PROCORE_COMPANY_ID": "123456",
    }


def write_token(path: Path, **overrides: object) -> None:
    """Write a token store payload."""
    payload: dict[str, object] = {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "expires_at": int(time.time()) + 3600,
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload), encoding="utf-8")


class AuthDiagnosticsTestCase(unittest.TestCase):
    """Validate auth status, refresh, and login URL helpers."""

    def test_status_with_full_token_data(self) -> None:
        """Complete config and token data report usable auth state."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token.json"
            write_token(token_path)

            report = get_auth_status(
                token_store=TokenStore(token_path),
                env_path=root / ".env",
                environ=required_environment(),
            )

        self.assertEqual(report.exit_code, 0)
        self.assertTrue(report.access_token_present)
        self.assertTrue(report.refresh_token_present)
        self.assertEqual(report.token_status, "Valid")
        self.assertEqual(report.company_id, 123456)
        self.assertIn("ready", format_auth_status(report))

    def test_status_with_missing_token_store_fails(self) -> None:
        """Missing token storage exits with failure guidance."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)

            report = get_auth_status(
                token_store=TokenStore(root / "missing.json"),
                env_path=root / ".env",
                environ=required_environment(),
            )

        self.assertEqual(report.exit_code, 1)
        self.assertFalse(report.token_store_exists)
        self.assertIn("Token store is missing.", report.errors)
        self.assertIn("auth login-url", format_auth_status(report))

    def test_status_with_missing_refresh_token_warns_but_exits_zero(self) -> None:
        """Missing refresh token is a warning when an access token exists."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token.json"
            write_token(token_path, refresh_token=None)

            report = get_auth_status(
                token_store=TokenStore(token_path),
                env_path=root / ".env",
                environ=required_environment(),
            )

        self.assertEqual(report.exit_code, 0)
        self.assertFalse(report.refresh_token_present)
        self.assertIn("Refresh token is missing.", report.warnings)

    def test_status_detects_expired_token(self) -> None:
        """Expired access tokens are identified without calling Procore."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token.json"
            write_token(token_path, expires_at=int(time.time()) - 60)

            report = get_auth_status(
                token_store=TokenStore(token_path),
                env_path=root / ".env",
                environ=required_environment(),
            )

        self.assertEqual(report.token_status, "Expired")
        self.assertIn("auth refresh", format_auth_status(report))

    def test_status_with_missing_configuration_fails(self) -> None:
        """Missing auth configuration exits with a failure."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token.json"
            write_token(token_path)

            report = get_auth_status(
                token_store=TokenStore(token_path),
                env_path=root / ".env",
                environ={},
            )

        self.assertEqual(report.exit_code, 1)
        self.assertIn("PROCORE_CLIENT_ID", report.missing_configuration)
        self.assertIn("Missing configuration", format_auth_status(report))

    def test_status_with_unreadable_token_store_fails(self) -> None:
        """Unreadable token storage exits with a failure."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token.json"
            token_path.write_text("not-json", encoding="utf-8")

            report = get_auth_status(
                token_store=TokenStore(token_path),
                env_path=root / ".env",
                environ=required_environment(),
            )

        self.assertEqual(report.exit_code, 1)
        self.assertIn("unreadable", report.errors[0])
        self.assertIn("missing or unreadable", format_auth_status(report))

    def test_status_with_empty_token_store_fails(self) -> None:
        """Empty token storage is reported as unusable token data."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token.json"
            token_path.write_text("{}", encoding="utf-8")

            report = get_auth_status(
                token_store=TokenStore(token_path),
                env_path=root / ".env",
                environ=required_environment(),
            )

        self.assertEqual(report.exit_code, 1)
        self.assertIn("does not contain token data", report.errors[0])

    def test_status_with_invalid_company_id_keeps_safe_output(self) -> None:
        """Invalid company IDs do not crash status output."""
        environment = required_environment()
        environment["PROCORE_COMPANY_ID"] = "not-a-number"

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            token_path = root / "token.json"
            write_token(token_path)

            report = get_auth_status(
                token_store=TokenStore(token_path),
                env_path=root / ".env",
                environ=environment,
            )

        self.assertIsNone(report.company_id)
        self.assertIn("Company ID: Missing", format_auth_status(report))

    def test_login_url_generation(self) -> None:
        """Authorization URL includes standard OAuth code-flow parameters."""
        settings = ProcoreSettings(
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="http://localhost:8080/callback",
            login_url="https://login.procore.com",
            api_base="https://api.procore.com",
            company_id=123,
        )

        result = build_authorization_url(settings)

        self.assertIn("https://login.procore.com/oauth/authorize?", result.authorization_url)
        self.assertIn("response_type=code", result.authorization_url)
        self.assertIn("client_id=client-id", result.authorization_url)
        self.assertIn(
            "redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Fcallback", result.authorization_url
        )
        self.assertNotIn("client-secret", result.authorization_url)
        self.assertIn("Open this URL", format_login_url(result))

    def test_refresh_success(self) -> None:
        """Refresh success returns a safe message and expiry."""
        token = StoredToken(
            access_token="new-access-token",
            refresh_token="refresh-token",
            expires_at=int(time.time()) + 7200,
        )
        manager = Mock()
        manager.refresh_token.return_value = token

        result = refresh_auth_token(manager)

        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("successfully", format_auth_refresh(result))
        self.assertNotIn("new-access-token", format_auth_refresh(result))
        manager.refresh_token.assert_called_once_with()

    def test_refresh_failure_due_to_missing_refresh_token(self) -> None:
        """Missing refresh token becomes a beginner-friendly failure."""
        manager = Mock()
        manager.refresh_token.side_effect = AuthenticationError(
            "No Procore refresh token is available."
        )

        result = refresh_auth_token(manager)

        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("No Procore refresh token", result.error or "")

    def test_refresh_failure_due_to_auth_error(self) -> None:
        """OAuth refresh rejections are reported without token values."""
        manager = Mock()
        manager.refresh_token.side_effect = AuthenticationError(
            "OAuth token request failed with status 401."
        )

        result = refresh_auth_token(manager)

        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("status 401", result.error or "")

    def test_refresh_failure_without_error_detail_formats_next_step(self) -> None:
        """Refresh failures without details still give a useful next step."""
        formatted = format_auth_refresh(
            refresh_auth_token(Mock(refresh_token=Mock(side_effect=AuthenticationError(""))))
        )

        self.assertIn("Next step", formatted)

    def test_exchange_code_success_saves_token_without_printing_secrets(self) -> None:
        """Authorization code exchange saves tokens and formats safe output."""
        stored_token = StoredToken(
            access_token="new-access-token",
            refresh_token="new-refresh-token",
            expires_at=int(time.time()) + 7200,
        )
        manager = Mock()
        manager.save_oauth_response.return_value = stored_token
        exchange = Mock(return_value="oauth-response")

        result = exchange_code_and_save(
            " authorization-code ",
            token_manager=manager,
            exchange_func=exchange,
        )
        formatted = format_auth_exchange(result)

        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
        exchange.assert_called_once_with("authorization-code")
        manager.save_oauth_response.assert_called_once_with("oauth-response")
        self.assertIn("Token store: Updated", formatted)
        self.assertIn("Refresh token: Present", formatted)
        self.assertIn("Access token: Present", formatted)
        self.assertNotIn("new-access-token", formatted)
        self.assertNotIn("new-refresh-token", formatted)

    def test_exchange_code_missing_code_returns_failure(self) -> None:
        """Blank authorization codes fail before OAuth is called."""
        exchange = Mock()
        manager = Mock()

        result = exchange_code_and_save("", token_manager=manager, exchange_func=exchange)

        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Authorization code is required", result.error or "")
        exchange.assert_not_called()
        manager.save_oauth_response.assert_not_called()

    def test_exchange_code_failure_returns_safe_guidance(self) -> None:
        """OAuth exchange failures become beginner-friendly messages."""
        exchange = Mock(
            side_effect=AuthenticationError("OAuth token request failed with status 401.")
        )
        manager = Mock()

        result = exchange_code_and_save(
            "bad-code",
            token_manager=manager,
            exchange_func=exchange,
        )
        formatted = format_auth_exchange(result)

        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Authorization code exchange failed", formatted)
        self.assertIn("auth login-url", formatted)
        self.assertNotIn("bad-code", formatted)
        manager.save_oauth_response.assert_not_called()

    def test_exchange_code_save_failure_returns_safe_guidance(self) -> None:
        """Token save failures are reported without token values."""
        manager = Mock()
        manager.save_oauth_response.side_effect = AuthenticationError("Unable to save token store.")
        exchange = Mock(return_value="oauth-response")

        result = exchange_code_and_save(
            "authorization-code",
            token_manager=manager,
            exchange_func=exchange,
        )

        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Unable to save token store", result.error or "")


if __name__ == "__main__":
    unittest.main()
