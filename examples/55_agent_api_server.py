"""Show how to start the local PyProcore agent API server.

This example intentionally does not start a long-running server. Use the printed
CLI command when you want to run the local discovery API yourself.
"""


def main() -> None:
    """Print beginner-friendly local agent API server instructions."""
    print("Start the local PyProcore agent API server with:")
    print("  procore-sdk agent serve --port 8765")
    print()
    print("Then inspect discovery endpoints:")
    print("  http://127.0.0.1:8765/health")
    print("  http://127.0.0.1:8765/agent/manifest")
    print("  http://127.0.0.1:8765/agent/tools")
    print()
    print("The server is local-first and does not execute tools in Phase 7B.")


if __name__ == "__main__":
    main()
