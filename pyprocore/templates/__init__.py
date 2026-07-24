"""Optional starter template helpers for PyProcore.

Templates are static local examples only. They are not executed, installed, or
hosted by PyProcore, and they do not call Procore or external AI/model APIs.
"""

from pyprocore.templates.copy import copy_starter_template, template_copy_result_to_jsonable
from pyprocore.templates.models import (
    StarterTemplateFile,
    StarterTemplateMetadata,
    TemplateCopyFileResult,
    TemplateCopyFinding,
    TemplateCopyResult,
)
from pyprocore.templates.registry import (
    FASTAPI_READ_API_TEMPLATE_NAME,
    get_starter_template,
    iter_template_files,
    list_starter_templates,
)
from pyprocore.templates.reports import (
    template_copy_result_to_json,
    template_copy_result_to_markdown,
    template_metadata_to_json,
    template_metadata_to_markdown,
    template_to_summary_dict,
    templates_to_json,
    templates_to_markdown,
)

__all__ = [
    "FASTAPI_READ_API_TEMPLATE_NAME",
    "StarterTemplateFile",
    "StarterTemplateMetadata",
    "TemplateCopyFileResult",
    "TemplateCopyFinding",
    "TemplateCopyResult",
    "copy_starter_template",
    "get_starter_template",
    "iter_template_files",
    "list_starter_templates",
    "template_copy_result_to_json",
    "template_copy_result_to_jsonable",
    "template_copy_result_to_markdown",
    "template_metadata_to_json",
    "template_metadata_to_markdown",
    "template_to_summary_dict",
    "templates_to_json",
    "templates_to_markdown",
]
