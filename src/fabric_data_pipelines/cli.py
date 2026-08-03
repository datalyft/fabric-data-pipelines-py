"""Command-line interface for fabric-data-pipelines."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fabric_data_pipelines.codegen import codegen_pipeline
from fabric_data_pipelines.errors import PipelineImportError
from fabric_data_pipelines.importing import load_item, pipeline_from_json
from fabric_data_pipelines.pipeline import Pipeline


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="fabric-data-pipelines",
        description="Tools for Microsoft Fabric data pipelines as code.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    codegen = sub.add_parser(
        "codegen",
        help="Generate Python source from a Fabric item folder or pipeline JSON file.",
    )
    codegen.add_argument(
        "path",
        type=Path,
        help="Path to a *.DataPipeline folder or pipeline-content.json / .json file",
    )
    codegen.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write generated Python to this path (default: stdout)",
    )
    codegen.add_argument(
        "--name",
        help="Pipeline name (required when input is raw pipeline JSON without an item folder)",
    )

    args = parser.parse_args(argv)
    if args.command == "codegen":
        return _cmd_codegen(args.path, output=args.output, name=args.name)
    parser.error(f"Unknown command: {args.command}")
    return 2


def _cmd_codegen(path: Path, *, output: Path | None, name: str | None) -> int:
    try:
        pipeline = _load_for_codegen(path, name=name)
        source = codegen_pipeline(pipeline)
    except (PipelineImportError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if output is None:
        sys.stdout.write(source)
        if not source.endswith("\n"):
            sys.stdout.write("\n")
    else:
        output.write_text(source if source.endswith("\n") else source + "\n", encoding="utf-8")
    return 0


def _load_for_codegen(path: Path, *, name: str | None) -> Pipeline:
    if path.is_dir() or (path.is_file() and path.name == "pipeline-content.json"):
        return load_item(path)
    if path.is_file() and path.suffix == ".json":
        if not name:
            raise PipelineImportError(
                "When codegen input is a JSON file, pass --name for the pipeline name"
            )
        return pipeline_from_json(path.read_text(encoding="utf-8"), name=name)
    raise PipelineImportError(f"Expected a *.DataPipeline folder or JSON file, got '{path}'")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
