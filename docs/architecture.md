# Architecture

PyProcore is structured as a layered Python SDK. Each layer has a focused
responsibility and should stay independently testable.

## Layers

### `pyprocore.auth`

Handles OAuth token exchange, token persistence, expiry detection, and refresh.
Application code should not manage bearer tokens directly.

### `pyprocore.core`

Contains configuration, endpoint path helpers, the reusable HTTP client,
logging, and custom exceptions. The client owns request execution, retries,
pagination, authentication headers, and error normalization.

### `pyprocore.models`

Defines typed Pydantic models for Procore resources. Models preserve unknown
fields so the SDK can remain tolerant of Procore response changes while still
offering typed access to known fields.

### `pyprocore.services`

Provides resource-oriented service functions for companies, projects, RFIs,
submittals, and file downloads. Services compose the core client and typed
models without exposing raw HTTP mechanics.

### Search and Resolver Layer

The search layer resolves human-friendly names and numbers to typed Procore
resources. It is intentionally built on existing services rather than separate
endpoint logic.

### Automation Layer

The automation layer packages resolved RFIs and submittals into typed workflow
objects for downstream systems. It coordinates project resolution, item
resolution, metadata retrieval, and optional attachment downloads.

### CLI

The command-line interface exposes common service, resolver, download, and
workflow packaging operations. It prints JSON-friendly output suitable for
scripts and manual inspection.

## Integration Boundaries

AI assistants, Power Automate flows, Outlook integrations, and other
application-specific workflows should live outside the core SDK. Keeping those
integrations separate protects the SDK from vendor-specific runtime assumptions
and keeps PyProcore reusable for many automation environments.
