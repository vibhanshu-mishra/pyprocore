"""Resolvers for automation workflow inputs."""

from __future__ import annotations

from pyprocore.automation.models import AutomationInput
from pyprocore.core.exceptions import ValidationError
from pyprocore.models import RFI, Project, Submittal
from pyprocore.services.rfis import get_rfi
from pyprocore.services.search import find_project, find_rfi, find_submittal
from pyprocore.services.submittals import get_submittal


def resolve_project(input_data: AutomationInput) -> Project:
    """Resolve the project referenced by workflow input.

    Args:
        input_data: Automation request containing a project ID, name, or number.

    Returns:
        The resolved project model.

    Raises:
        ValidationError: If no project identifier is provided.
    """
    if input_data.project_id is not None:
        if input_data.project_id <= 0:
            raise ValidationError("project_id must be a positive integer.")
        return Project(id=input_data.project_id)

    if input_data.project_number:
        return find_project(number=input_data.project_number, company_id=input_data.company_id)

    if input_data.project_name:
        return find_project(input_data.project_name, company_id=input_data.company_id)

    raise ValidationError("Provide project_id, project_name, or project_number.")


def resolve_rfi(input_data: AutomationInput, project_id: int) -> RFI:
    """Resolve the RFI referenced by workflow input.

    Args:
        input_data: Automation request containing an RFI ID or number.
        project_id: Resolved Procore project ID.

    Returns:
        The resolved RFI model.

    Raises:
        ValidationError: If no RFI identifier is provided.
    """
    if input_data.item_id is not None:
        return get_rfi(project_id, input_data.item_id)

    if input_data.item_number:
        return find_rfi(project_id, number=input_data.item_number)

    raise ValidationError("Provide item_id or item_number for the RFI workflow.")


def resolve_submittal(input_data: AutomationInput, project_id: int) -> Submittal:
    """Resolve the submittal referenced by workflow input.

    Args:
        input_data: Automation request containing a submittal ID or number.
        project_id: Resolved Procore project ID.

    Returns:
        The resolved submittal model.

    Raises:
        ValidationError: If no submittal identifier is provided.
    """
    if input_data.item_id is not None:
        return get_submittal(project_id, input_data.item_id)

    if input_data.item_number:
        return find_submittal(project_id, number=input_data.item_number)

    raise ValidationError("Provide item_id or item_number for the submittal workflow.")
