"""Typed models for the PyProcore agent tool registry."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from pyprocore.models.base import ProcoreModel


class AgentToolCategory(str, Enum):
    """High-level category for an agent-facing PyProcore tool."""

    RESOURCE = "resource"
    SEARCH = "search"
    WORKFLOW = "workflow"
    LOCAL_EXPORT = "local_export"
    VALIDATION = "validation"


class AgentToolPermission(str, Enum):
    """Permission metadata describing what a tool may do."""

    READ_PROCORE = "read_procore"
    READ_LOCAL_FILES = "read_local_files"
    WRITE_LOCAL_FILES = "write_local_files"
    VALIDATE_LOCAL_FILES = "validate_local_files"


class AgentToolSafety(str, Enum):
    """Safety classification for an agent-facing tool."""

    READ_ONLY = "read_only"
    LOCAL_FILE_OUTPUT = "local_file_output"


class AgentTool(ProcoreModel):
    """Metadata describing one PyProcore operation available to agents.

    Attributes:
        name: Stable tool identifier, such as ``procore.find_rfi``.
        title: Human-readable tool label.
        description: Beginner-friendly summary of what the tool does.
        category: High-level tool category.
        input_schema: JSON-schema-like description of accepted inputs.
        output_schema: JSON-schema-like description of returned data.
        permissions: Required permission classes.
        requires_auth: Whether the tool needs configured Procore authentication.
        calls_live_api: Whether execution would call the Procore API.
        produces_files: Whether execution may write local output files.
        side_effects: Human-readable side-effect notes.
        safety_level: Safety classification.
        service_path: Python service module path when applicable.
        operation_path: Python function path when applicable.
        cli_command: Equivalent CLI command shape when available.
        examples: Short usage examples.
        version_added: PyProcore version where this tool metadata was introduced.
    """

    name: str
    title: str
    description: str
    category: AgentToolCategory
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    permissions: list[AgentToolPermission] = Field(default_factory=list)
    requires_auth: bool = True
    calls_live_api: bool = True
    produces_files: bool = False
    side_effects: list[str] = Field(default_factory=list)
    safety_level: AgentToolSafety = AgentToolSafety.READ_ONLY
    service_path: str | None = None
    operation_path: str | None = None
    cli_command: str | None = None
    examples: list[str] = Field(default_factory=list)
    version_added: str = "2.2.0"


class AgentToolRegistry(ProcoreModel):
    """Static collection of PyProcore agent tool metadata."""

    registry_version: str = "1"
    tools: list[AgentTool] = Field(default_factory=list)

    @property
    def tool_count(self) -> int:
        """Return the number of registered tools."""
        return len(self.tools)


class AgentManifest(ProcoreModel):
    """Serializable manifest for agent and orchestration integrations.

    Attributes:
        package_name: Python package name.
        package_version: Installed PyProcore version.
        registry_version: Agent registry schema version.
        generated_at: UTC timestamp when the manifest was generated.
        tool_count: Number of tools in the manifest.
        tools: Sorted tool metadata.
    """

    package_name: str
    package_version: str
    registry_version: str
    generated_at: datetime
    tool_count: int
    tools: list[AgentTool]
