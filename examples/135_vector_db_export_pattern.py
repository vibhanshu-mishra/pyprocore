"""Build a local vector export manifest without installing a vector database.

PyProcore only prepares chunks and metadata. Users can later index reviewed
chunks in their own vector system if they choose.
"""

import json

from pyprocore.workflows import build_vector_index_manifest


def main() -> None:
    """Build and print a local vector manifest preview."""
    text = "\n".join(
        [
            "Placeholder project context paragraph one.",
            "Placeholder project context paragraph two.",
            "Placeholder project context paragraph three.",
        ]
    )
    manifest = build_vector_index_manifest(
        text, source_name="placeholder-context.md", chunk_size=80
    )
    print(json.dumps(manifest.model_dump(mode="json"), indent=2))
    print("\nNo vector database dependency is required.")


if __name__ == "__main__":
    main()
