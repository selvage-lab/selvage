"""Export stable JSON Schema contracts for evaluation payloads."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from selvage.src.eval.models import GoldenFixture, ReviewRun


def schema_documents() -> dict[str, dict]:
    """Return each public wire contract keyed by its canonical filename."""
    return {
        "review-run.v1.json": ReviewRun.model_json_schema(),
        "golden.v1.json": GoldenFixture.model_json_schema(),
    }


def export_schemas(output: Path) -> list[Path]:
    """Write deterministic JSON Schema documents into *output*."""
    output.mkdir(parents=True, exist_ok=True)
    written = []
    for filename, schema in schema_documents().items():
        destination = output / filename
        destination.write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.append(destination)
    return written


def main(argv: Sequence[str] | None = None) -> int:
    """Run the JSON Schema export CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("eval/schemas"),
        help="directory for generated schema files (default: eval/schemas)",
    )
    args = parser.parse_args(argv)
    for path in export_schemas(args.output):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
