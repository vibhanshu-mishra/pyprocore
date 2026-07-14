"""Tests for token storage and refresh behavior."""

from __future__ import annotations

import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import SecretStr

from pyprocore.auth.oauth import OAuthTokenResponse
from pyprocore.auth.token_manager import TokenManager
from pyprocore.auth.token_store import StoredToken, TokenStore
from pyprocore.core.config import ProcoreSettings
from pyprocore.core.exceptions import AuthenticationError


class FakeOAuthClient:
    """Fake OAuth client for refresh tests."""

    def __init__(self, token_response: OAuthTokenResponse) -> None:
        """Initialize the fake client."""
        self.token_response = token_response
        self.refresh_tokens: list[str] = []
        self.client_credentials_requests = 0

    def refresh_access_token(self, refresh_token: str) -> OAuthTokenResponse:
        """Return the configured token response and record the input token."""
        self.refresh_tokens.append(refresh_token)
        return self.token_response

    def request_client_credentials_token(self) -> OAuthTokenResponse:
        """Return the configured token response and record the request."""
        self.client_credentials_requests += 1
        return self.token_response


class TokenManagementTestCase(unittest.TestCase):
    """Validate token persistence and refresh flows."""

    def test_token_store_round_trip(self) -> None:
        """Saved tokens can be loaded without exposing secret wrappers."""
        with TemporaryDirectory() as temporary_directory:
            store = TokenStore(Path(temporary_directory) / "token.json")
            token = StoredToken(
                access_token="access-token",
                refresh_token="refresh-token",
                expires_at=int(time.time()) + 3600,
            )

            store.save(token)
            loaded = store.load()

            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.access_token.get_secret_value(), "access-token")
            self.assertIsNotNone(loaded.refresh_token)
            assert loaded.refresh_token is not None
            self.assertEqual(loaded.refresh_token.get_secret_value(), "refresh-token")

    def test_missing_token_raises_authentication_error(self) -> None:
        """Access token lookup fails clearly when no token has been stored."""
        with TemporaryDirectory() as temporary_directory:
            manager = TokenManager(
                token_store=TokenStore(Path(temporary_directory) / "token.json"),
                oauth_client=FakeOAuthClient(
                    OAuthTokenResponse(
                        access_token=SecretStr("unused"),
                        expires_in=3600,
                    )
                ),
            )

            with self.assertRaises(AuthenticationError):
                manager.get_access_token()

    def test_missing_client_credentials_token_requests_and_saves_token(self) -> None:
        """Client credentials mode requests a token when none is stored."""
        with TemporaryDirectory() as temporary_directory:
            store = TokenStore(Path(temporary_directory) / "token.json")
            oauth_client = FakeOAuthClient(
                OAuthTokenResponse(
                    access_token=SecretStr("client-access-token"),
                    expires_in=3600,
                )
            )
            manager = TokenManager(
                token_store=store,
                oauth_client=oauth_client,
                settings=client_credentials_settings(),
            )

            access_token = manager.get_access_token()
            saved_token = store.load()

            self.assertEqual(access_token, "client-access-token")
            self.assertEqual(oauth_client.client_credentials_requests, 1)
            self.assertIsNotNone(saved_token)
            assert saved_token is not None
            self.assertEqual(saved_token.auth_mode, "client_credentials")
            self.assertIsNone(saved_token.refresh_token)

    def test_expired_token_refresh_reuses_existing_refresh_token(self) -> None:
        """Expired access tokens are refreshed and retain refresh tokens."""
        with TemporaryDirectory() as temporary_directory:
            store = TokenStore(Path(temporary_directory) / "token.json")
            store.save(
                StoredToken(
                    access_token="old-access-token",
                    refresh_token="existing-refresh-token",
                    expires_at=1,
                )
            )
            oauth_client = FakeOAuthClient(
                OAuthTokenResponse(
                    access_token=SecretStr("new-access-token"),
                    expires_in=3600,
                    refresh_token=None,
                )
            )
            manager = TokenManager(token_store=store, oauth_client=oauth_client)

            access_token = manager.get_access_token()
            saved_token = store.load()

            self.assertEqual(access_token, "new-access-token")
            self.assertEqual(oauth_client.refresh_tokens, ["existing-refresh-token"])
            self.assertIsNotNone(saved_token)
            assert saved_token is not None
            self.assertIsNotNone(saved_token.refresh_token)
            assert saved_token.refresh_token is not None
            self.assertEqual(
                saved_token.refresh_token.get_secret_value(),
                "existing-refresh-token",
            )

    def test_valid_token_is_returned_without_refresh(self) -> None:
        """Unexpired access tokens are returned as-is."""
        with TemporaryDirectory() as temporary_directory:
            store = TokenStore(Path(temporary_directory) / "token.json")
            store.save(
                StoredToken(
                    access_token="current-access-token",
                    refresh_token="refresh-token",
                    expires_at=int(time.time()) + 3600,
                )
            )
            oauth_client = FakeOAuthClient(
                OAuthTokenResponse(access_token=SecretStr("unused"), expires_in=3600)
            )

            access_token = TokenManager(
                token_store=store, oauth_client=oauth_client
            ).get_access_token()

            self.assertEqual(access_token, "current-access-token")
            self.assertEqual(oauth_client.refresh_tokens, [])

    def test_force_refresh_refreshes_unexpired_token(self) -> None:
        """Callers can force refresh even before expiry."""
        with TemporaryDirectory() as temporary_directory:
            store = TokenStore(Path(temporary_directory) / "token.json")
            store.save(
                StoredToken(
                    access_token="current-access-token",
                    refresh_token="refresh-token",
                    expires_at=int(time.time()) + 3600,
                )
            )
            oauth_client = FakeOAuthClient(
                OAuthTokenResponse(
                    access_token=SecretStr("forced-access-token"),
                    refresh_token=SecretStr("new-refresh-token"),
                    expires_in=3600,
                )
            )

            access_token = TokenManager(
                token_store=store,
                oauth_client=oauth_client,
            ).get_access_token(force_refresh=True)

            self.assertEqual(access_token, "forced-access-token")
            saved_token = store.load()
            self.assertIsNotNone(saved_token)
            assert saved_token is not None
            self.assertIsNotNone(saved_token.refresh_token)
            assert saved_token.refresh_token is not None
            self.assertEqual(saved_token.refresh_token.get_secret_value(), "new-refresh-token")

    def test_refresh_token_requires_stored_token_and_refresh_token(self) -> None:
        """Refresh failures are explicit before OAuth is called."""
        with TemporaryDirectory() as temporary_directory:
            store = TokenStore(Path(temporary_directory) / "token.json")
            manager = TokenManager(
                token_store=store,
                oauth_client=FakeOAuthClient(
                    OAuthTokenResponse(access_token=SecretStr("unused"), expires_in=3600)
                ),
            )

            with self.assertRaises(AuthenticationError):
                manager.refresh_token()

            store.save(
                StoredToken(
                    access_token="access-token",
                    refresh_token=None,
                    expires_at=1,
                )
            )
            with self.assertRaises(AuthenticationError):
                manager.refresh_token()

    def test_expired_client_credentials_token_requests_new_token(self) -> None:
        """Expired client credentials tokens renew without refresh tokens."""
        with TemporaryDirectory() as temporary_directory:
            store = TokenStore(Path(temporary_directory) / "token.json")
            store.save(
                StoredToken(
                    access_token="old-client-token",
                    refresh_token=None,
                    expires_at=1,
                    auth_mode="client_credentials",
                )
            )
            oauth_client = FakeOAuthClient(
                OAuthTokenResponse(
                    access_token=SecretStr("new-client-token"),
                    expires_in=3600,
                )
            )
            manager = TokenManager(
                token_store=store,
                oauth_client=oauth_client,
                settings=client_credentials_settings(),
            )

            access_token = manager.get_access_token()
            saved_token = store.load()

            self.assertEqual(access_token, "new-client-token")
            self.assertEqual(oauth_client.refresh_tokens, [])
            self.assertEqual(oauth_client.client_credentials_requests, 1)
            self.assertIsNotNone(saved_token)
            assert saved_token is not None
            self.assertEqual(saved_token.auth_mode, "client_credentials")
            self.assertIsNone(saved_token.refresh_token)

    def test_save_oauth_response_and_clear_token(self) -> None:
        """Initial OAuth responses can be saved and later cleared."""
        with TemporaryDirectory() as temporary_directory:
            store = TokenStore(Path(temporary_directory) / "token.json")
            manager = TokenManager(
                token_store=store,
                oauth_client=FakeOAuthClient(
                    OAuthTokenResponse(access_token=SecretStr("unused"), expires_in=3600)
                ),
            )

            stored_token = manager.save_oauth_response(
                OAuthTokenResponse(
                    access_token=SecretStr("initial-access-token"),
                    refresh_token=SecretStr("initial-refresh-token"),
                    expires_in=3600,
                )
            )
            self.assertEqual(stored_token.access_token.get_secret_value(), "initial-access-token")
            self.assertIsNotNone(store.load())

            manager.clear_token()
            self.assertIsNone(store.load())


def client_credentials_settings() -> ProcoreSettings:
    """Return test settings for client credentials auth."""
    return ProcoreSettings(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri=None,
        login_url="https://login.example.com",
        api_base="https://api.example.com",
        company_id=123,
        auth_mode="client_credentials",
    )


if __name__ == "__main__":
    unittest.main()
