# Getting Started

This guide gets PyProcore running locally without making any live Procore calls
until you choose to authenticate.

## Install From Source

```bash
git clone https://github.com/vibhanshu-mishra/pyprocore.git
cd pyprocore
python3 -m venv .venv
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

For contributor checks, install the development extras:

```bash
python3 -m pip install -e ".[dev]"
```

For local documentation work, install the optional docs extra:

```bash
python3 -m pip install -e ".[docs]"
```

## Basic CLI Check

```bash
procore-sdk --help
procore-sdk doctor
```

When testing unreleased local CLI changes, prefer:

```bash
PYTHONPATH=. procore-sdk --help
PYTHONPATH=. python3 -m pyprocore.app --help
```

## Check Examples Without Credentials

The examples check compiles every example script and confirms it has a main
guard. It never executes examples, imports PyProcore, or calls Procore.

```bash
make examples-check
```

## First Useful Commands

After `.env` is configured and OAuth has been completed:

```bash
procore-sdk companies
procore-sdk projects
procore-sdk rfis --project "$PROCORE_PROJECT_ID"
procore-sdk submittals --project "$PROCORE_PROJECT_ID"
```

## Where Outputs Go

Examples and workflow commands usually write to local folders such as:

- `downloads/`
- `exports/`
- `project-context/`
- command-specific `--output-dir` locations

These folders can contain project data. Review them before sharing or uploading.

## Keep Secrets Out Of Git

Do not commit `.env`, token stores, logs with private data, downloaded files, or
generated workflow outputs. PyProcore tries to redact secrets in logs, but local
files are still your responsibility.
