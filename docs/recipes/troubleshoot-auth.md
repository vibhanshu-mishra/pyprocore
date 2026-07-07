# Troubleshoot Authentication

## What this does

Helps you check the most common OAuth and token setup problems.

## When to use it

Use this when PyProcore raises an authentication error, cannot refresh a token,
or cannot make authenticated Procore requests.

Start with the local diagnostics command:

```bash
procore-sdk doctor
procore-sdk auth status
```

These commands check configuration, token storage, Python version, and writable
SDK folders without making live Procore calls.

## Before you start

You need a `.env` file with:

```bash
PROCORE_CLIENT_ID=your_client_id
PROCORE_CLIENT_SECRET=your_client_secret
PROCORE_REDIRECT_URI=your_redirect_uri
PROCORE_LOGIN_URL=https://login.procore.com
PROCORE_API_BASE=https://api.procore.com
PROCORE_COMPANY_ID=your_company_id
```

You also need to complete OAuth once so PyProcore has an access token and,
ideally, a refresh token.

## Auth flow

1. Run `procore-sdk doctor`.
2. Run `procore-sdk auth status`.
3. If no token is stored, run `procore-sdk auth login-url` and open the URL.
4. Copy the returned authorization code and run:

   ```bash
   procore-sdk auth exchange-code YOUR_AUTHORIZATION_CODE
   ```

5. Run `procore-sdk auth refresh` to confirm refresh tokens work.

## Code

```bash
procore-sdk doctor
procore-sdk auth login-url
procore-sdk auth exchange-code YOUR_AUTHORIZATION_CODE
procore-sdk auth status
```

## Expected output

If authentication is ready, `procore-sdk auth status` should show that the
token store exists, the access token is present, and the refresh token is
present. Token values are never printed.

For a real authenticated connectivity check, run:

```bash
procore-sdk auth refresh
procore-sdk doctor --live
```

## Common issues

- Missing `.env` values cause configuration errors.
- Authorization codes are short-lived. Generate a fresh code with
  `procore-sdk auth login-url` if exchange fails.
- Expired access tokens require a valid refresh token.
- If refresh fails, repeat the OAuth authorization-code flow.
- Never paste client secrets, access tokens, refresh tokens, `.env` files, or
  token stores into public issues.
