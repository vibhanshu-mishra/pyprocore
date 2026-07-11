# Contributing

Thank you for helping improve PyProcore. This project is a Python SDK and
automation foundation for Procore data workflows, including typed API access,
downloads, local exports, AI-ready packages, workflow plans, and CLI tooling.

## Local Development

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/vibhanshu-mishra/pyprocore.git
cd pyprocore
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
```

Install the editable package with development tools:

```bash
python3 -m pip install -e ".[dev]"
```

If build isolation cannot reach PyPI in your environment, try:

```bash
python3 -m pip install --no-build-isolation -e ".[dev]"
```

## Local Checks

Run focused checks while developing:

```bash
make examples-check
make test
make coverage
make lint
make typecheck
python3 -m black --check .
python3 -m isort --check-only .
```

Run the release-readiness gate before a larger pull request:

```bash
make release-check
```

Unit tests must not require live Procore access. Mock HTTP calls and keep tests
safe for contributors without credentials.

## Branch and Commit Guidance

- Keep branches focused on one change.
- Use descriptive branch names, such as `fix-token-refresh-message` or
  `add-drawings-example`.
- Keep commits small enough to review.
- Do not mix unrelated refactors with feature or bug-fix work.

## Adding a New Endpoint

When adding a Procore endpoint:

1. Add endpoint helpers in `pyprocore/core/endpoints.py`.
2. Add or update typed models in `pyprocore/models/`.
3. Add service functions in `pyprocore/services/`.
4. Add object-client wrappers in `pyprocore/client.py` when appropriate.
5. Add CLI commands only when useful for users.
6. Add mocked unit tests for success and common failures.
7. Add docs, examples, or recipes for user-facing workflows.

Do not add Procore mutation behavior unless it is explicitly in scope and
reviewed carefully.

## Docs, Examples, and Tests

Documentation changes should be beginner-friendly and avoid real company,
project, RFI, submittal, or token values.

Examples should:

- use environment variables or placeholder IDs
- avoid secrets
- include `if __name__ == "__main__":`
- be syntax-checkable with `make examples-check`

Tests should:

- use `unittest` and `unittest.mock`
- avoid live Procore calls
- avoid reading real `.env` or token stores
- cover both success and failure behavior

## Secret Safety

Do not commit secrets or generated private project outputs.

Never commit or paste:

- Procore client secrets
- access tokens
- refresh tokens
- Authorization headers
- `.env` files
- `token_store.json`
- logs containing credentials
- generated downloads or workflow outputs with sensitive project data

If you accidentally expose a secret, rotate it immediately before opening a
public issue or pull request.

## Opening a Pull Request

Before opening a pull request:

- summarize what changed and why
- mention any user-facing behavior changes
- add or update tests
- add or update docs/examples when relevant
- confirm no secrets or generated outputs are committed
- run the local checks listed above

Large changes are easier to review when an issue exists first.
