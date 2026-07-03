"""Unit tests for SDK support modules."""

from __future__ import annotations

import time
import unittest
from email.message import EmailMessage
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import requests
from requests import Response

import pyprocore.auth as auth
import pyprocore.core as core
from pyprocore.auth.oauth import OAuthClient, exchange_authorization_code, refresh_access_token
from pyprocore.auth.token_store import StoredToken, TokenStore, load_token, save_token
from pyprocore.core.config import ProcoreSettings, get_settings
from pyprocore.core.exceptions import AuthenticationError, ConfigurationError
from pyprocore.parser.email_parser import EmailParser, parse_email_file, parse_email_text


def settings() -> ProcoreSettings:
    """Return test settings without reading environment variables."""
    return ProcoreSettings(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="http://localhost/callback",
        login_url="https://login.example.com/",
        api_base="https://api.example.com/",
        company_id=123,
    )


def oauth_response(
    status_code: int = 200,
    body: bytes = (
        b'{"access_token": "access-token", "refresh_token": "refresh-token", '
        b'"expires_in": 3600, "token_type": "Bearer"}'
    ),
    content_type: str = "application/json",
) -> Response:
    """Build a mocked OAuth HTTP response."""
    response = Response()
    response.status_code = status_code
    response._content = body
    response.headers["Content-Type"] = content_type
    response.url = "https://login.example.com/oauth/token"
    return response


class ConfigTestCase(unittest.TestCase):
    """Validate environment-backed configuration loading."""

    def tearDown(self) -> None:
        """Clear cached settings after environment mutations."""
        get_settings.cache_clear()

    def test_settings_normalize_urls_and_company_id(self) -> None:
        """Settings strip URL suffixes and coerce company IDs."""
        configured = settings()

        self.assertEqual(configured.login_url, "https://login.example.com")
        self.assertEqual(configured.api_base, "https://api.example.com")
        self.assertEqual(configured.company_id, 123)

    def test_get_settings_reads_environment(self) -> None:
        """get_settings reads supported Procore variables from the environment."""
        environment = {
            "PROCORE_CLIENT_ID": "client-id",
            "PROCORE_CLIENT_SECRET": "client-secret",
            "PROCORE_REDIRECT_URI": "http://localhost/callback",
            "PROCORE_LOGIN_URL": "https://login.example.com/",
            "PROCORE_API_BASE": "https://api.example.com/",
            "PROCORE_COMPANY_ID": "456",
        }

        with patch.dict("os.environ", environment, clear=True):
            configured = get_settings()

        self.assertEqual(configured.company_id, 456)
        self.assertEqual(configured.api_base, "https://api.example.com")

    def test_get_settings_raises_clear_error_for_invalid_environment(self) -> None:
        """Invalid configuration becomes ConfigurationError."""
        with patch.dict("os.environ", {}, clear=True):
            get_settings.cache_clear()
            with self.assertRaises(ConfigurationError):
                get_settings()


class OAuthClientTestCase(unittest.TestCase):
    """Validate OAuth request behavior without live Procore access."""

    def setUp(self) -> None:
        """Create fresh session mocks for each test."""
        self.session = Mock(spec=requests.Session)
        self.client = OAuthClient(settings=settings(), session=self.session, timeout_seconds=7)

    def test_exchange_authorization_code_posts_expected_payload(self) -> None:
        """Authorization code exchange posts to the configured login host."""
        self.session.post.return_value = oauth_response()

        token = self.client.exchange_authorization_code(" code-123 ")

        self.assertEqual(token.access_token.get_secret_value(), "access-token")
        self.session.post.assert_called_once()
        call = self.session.post.call_args
        self.assertEqual(call.args[0], "https://login.example.com/oauth/token")
        self.assertEqual(call.kwargs["timeout"], 7)
        self.assertEqual(call.kwargs["data"]["grant_type"], "authorization_code")
        self.assertEqual(call.kwargs["data"]["code"], "code-123")
        self.assertEqual(call.kwargs["data"]["client_secret"], "client-secret")

    def test_refresh_access_token_posts_expected_payload(self) -> None:
        """Refresh flow posts a refresh-token grant."""
        self.session.post.return_value = oauth_response()

        token = self.client.refresh_access_token(" refresh-token ")

        self.assertEqual(token.refresh_token.get_secret_value(), "refresh-token")
        self.assertEqual(self.session.post.call_args.kwargs["data"]["grant_type"], "refresh_token")
        self.assertEqual(
            self.session.post.call_args.kwargs["data"]["refresh_token"], "refresh-token"
        )

    def test_blank_oauth_inputs_raise_authentication_error(self) -> None:
        """Blank authorization codes and refresh tokens are rejected."""
        with self.assertRaises(AuthenticationError):
            self.client.exchange_authorization_code(" ")
        with self.assertRaises(AuthenticationError):
            self.client.refresh_access_token("")

        self.session.post.assert_not_called()

    def test_oauth_http_error_raises_safe_authentication_error(self) -> None:
        """OAuth HTTP failures include status and response body."""
        self.session.post.return_value = oauth_response(401, b'{"error": "invalid"}')

        with self.assertRaises(AuthenticationError) as context:
            self.client.refresh_access_token("refresh-token")

        self.assertIn("status 401", str(context.exception))
        self.assertNotIn("client-secret", str(context.exception))

    def test_oauth_request_exception_and_invalid_json_raise_authentication_error(self) -> None:
        """Network failures and invalid JSON are normalized."""
        self.session.post.side_effect = requests.RequestException("timeout")
        with self.assertRaises(AuthenticationError):
            self.client.refresh_access_token("refresh-token")

        self.session.post.side_effect = None
        self.session.post.return_value = oauth_response(200, b"not-json", "text/plain")
        with self.assertRaises(AuthenticationError):
            self.client.refresh_access_token("refresh-token")

    def test_oauth_invalid_payload_raises_authentication_error(self) -> None:
        """Malformed successful OAuth payloads are rejected."""
        self.session.post.return_value = oauth_response(200, b'{"access_token": "missing-expiry"}')

        with self.assertRaises(AuthenticationError):
            self.client.refresh_access_token("refresh-token")

    def test_module_level_oauth_helpers_use_default_client(self) -> None:
        """Convenience helpers delegate to OAuthClient."""
        with patch("pyprocore.auth.oauth.OAuthClient") as oauth_class:
            oauth = Mock()
            oauth.exchange_authorization_code.return_value = "code-token"
            oauth.refresh_access_token.return_value = "refresh-token"
            oauth_class.return_value = oauth

            self.assertEqual(exchange_authorization_code("code"), "code-token")
            self.assertEqual(refresh_access_token("refresh"), "refresh-token")


class TokenStoreTestCase(unittest.TestCase):
    """Validate token file edge cases."""

    def test_empty_and_missing_token_files_load_as_none(self) -> None:
        """Missing, empty, and empty-object token files behave as no token."""
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "token.json"
            store = TokenStore(path)
            self.assertIsNone(store.load())

            path.write_text("", encoding="utf-8")
            self.assertIsNone(store.load())

            path.write_text("{}", encoding="utf-8")
            self.assertIsNone(store.load())

    def test_invalid_token_files_raise_authentication_error(self) -> None:
        """Invalid JSON and invalid token payloads fail clearly."""
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "token.json"
            store = TokenStore(path)

            path.write_text("{bad-json", encoding="utf-8")
            with self.assertRaises(AuthenticationError):
                store.load()

            path.write_text('{"access_token": "token"}', encoding="utf-8")
            with self.assertRaises(AuthenticationError):
                store.load()

    def test_token_expiry_and_public_serialization(self) -> None:
        """StoredToken handles expiry skew and plain JSON persistence."""
        token = StoredToken(
            access_token="access-token",
            refresh_token="refresh-token",
            expires_at=int(time.time()) + 30,
            token_type=" Bearer ",
        )

        self.assertTrue(token.is_expired())
        self.assertFalse(token.is_expired(skew_seconds=0))
        self.assertEqual(token.token_type, "Bearer")
        self.assertEqual(token.to_public_dict()["access_token"], "access-token")
        self.assertEqual(token.to_public_dict()["refresh_token"], "refresh-token")

    def test_from_oauth_response_accepts_mapping_and_existing_refresh_token(self) -> None:
        """StoredToken can be created from mapping-style OAuth payloads."""
        token = StoredToken.from_oauth_response(
            {"access_token": "new-access", "expires_in": 3600},
            existing_refresh_token="existing-refresh",
        )

        self.assertEqual(token.access_token.get_secret_value(), "new-access")
        self.assertIsNotNone(token.refresh_token)
        assert token.refresh_token is not None
        self.assertEqual(token.refresh_token.get_secret_value(), "existing-refresh")

    def test_clear_and_module_level_store_helpers(self) -> None:
        """TokenStore clear and module helpers delegate to the default store."""
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "token.json"
            store = TokenStore(path)
            token = StoredToken(
                access_token="access-token",
                refresh_token=None,
                expires_at=int(time.time()) + 3600,
            )
            store.save(token)
            self.assertTrue(path.exists())
            store.clear()
            self.assertFalse(path.exists())

        with patch("pyprocore.auth.token_store.TokenStore") as store_class:
            default_store = Mock()
            default_store.load.return_value = "loaded-token"
            store_class.return_value = default_store

            self.assertEqual(load_token(), "loaded-token")
            save_token(token)
            default_store.save.assert_called_once_with(token)


class EmailParserTestCase(unittest.TestCase):
    """Validate email parsing utilities."""

    def test_parse_text_email_extracts_headers_and_text_body(self) -> None:
        """Plain text messages are parsed into structured email data."""
        parsed = EmailParser().parse_text(
            "Subject: Test RFI\n"
            "From: sender@example.com\n"
            "To: one@example.com, two@example.com\n"
            "Cc: cc@example.com\n"
            "Date: Fri, 03 Jul 2026 10:00:00 -0500\n"
            "\n"
            "Please review this RFI."
        )

        self.assertEqual(parsed.subject, "Test RFI")
        self.assertEqual(parsed.sender, "sender@example.com")
        self.assertEqual(parsed.recipients, ["one@example.com", "two@example.com"])
        self.assertEqual(parsed.cc, ["cc@example.com"])
        self.assertEqual(parsed.text_body, "Please review this RFI.")
        self.assertIsNone(parsed.html_body)

    def test_parse_multipart_email_extracts_html_text_and_attachments(self) -> None:
        """Multipart messages expose text, HTML, and attachment metadata."""
        message = EmailMessage()
        message["Subject"] = "Submittal"
        message["From"] = "sender@example.com"
        message["To"] = "receiver@example.com"
        message.set_content("Plain body")
        message.add_alternative("<p>HTML body</p>", subtype="html")
        message.add_attachment(
            b"attachment-bytes",
            maintype="application",
            subtype="pdf",
            filename="../spec.pdf",
        )

        parsed = EmailParser().parse_bytes(message.as_bytes())

        self.assertEqual(parsed.text_body.strip(), "Plain body")
        self.assertIn("HTML body", parsed.html_body or "")
        self.assertEqual(len(parsed.attachments), 1)
        self.assertEqual(parsed.attachments[0].filename, "spec.pdf")
        self.assertEqual(parsed.attachments[0].content_type, "application/pdf")
        self.assertEqual(parsed.attachments[0].size_bytes, len(b"attachment-bytes"))

    def test_parse_file_and_module_level_helpers(self) -> None:
        """File and module-level parsing helpers return ParsedEmail objects."""
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "message.eml"
            path.write_text("Subject: From File\n\nBody", encoding="utf-8")

            self.assertEqual(EmailParser().parse_file(path).subject, "From File")
            self.assertEqual(parse_email_file(path).subject, "From File")
            self.assertEqual(parse_email_text("Subject: From Text\n\nBody").subject, "From Text")


class PackageInitTestCase(unittest.TestCase):
    """Validate lazy package exports."""

    def test_auth_lazy_exports_and_missing_attribute(self) -> None:
        """auth exposes public objects lazily and rejects unknown names."""
        self.assertIs(auth.OAuthClient, OAuthClient)
        self.assertIs(auth.TokenStore, TokenStore)
        with self.assertRaises(AttributeError):
            getattr(auth, "Missing")

    def test_core_lazy_exports_and_missing_attribute(self) -> None:
        """core exposes public objects lazily and rejects unknown names."""
        self.assertIs(core.ProcoreSettings, ProcoreSettings)
        self.assertIs(core.AuthenticationError, AuthenticationError)
        self.assertTrue(callable(core.get_logger))
        with self.assertRaises(AttributeError):
            getattr(core, "Missing")


if __name__ == "__main__":
    unittest.main()
