# Contributing

Thank you for your interest in improving PyProcore. Contributions, bug reports,
documentation fixes, and thoughtful questions are welcome.

## Local Development

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/vibhanshu-mishra/pyprocore.git
cd pyprocore
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
```

Install development dependencies:

```bash
pip install -e ".[dev]"
```

If you are working in a restricted environment where build isolation cannot
resolve PyPI dependencies, use:

```bash
pip install --no-build-isolation -e ".[dev]"
```

## Checks

Run the full local quality gate before opening a pull request:

```bash
make lint
make typecheck
make test
make coverage
```

## Coding Standards

- Format Python code with Black.
- Sort imports with isort.
- Keep flake8 clean.
- Keep mypy clean for the source package.
- Use typed public APIs.
- Add or update tests for behavior changes.
- Mock all HTTP requests in tests.
- Do not require live Procore access for unit tests.

## Pull Requests

Pull requests should include a clear summary, focused scope, and tests or
documentation updates where appropriate. Keep public APIs backwards compatible
unless the change is explicitly documented as breaking.

Before submitting, confirm:

- Relevant tests were added or updated.
- Documentation was updated when behavior or usage changed.
- `make lint` passed.
- `make typecheck` passed.
- `make test` passed.
- `make coverage` passed.

## Issues

Please use the GitHub issue templates when reporting bugs, requesting features,
or asking questions. Include enough detail for maintainers to reproduce or
understand the request.

## Secrets and Generated Files

Do not commit secrets, tokens, logs, `.env` files, token stores, build outputs,
or generated caches. This includes:

- Procore client secrets
- Access tokens
- Refresh tokens
- `.env`
- `token_store.json`
- `logs/`
- `dist/`
- `build/`
- `*.egg-info/`
- `.coverage`
- `htmlcov/`
- `__pycache__/`
