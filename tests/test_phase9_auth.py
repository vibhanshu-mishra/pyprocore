"""Phase 9A enterprise authentication hardening tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pyprocore.auth.oauth import OAuthClient
from pyprocore.auth.permissions import (
    explain_auth_error,
    explain_environment_mismatch,
    explain_permission_error,
)
from pyprocore.auth.token_store import TokenStore
from pyprocore.core.config import AuthMode, normalize_auth_mode
from pyprocore.core.exceptions import AuthenticationError


class Phase9AuthTests(unittest.TestCase):
    def test_auth_mode_normalization_and_rejection(self) -> None:
        self.assertEqual(normalize_auth_mode(None), AuthMode.AUTHORIZATION_CODE)
        self.assertEqual(normalize_auth_mode(" CLIENT-CREDENTIALS "), AuthMode.CLIENT_CREDENTIALS)
        with self.assertRaisesRegex(ValueError, "Supported modes"):
            normalize_auth_mode("password")

    def test_permission_explanations_are_mode_specific_and_safe(self) -> None:
        secret = "do-not-print-this-token"
        message = explain_auth_error(401, {"access_token": secret}, "client_credentials")
        self.assertIn("requests a new access token", message)
        self.assertNotIn(secret, message)
        self.assertIn("service account", explain_permission_error(403, {}, "client_credentials"))
        self.assertIn(
            "different environments",
            explain_environment_mismatch("https://sandbox.example", "https://api.procore.com"),
        )

    def test_malformed_store_error_does_not_echo_contents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "token.json"
            secret = "secret-token-value"
            path.write_text('{"access_token": "' + secret + '"}', encoding="utf-8")
            with self.assertRaises(AuthenticationError) as context:
                TokenStore(path).load()
        self.assertNotIn(secret, str(context.exception))

    def test_oauth_error_redaction(self) -> None:
        redacted = OAuthClient._redact_error_body({"refresh_token": "secret", "message": "bad"})
        self.assertEqual(redacted["refresh_token"], "[REDACTED]")
