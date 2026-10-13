"""Script to export OpenAPI specification to docs/openapi.json."""

import json
from pathlib import Path

from omnimission.main import create_app


def export_openapi() -> None:
    """Generate and write OpenAPI JSON schema."""
    app = create_app()
    openapi_schema = app.openapi()

    # Locate repo docs directory
    repo_root = Path(__file__).resolve().parents[5]
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    output_path = docs_dir / "openapi.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"OpenAPI schema successfully written to {output_path}")


if __name__ == "__main__":
    export_openapi()
