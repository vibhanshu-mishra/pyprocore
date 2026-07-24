"""Local-only API maintenance assistant for user-provided OAS JSON files."""

from pyprocore.maintenance.coverage import analyze_pyprocore_coverage_gaps
from pyprocore.maintenance.drift import (
    compare_oas_catalogs,
    detect_added_endpoints,
    detect_changed_methods,
    detect_changed_operation_ids,
    detect_changed_parameters,
    detect_removed_endpoints,
    detect_risky_changes,
)
from pyprocore.maintenance.models import (
    MAINTENANCE_MODE,
    MAINTENANCE_SCHEMA_VERSION,
    ApiCoverageGap,
    ApiCoverageGapReport,
    ApiDriftReport,
    ApiEndpointChange,
    ApiMaintenanceFinding,
    ApiMaintenancePlan,
    ApiMaintenanceTask,
    ApiScaffoldCopyResult,
    ApiScaffoldFile,
    ApiScaffoldPlan,
)
from pyprocore.maintenance.plans import build_api_maintenance_plan
from pyprocore.maintenance.reports import (
    coverage_gap_report_to_markdown,
    drift_report_to_markdown,
    maintenance_plan_to_markdown,
    maintenance_report_to_json,
    scaffold_copy_result_to_markdown,
    scaffold_plan_to_markdown,
)
from pyprocore.maintenance.scaffold import (
    copy_read_only_endpoint_scaffold,
    plan_read_only_endpoint_scaffold,
)

__all__ = [
    "MAINTENANCE_MODE",
    "MAINTENANCE_SCHEMA_VERSION",
    "ApiCoverageGap",
    "ApiCoverageGapReport",
    "ApiDriftReport",
    "ApiEndpointChange",
    "ApiMaintenanceFinding",
    "ApiMaintenancePlan",
    "ApiMaintenanceTask",
    "ApiScaffoldCopyResult",
    "ApiScaffoldFile",
    "ApiScaffoldPlan",
    "analyze_pyprocore_coverage_gaps",
    "build_api_maintenance_plan",
    "compare_oas_catalogs",
    "copy_read_only_endpoint_scaffold",
    "coverage_gap_report_to_markdown",
    "detect_added_endpoints",
    "detect_changed_methods",
    "detect_changed_operation_ids",
    "detect_changed_parameters",
    "detect_removed_endpoints",
    "detect_risky_changes",
    "drift_report_to_markdown",
    "maintenance_plan_to_markdown",
    "maintenance_report_to_json",
    "plan_read_only_endpoint_scaffold",
    "scaffold_copy_result_to_markdown",
    "scaffold_plan_to_markdown",
]
