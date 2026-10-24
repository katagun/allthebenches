from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .build import build, export_schema, load_dataset
from .collectors import SOURCES, collect, collect_openrouter_endpoints
from .feed_health import feed_health
from .reconcile import candidate_openrouter_ids, write_reconciliation_proposal


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="benches")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate curated dataset")
    validate.add_argument("--input", type=Path, default=Path("data/curated/dataset.json"))
    build_cmd = sub.add_parser("build", help="build static output from local curated data")
    build_cmd.add_argument("--input", type=Path, default=Path("data/curated/dataset.json"))
    build_cmd.add_argument("--output", type=Path, default=Path("web/public/data"))
    build_cmd.add_argument("--offline", action="store_true", help="preserve published feed metadata; ignore local staging files")
    schema_cmd = sub.add_parser("schema", help="regenerate JSON Schema and TypeScript declarations")
    schema_cmd.add_argument("--root", type=Path, default=Path.cwd())
    collect_cmd = sub.add_parser("collect", help="stage metadata feeds; never edits curated records")
    collect_cmd.add_argument("--source", choices=[*SOURCES, "all"], required=True)
    collect_cmd.add_argument("--staging", type=Path, default=Path("data/staging"))
    endpoints_cmd = sub.add_parser("collect-endpoints", help="collect endpoint quotes for exact catalog-matched curated IDs")
    endpoints_cmd.add_argument("--input", type=Path, default=Path("data/curated/dataset.json"))
    endpoints_cmd.add_argument("--staging", type=Path, default=Path("data/staging"))
    reconcile_cmd = sub.add_parser("reconcile", help="write review-only metadata proposal from staged feeds")
    reconcile_cmd.add_argument("--input", type=Path, default=Path("data/curated/dataset.json"))
    reconcile_cmd.add_argument("--staging", type=Path, default=Path("data/staging"))
    reconcile_cmd.add_argument("--output", type=Path, default=Path("data/staging/reconciliation-proposal.json"))
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            dataset = load_dataset(args.input)
            print(f"Valid dataset: {len(dataset.models)} models, {len(dataset.observations)} observations")
        elif args.command == "build":
            dataset = load_dataset(args.input)
            feeds = None
            staging = Path("data/staging")
            if not args.offline and staging.exists():
                feeds = feed_health(staging)
            manifest = build(dataset, args.output, feeds)
            export_schema(Path.cwd())
            print(manifest["snapshot_id"])
        elif args.command == "schema":
            export_schema(args.root)
            print("Wrote schemas/dataset.schema.json and web/src/generated/dataset.ts")
        elif args.command == "collect":
            sources = list(SOURCES) if args.source == "all" else [args.source]
            failures = 0
            for source in sources:
                result = collect(source, args.staging)
                print(f"{source}: {result['status']}")
                failures += result["status"] != "ok"
            return 1 if failures else 0
        elif args.command == "collect-endpoints":
            ids = candidate_openrouter_ids(args.input, args.staging)
            if not ids:
                print("No exact curated-name Atlas IDs exist in the staged OpenRouter catalog.")
                return 1
            result = collect_openrouter_endpoints(ids, args.staging)
            print(f"{result['status']}: {len(result['endpoints'])} endpoint detail records")
            return 0 if result["status"] == "ok" else 1
        elif args.command == "reconcile":
            result = write_reconciliation_proposal(args.input, args.staging, args.output)
            print(f"Wrote review-only proposal for {len(result['models'])} models and {len(result['labs'])} labs to {args.output}")
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
