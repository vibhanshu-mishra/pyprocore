# Authentication

PyProcore uses Procore OAuth and reads configuration from environment variables
or a local `.env` file in your current working directory.

## `.env` Setup

Copy the sample file and fill in your own values:

```bash
cp .env.example .env
```

Required values:

```bash
PROCORE_CLIENT_ID=your_client_id
PROCORE_CLIENT_SECRET=your_client_secret_keep_private
PROCORE_REDIRECT_URI=http://localhost:8080/callback
PROCORE_LOGIN_URL=https://login.procore.com
PROCORE_API_BASE=https://api.procore.com
PROCORE_COMPANY_ID=123456
```

Environment variables already set in your shell take precedence over `.env`
values.

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

## Common Errors

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
