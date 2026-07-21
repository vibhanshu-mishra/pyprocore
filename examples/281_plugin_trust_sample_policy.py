"""Print a conservative metadata-only plugin trust policy.

This example does not install plugins, import plugin modules, execute plugin
code, call Procore, or contact external services.
"""

from __future__ import annotations

import json

from pyprocore.plugins import export_trust_policy_template


def main() -> None:
    """Print the trust policy template as JSON."""
    policy = export_trust_policy_template()
    print("Sample local plugin trust policy:")
    print(json.dumps(policy.model_dump(mode="json"), indent=2))
    print("\nRemote install, execution, and arbitrary imports remain denied.")


if __name__ == "__main__":
    main()
