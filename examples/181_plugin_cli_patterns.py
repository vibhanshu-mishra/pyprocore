"""Show safe plugin CLI command patterns.

These are command examples only. The script does not run subprocesses, call
Procore, install plugins, or execute plugin code.
"""


def main() -> None:
    """Print safe local plugin CLI patterns."""
    commands = [
        "procore-sdk plugins list",
        "procore-sdk plugins show csv_exporter_plugin",
        "procore-sdk plugins manifest --json",
        "procore-sdk plugins sample-manifest --json",
        "procore-sdk plugins validate ./plugin-manifest.json",
    ]
    print("Safe plugin CLI patterns")
    for command in commands:
        print(f"- {command}")
    print("These commands inspect or validate metadata only.")


if __name__ == "__main__":
    main()
