#!/usr/bin/env python3
"""Capture current endpoint evidence for exact IDs already on curated routes.

Discovery and capture only; review routes before importing metrics. An existing
output is reused as last-good evidence, and failed responses remain marked stale.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.collectors import collect_openrouter_endpoints  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/curated/dataset.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--previous", type=Path, help="Reviewed last-good endpoint snapshot to seed retention")
    args = parser.parse_args()
    dataset = json.loads(args.dataset.read_text())
    ids = sorted({r["upstream_model_id"] for r in dataset["routes"]
                  if r["id"].startswith("openrouter:") and r.get("upstream_model_id")})
    with tempfile.TemporaryDirectory() as directory:
        staging = Path(directory)
        if args.previous:
            shutil.copyfile(args.previous, staging / "openrouter-endpoints.json")
        elif args.output.exists():
            shutil.copyfile(args.output, staging / "openrouter-endpoints.json")
        result = collect_openrouter_endpoints(ids, staging)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(staging / "openrouter-endpoints.json", args.output)
    print(json.dumps({"status": result["status"], "attempts": result["attempts"]}))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
