"""Read-only project-management extras services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.models import (
    ActionPlan,
    ActionPlanChangeHistoryEvent,
    CalendarItem,
    CoordinationIssue,
    CoordinationIssueActivity,
    CoordinationIssueChangeHistoryEvent,
    CoordinationIssueFilterOption,
    Form,
    FormTemplate,
    ProjectSchedule,
    ScheduleImportStatus,
    ScheduleIntegration,
    ScheduleResourceAssignment,
    ScheduleSettings,
    ScheduleType,
    Task,
    TaskRequestedChange,
)
from pyprocore.services.financials import FinancialsService


class ProjectManagementService(FinancialsService):
    """Service for read-only schedule, task, coordination, form, and action-plan data."""

    def __init__(self, client: ProcoreClient | None = None) -> None:
        """Initialize the service.

        Args:
            client: Optional shared Procore HTTP client.
        """
        super().__init__(client=client)

    def get_project_schedule(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> ProjectSchedule:
        """Return read-only project schedule metadata."""
        response = self._get_project_payload(
            company_id,
            project_id,
            endpoints.project_schedule(project_id),
            params=params,
            extra_params=extra_params,
        )
        return ProjectSchedule.model_validate(response)

    def get_schedule_settings(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> ScheduleSettings:
        """Return read-only project schedule settings."""
        response = self._get_project_payload(
            company_id,
            project_id,
            endpoints.schedule_settings(project_id),
            params=params,
            extra_params=extra_params,
        )
        return ScheduleSettings.model_validate(response)

    def get_schedule_type(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> ScheduleType:
        """Return read-only project schedule type metadata."""
        response = self._get_project_payload(
            company_id,
            project_id,
            endpoints.schedule_type(project_id),
            params=params,
            extra_params=extra_params,
        )
        return ScheduleType.model_validate(response)

    def get_schedule_integration(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> ScheduleIntegration:
        """Return read-only project schedule integration metadata."""
        response = self._get_project_payload(
            company_id,
            project_id,
            endpoints.schedule_integration(project_id),
            params=params,
            extra_params=extra_params,
        )
        return ScheduleIntegration.model_validate(response)

    def get_schedule_import_status(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> ScheduleImportStatus:
        """Return read-only status for the latest project schedule import."""
        response = self._get_project_payload(
            company_id,
            project_id,
            endpoints.schedule_import_status(project_id),
            params=params,
            extra_params=extra_params,
        )
        return ScheduleImportStatus.model_validate(response)

    def list_schedule_resource_assignments(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ScheduleResourceAssignment]:
        """Return project schedule resource assignments."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.schedule_resource_assignments(project_id),
            ScheduleResourceAssignment,
            ("schedule_resource_assignments", "resource_assignments", "assignments"),
            params=params,
            extra_params=extra_params,
        )

    def get_schedule_resource_assignment(
        self,
        company_id: int | None,
        project_id: int,
        schedule_resource_assignment_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> ScheduleResourceAssignment:
        """Return one project schedule resource assignment."""
        return self._get_project_resource(
            company_id,
            project_id,
            schedule_resource_assignment_id,
            "schedule_resource_assignment_id",
            endpoints.schedule_resource_assignment(project_id, schedule_resource_assignment_id),
            ScheduleResourceAssignment,
            params=params,
            extra_params=extra_params,
        )

    def list_tasks(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Task]:
        """Return read-only project tasks."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.tasks(project_id),
            Task,
            ("tasks", "schedule_tasks"),
            params=params,
            extra_params=extra_params,
        )

    def get_task(
        self,
        company_id: int | None,
        project_id: int,
        task_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> Task:
        """Return one read-only project task."""
        return self._get_project_resource(
            company_id,
            project_id,
            task_id,
            "task_id",
            endpoints.task(project_id, task_id),
            Task,
            params=params,
            extra_params=extra_params,
        )

    def list_task_requested_changes(
        self,
        company_id: int | None,
        project_id: int,
        task_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[TaskRequestedChange]:
        """Return read-only requested changes for one task."""
        self._validate_positive_id(task_id, "task_id")
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.task_requested_changes(project_id, task_id),
            TaskRequestedChange,
            ("task_requested_changes", "requested_changes"),
            params=params,
            extra_params=extra_params,
        )

    def list_calendar_items(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CalendarItem]:
        """Return read-only project calendar items."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.calendar_items(project_id),
            CalendarItem,
            ("calendar_items",),
            params=params,
            extra_params=extra_params,
        )

    def get_calendar_item(
        self,
        company_id: int | None,
        project_id: int,
        calendar_item_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> CalendarItem:
        """Return one read-only project calendar item."""
        return self._get_project_resource(
            company_id,
            project_id,
            calendar_item_id,
            "calendar_item_id",
            endpoints.calendar_item(project_id, calendar_item_id),
            CalendarItem,
            params=params,
            extra_params=extra_params,
        )

    def list_coordination_issues(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CoordinationIssue]:
        """Return read-only project coordination issues."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.coordination_issues(project_id),
            CoordinationIssue,
            ("coordination_issues",),
            params=params,
            extra_params=extra_params,
        )

    def get_coordination_issue(
        self,
        company_id: int | None,
        project_id: int,
        coordination_issue_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> CoordinationIssue:
        """Return one read-only project coordination issue."""
        return self._get_project_resource(
            company_id,
            project_id,
            coordination_issue_id,
            "coordination_issue_id",
            endpoints.coordination_issue(project_id, coordination_issue_id),
            CoordinationIssue,
            params=params,
            extra_params=extra_params,
        )

    def list_coordination_issue_change_history(
        self,
        company_id: int | None,
        project_id: int,
        coordination_issue_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CoordinationIssueChangeHistoryEvent]:
        """Return read-only change history for one coordination issue."""
        self._validate_positive_id(coordination_issue_id, "coordination_issue_id")
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.coordination_issue_change_history(project_id, coordination_issue_id),
            CoordinationIssueChangeHistoryEvent,
            ("coordination_issue_change_history", "change_history", "events"),
            params=params,
            extra_params=extra_params,
        )

    def list_coordination_issue_activity_feed(
        self,
        company_id: int | None,
        project_id: int,
        coordination_issue_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CoordinationIssueActivity]:
        """Return read-only activity feed entries for one coordination issue."""
        self._validate_positive_id(coordination_issue_id, "coordination_issue_id")
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.coordination_issue_activity_feed(project_id, coordination_issue_id),
            CoordinationIssueActivity,
            ("coordination_issue_activity_feed", "activity_feed", "activities"),
            params=params,
            extra_params=extra_params,
        )

    def list_coordination_issue_filter_options(
        self,
        company_id: int | None,
        project_id: int,
        *,
        option_type: str | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CoordinationIssueFilterOption]:
        """Return read-only coordination issue filter options."""
        option_params = dict(extra_params)
        if option_type is not None:
            option_params["option_type"] = option_type
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.coordination_issue_filter_options(project_id),
            CoordinationIssueFilterOption,
            ("coordination_issue_filter_options", "filter_options", "options"),
            params=params,
            extra_params=option_params,
        )

    def list_forms(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Form]:
        """Return read-only project forms."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.forms(project_id),
            Form,
            ("forms",),
            params=params,
            extra_params=extra_params,
        )

    def get_form(
        self,
        company_id: int | None,
        project_id: int,
        form_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> Form:
        """Return one read-only project form."""
        return self._get_project_resource(
            company_id,
            project_id,
            form_id,
            "form_id",
            endpoints.form(project_id, form_id),
            Form,
            params=params,
            extra_params=extra_params,
        )

    def list_form_templates(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[FormTemplate]:
        """Return read-only project form templates."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.form_templates(project_id),
            FormTemplate,
            ("form_templates", "templates"),
            params=params,
            extra_params=extra_params,
        )

    def list_action_plans(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ActionPlan]:
        """Return read-only project action plans."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.action_plans(project_id),
            ActionPlan,
            ("action_plans",),
            params=params,
            extra_params=extra_params,
        )

    def get_action_plan(
        self,
        company_id: int | None,
        project_id: int,
        action_plan_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> ActionPlan:
        """Return one read-only project action plan."""
        return self._get_project_resource(
            company_id,
            project_id,
            action_plan_id,
            "action_plan_id",
            endpoints.action_plan(project_id, action_plan_id),
            ActionPlan,
            params=params,
            extra_params=extra_params,
        )

    def list_action_plan_change_history_events(
        self,
        company_id: int | None,
        project_id: int,
        action_plan_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ActionPlanChangeHistoryEvent]:
        """Return read-only change history events for one action plan."""
        self._validate_positive_id(action_plan_id, "action_plan_id")
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.action_plan_change_history_events(project_id, action_plan_id),
            ActionPlanChangeHistoryEvent,
            ("action_plan_change_history_events", "change_history_events", "events"),
            params=params,
            extra_params=extra_params,
        )


def get_project_schedule(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> ProjectSchedule:
    """Return read-only project schedule metadata."""
    return ProjectManagementService(client=client).get_project_schedule(
        company_id,
        project_id,
        **params,
    )


def get_schedule_settings(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> ScheduleSettings:
    """Return read-only project schedule settings."""
    return ProjectManagementService(client=client).get_schedule_settings(
        company_id,
        project_id,
        **params,
    )


def get_schedule_type(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> ScheduleType:
    """Return read-only project schedule type metadata."""
    return ProjectManagementService(client=client).get_schedule_type(
        company_id,
        project_id,
        **params,
    )


def get_schedule_integration(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> ScheduleIntegration:
    """Return read-only project schedule integration metadata."""
    return ProjectManagementService(client=client).get_schedule_integration(
        company_id,
        project_id,
        **params,
    )


def get_schedule_import_status(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> ScheduleImportStatus:
    """Return read-only project schedule import status."""
    return ProjectManagementService(client=client).get_schedule_import_status(
        company_id,
        project_id,
        **params,
    )


def list_schedule_resource_assignments(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[ScheduleResourceAssignment]:
    """Return project schedule resource assignments."""
    return ProjectManagementService(client=client).list_schedule_resource_assignments(
        company_id,
        project_id,
        **params,
    )


def get_schedule_resource_assignment(
    company_id: int | None,
    project_id: int,
    schedule_resource_assignment_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> ScheduleResourceAssignment:
    """Return one project schedule resource assignment."""
    return ProjectManagementService(client=client).get_schedule_resource_assignment(
        company_id,
        project_id,
        schedule_resource_assignment_id,
        **params,
    )


def list_tasks(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[Task]:
    """Return read-only project tasks."""
    return ProjectManagementService(client=client).list_tasks(company_id, project_id, **params)


def get_task(
    company_id: int | None,
    project_id: int,
    task_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> Task:
    """Return one read-only project task."""
    return ProjectManagementService(client=client).get_task(
        company_id,
        project_id,
        task_id,
        **params,
    )


def list_task_requested_changes(
    company_id: int | None,
    project_id: int,
    task_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[TaskRequestedChange]:
    """Return read-only requested changes for one task."""
    return ProjectManagementService(client=client).list_task_requested_changes(
        company_id,
        project_id,
        task_id,
        **params,
    )


def list_calendar_items(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[CalendarItem]:
    """Return read-only project calendar items."""
    return ProjectManagementService(client=client).list_calendar_items(
        company_id,
        project_id,
        **params,
    )


def get_calendar_item(
    company_id: int | None,
    project_id: int,
    calendar_item_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> CalendarItem:
    """Return one read-only project calendar item."""
    return ProjectManagementService(client=client).get_calendar_item(
        company_id,
        project_id,
        calendar_item_id,
        **params,
    )


def list_coordination_issues(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[CoordinationIssue]:
    """Return read-only project coordination issues."""
    return ProjectManagementService(client=client).list_coordination_issues(
        company_id,
        project_id,
        **params,
    )


def get_coordination_issue(
    company_id: int | None,
    project_id: int,
    coordination_issue_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> CoordinationIssue:
    """Return one read-only project coordination issue."""
    return ProjectManagementService(client=client).get_coordination_issue(
        company_id,
        project_id,
        coordination_issue_id,
        **params,
    )


def list_coordination_issue_change_history(
    company_id: int | None,
    project_id: int,
    coordination_issue_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[CoordinationIssueChangeHistoryEvent]:
    """Return read-only change history for one coordination issue."""
    return ProjectManagementService(client=client).list_coordination_issue_change_history(
        company_id,
        project_id,
        coordination_issue_id,
        **params,
    )


def list_coordination_issue_activity_feed(
    company_id: int | None,
    project_id: int,
    coordination_issue_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[CoordinationIssueActivity]:
    """Return read-only activity feed entries for one coordination issue."""
    return ProjectManagementService(client=client).list_coordination_issue_activity_feed(
        company_id,
        project_id,
        coordination_issue_id,
        **params,
    )


def list_coordination_issue_filter_options(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[CoordinationIssueFilterOption]:
    """Return read-only coordination issue filter options."""
    return ProjectManagementService(client=client).list_coordination_issue_filter_options(
        company_id,
        project_id,
        **params,
    )


def list_forms(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[Form]:
    """Return read-only project forms."""
    return ProjectManagementService(client=client).list_forms(company_id, project_id, **params)


def get_form(
    company_id: int | None,
    project_id: int,
    form_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> Form:
    """Return one read-only project form."""
    return ProjectManagementService(client=client).get_form(
        company_id,
        project_id,
        form_id,
        **params,
    )


def list_form_templates(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[FormTemplate]:
    """Return read-only project form templates."""
    return ProjectManagementService(client=client).list_form_templates(
        company_id,
        project_id,
        **params,
    )


def list_action_plans(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[ActionPlan]:
    """Return read-only project action plans."""
    return ProjectManagementService(client=client).list_action_plans(
        company_id,
        project_id,
        **params,
    )


def get_action_plan(
    company_id: int | None,
    project_id: int,
    action_plan_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> ActionPlan:
    """Return one read-only project action plan."""
    return ProjectManagementService(client=client).get_action_plan(
        company_id,
        project_id,
        action_plan_id,
        **params,
    )


def list_action_plan_change_history_events(
    company_id: int | None,
    project_id: int,
    action_plan_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[ActionPlanChangeHistoryEvent]:
    """Return read-only change history events for one action plan."""
    return ProjectManagementService(client=client).list_action_plan_change_history_events(
        company_id,
        project_id,
        action_plan_id,
        **params,
    )
