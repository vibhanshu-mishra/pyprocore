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
4. Exchange the returned authorization code with the existing Python helper.
5. Run `procore-sdk auth refresh` to confirm refresh tokens work.

## Code

```python
from pyprocore.auth.token_manager import get_access_token
from pyprocore.core.exceptions import ProcoreError

try:
    token = get_access_token()
except ProcoreError as error:
    print(f"Authentication is not ready: {error}")
else:
    print(f"Authentication works. Token length: {len(token)}")
```

## Expected output

If authentication is ready, you should see a token length. The token value is
not printed.

For a real authenticated connectivity check, run:

```bash
procore-sdk auth refresh
procore-sdk doctor --live
```

## Common issues

- Missing `.env` values cause configuration errors.
- Expired access tokens require a valid refresh token.
- If refresh fails, repeat the OAuth authorization-code flow.
- Never paste client secrets, access tokens, refresh tokens, `.env` files, or
  token stores into public issues.
