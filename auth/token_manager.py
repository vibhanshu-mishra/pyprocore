"""High-level OAuth token management for the Procore SDK.

The token manager is the only authentication object the rest of the
application should need. It loads saved tokens, detects expiry, refreshes when
needed, and returns a plain access token string for HTTP clients.
"""

from __future__ import annotations

from auth.oauth import OAuthClient, OAuthTokenResponse
from auth.token_store import StoredToken, TokenStore
from core.exceptions import AuthenticationError


class TokenManager:
    """Manage loading, refreshing, and saving Procore OAuth tokens."""

    def __init__(
        self,
        token_store: TokenStore | None = None,
        oauth_client: OAuthClient | None = None,
    ) -> None:
        """Initialize the token manager.

        Args:
            token_store: Optional token persistence backend.
            oauth_client: Optional OAuth client used for token refreshes.
        """
        self._token_store = token_store or TokenStore()
        self._oauth_client = oauth_client or OAuthClient()

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a valid access token, refreshing it when necessary.

        Args:
            force_refresh: Refresh the token even if the stored token has not
                reached its refresh window.

        Returns:
            The current bearer access token as a plain string.

        Raises:
            AuthenticationError: If no token exists or refresh cannot complete.
        """
        token = self._token_store.load()
        if token is None:
            raise AuthenticationError(
                "No Procore token is stored. Complete OAuth authorization first."
            )

        if force_refresh or token.is_expired():
            token = self.refresh_token(token)

        return token.access_token.get_secret_value()

    def refresh_token(self, token: StoredToken | None = None) -> StoredToken:
        """Refresh the stored access token and persist the replacement.

        Args:
            token: Optional token to refresh. Defaults to the currently stored
                token.

        Returns:
            The refreshed stored token.

        Raises:
            AuthenticationError: If no refresh token is available.
        """
        current_token = token or self._token_store.load()
        if current_token is None:
            raise AuthenticationError("No Procore token is available to refresh.")

        if current_token.refresh_token is None:
            raise AuthenticationError("No Procore refresh token is available.")

        refresh_token = current_token.refresh_token.get_secret_value()
        refreshed_response = self._oauth_client.refresh_access_token(refresh_token)
        refreshed_token = StoredToken.from_oauth_response(
            refreshed_response,
            existing_refresh_token=refresh_token,
        )
        self._token_store.save(refreshed_token)
        return refreshed_token

    def save_oauth_response(self, token_response: OAuthTokenResponse) -> StoredToken:
        """Persist the token returned by an initial OAuth exchange.

        Args:
            token_response: OAuth response returned after exchanging an
                authorization code.

        Returns:
            The stored token representation.
        """
        token = StoredToken.from_oauth_response(token_response)
        self._token_store.save(token)
        return token

    def clear_token(self) -> None:
        """Remove the saved token from the local token store."""
        self._token_store.clear()


def get_access_token() -> str:
    """Return a valid access token using the default token manager."""
    return TokenManager().get_access_token()
