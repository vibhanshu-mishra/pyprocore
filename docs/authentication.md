# Authentication

PyProcore uses Procore OAuth and reads configuration from environment variables
or a local `.env` file in your current working directory.

Two auth modes are supported:

- `authorization_code`: the default user OAuth flow with login URL, code
  exchange, access token, and refresh token.
- `client_credentials`: server-to-server auth for Procore Data Connection Apps.
  This mode uses client ID and client secret, does not require a redirect URI,
  and may not return a refresh token.

Authorization Code is for user-based OAuth and access is limited by the
authenticated user's permissions. Client Credentials is for unattended
server-to-server jobs and does not use browser login or a redirect URI. Its
access is limited by the Data Connection App connection and service-account
permissions configured in Procore. Unknown auth modes are rejected.

## `.env` Setup

Copy the sample file and fill in your own values:

```bash
cp .env.example .env
```

Required values:

```bash
PROCORE_CLIENT_ID=your_client_id
PROCORE_CLIENT_SECRET=your_client_secret_keep_private
PROCORE_AUTH_MODE=authorization_code
PROCORE_REDIRECT_URI=http://localhost:8080/callback
PROCORE_LOGIN_URL=https://login.procore.com
PROCORE_API_BASE=https://api.procore.com
PROCORE_COMPANY_ID=123456
```

Environment variables already set in your shell take precedence over `.env`
values.

For a Data Connection App, use:

```bash
PROCORE_AUTH_MODE=client_credentials
PROCORE_CLIENT_ID=your_client_id
PROCORE_CLIENT_SECRET=your_client_secret_keep_private
PROCORE_LOGIN_URL=https://login.procore.com
PROCORE_API_BASE=https://api.procore.com
PROCORE_COMPANY_ID=123456
```

`PROCORE_REDIRECT_URI` is not required in `client_credentials` mode.

## OAuth Login URL

Generate the Procore authorization URL:

```bash
procore-sdk auth login-url
```

Open the URL in a browser, approve access, and copy the `code` value from the
redirect URL.

## Exchange Code

```bash
procore-sdk auth exchange-code YOUR_AUTHORIZATION_CODE
```

This saves OAuth tokens to the local token store used by the SDK.

## Check Auth Status

```bash
procore-sdk auth status
procore-sdk auth status --json
```

Status output avoids printing access tokens, refresh tokens, client secrets, or
Authorization headers.

## Refresh Tokens

```bash
procore-sdk auth refresh
```

Normal SDK calls refresh expired access tokens automatically when a refresh token
is available. The manual command is useful while troubleshooting.

## Client Credentials Token

For Data Connection Apps, set `PROCORE_AUTH_MODE=client_credentials`, then run:

```bash
procore-sdk auth client-credentials-token
```

This requests and saves a client credentials access token. Procore may omit a
refresh token for this grant type; PyProcore treats that as normal and requests
a fresh client credentials token when needed.

## Scheduled Export Planning

For enterprise scheduled exports, prefer `client_credentials` with a Procore
Data Connection App. Phase 9B adds local-only scheduled export plan validation
and dry-run manifest helpers. These commands do not require credentials, do not
call Procore, and should be run before any real scheduled export job:

```bash
procore-sdk scheduled-export validate examples/configs/scheduled_export_client_credentials.json
procore-sdk scheduled-export dry-run examples/configs/scheduled_export_client_credentials.json
```

Keep `.env`, token stores, logs, downloads, generated exports, and private
project data outside source control. Use separate credentials and token stores
for sandbox and production.

## Doctor

```bash
procore-sdk doctor
procore-sdk doctor --json
```

`doctor` checks local configuration and token-store state. Use `doctor --live`
only when you intentionally want an authenticated connectivity check.

## Production vs Sandbox

Make sure your login and API base URLs match the environment where your OAuth
app, company, project, and user access exist. A token from one environment will
not usually work against another.

## Token Store Warning

The token store contains sensitive OAuth material. Do not commit it, paste it
into issues, or upload it to shared systems. Treat it like a password file.
The default path is `pyprocore/auth/token_store.json`; managed environments can
pass an explicit `TokenStore` path. Legacy stores without `auth_mode` metadata
remain authorization-code stores. Never commit `.env`, token stores, logs,
downloads, or generated exports.

## Common Errors

### 401 Unauthorized

Check for a missing, expired, malformed, or wrong-environment token. Authorization
Code can renew with a stored refresh token. Client Credentials normally has no
refresh token; PyProcore renews it by requesting a new access token.

### 403 Forbidden

Check app-company connection, company/project/tool access, and either the user's
or Data Connection App/service-account permissions. Sandbox credentials and URLs
must not be mixed with production credentials and URLs.

### Unknown client

The client ID or login environment is probably wrong. Confirm
`PROCORE_CLIENT_ID`, `PROCORE_LOGIN_URL`, and whether you are using sandbox or
production.

### Invalid grant

The authorization code may be expired, already used, copied incorrectly, or from
a different redirect URI. Generate a fresh login URL and exchange the new code.

### Redirect URI mismatch

The redirect URI in `.env` must exactly match the redirect URI configured for the
OAuth app in Procore.

### App not connected to company

Authentication succeeded, but Procore rejected the company context. Confirm the
company ID, install/connect the app to that company, and make sure the OAuth user
has access.

### Token store missing

Run the login URL and exchange-code flow once. If the token store was deleted,
repeat the OAuth setup.

For `client_credentials` mode, run:

```bash
procore-sdk auth client-credentials-token
```
