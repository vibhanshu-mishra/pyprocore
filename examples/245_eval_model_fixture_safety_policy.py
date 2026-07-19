"""Print the default offline model-response fixture safety policy."""

from pyprocore.app import model_response_fixture_policy_summary


def main() -> None:
    """Display local deterministic safety policy flags."""
    policy = model_response_fixture_policy_summary()
    print("Offline fixture policy:")
    print(f"Model calls: {policy['external_model_calls']}")
    print(f"Live Procore calls: {policy['live_procore_calls']}")
    print(f"Tool execution: {policy['tool_execution']}")


if __name__ == "__main__":
    main()
