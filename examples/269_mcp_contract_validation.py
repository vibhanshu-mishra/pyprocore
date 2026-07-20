"""Validate PyProcore's local MCP discovery contract.

This example checks the static MCP manifest, resources, prompts, capabilities,
and disabled-response shape. It does not call Procore or require credentials.
"""

from __future__ import annotations

from pyprocore.mcp import build_mcp_contract_report


def main() -> None:
    """Run the local MCP contract validation example."""
    report = build_mcp_contract_report()
    status = "passed" if report["passed"] else "failed"
    print(f"MCP contract validation {status}.")
    print(f"Findings: {report['finding_count']}")
    for result in report["results"]:
        print(f"- {result['name']}: {'pass' if result['passed'] else 'fail'}")


if __name__ == "__main__":
    main()
