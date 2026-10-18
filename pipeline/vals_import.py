"""Deterministically expand frozen Vals benchmark-page observations.

Network capture and exact-name matching are intentionally separate from this
adapter. The frozen snapshot preserves the source rows and capture identities.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "unnamed"


def _category(page: dict[str, Any]) -> str:
    text = ((page.get("title") or "") + " " + (page.get("meta_description") or "")).lower()
    for words, category in (
        (("multimodal",), "multimodal"),
        (("cyber", "security"), "cybersecurity"), (("math", "mathematics", "olympiad"), "math"),
        (("coding", "code", "programming", "terminal"), "coding"), (("legal", "law"), "legal"),
        (("medical", "clinical", "healthcare"), "medical"), (("finance", "financial", "mortgage", "tax"), "finance"),
        (("agent", "computer use", "tool-use"), "agent"), (("search", "web search"), "search"),
        (("reasoning", "scientific reasoning"), "reasoning"),
    ):
        if any(word in text for word in words):
            return category
    return "unknown"


def _modality(page: dict[str, Any]) -> str:
    text = ((page.get("title") or "") + " " + (page.get("meta_description") or "")).lower()
    if "multimodal" in text:
        return "multimodal"
    modalities = [name for token, name in (("text", "text"), ("image", "image"), ("video", "video"), ("audio", "audio"))
                  if token in text]
    if len(modalities) > 1:
        return ",".join(modalities)
    if modalities:
        return modalities[0]
    return "unknown"


def build_expansion(snapshot: dict[str, Any], curated: dict[str, Any]) -> dict[str, Any]:
    configs = {c["id"]: c for c in curated["configurations"]}
    benchmarks = {b["id"]: b for b in curated["benchmarks"]}
    profile = snapshot["model_profiles"]
    pages = {p["slug"]: p for p in snapshot["pages"]}
    sources = []
    for page in snapshot["pages"]:
        sources.append({"id": page["source_id"], "url": page["url"],
            "title": page["title"], "publisher": "Vals AI", "original_evaluator": "Vals AI",
            "retrieved_at": snapshot.get("retrieved_at"), "version": "Frozen public page capture",
            "content_sha256": page["sha256"], "license": None, "attribution": "Vals AI",
            "method": "Leaderboard observations were selected by exact canonical name or a separately documented verified profile-link mapping; values and units are unchanged.",
            "locator": "Leaderboard table; row number and exact displayed cells retained in the frozen snapshot."})
    for info in profile.values():
        sources.append({"id": info["source_id"], "url": info["url"], "title": info["name"] + " model profile",
            "publisher": "Vals AI", "original_evaluator": "Vals AI", "retrieved_at": snapshot.get("retrieved_at"),
            "version": "Frozen public model profile capture", "content_sha256": info["sha256"],
            "license": None, "attribution": "Vals AI", "method": info.get("mapping_evidence", "Captured model profile records displayed model identity and profile setting; profile settings are not assumed to apply to individual leaderboard scores.")})

    out = {k: [] for k in ("sources", "configurations", "benchmarks", "series", "observations")}
    out["sources"] = sources
    added_config_ids, added_benchmark_ids, added_series_ids = set(), set(), set()
    for row in snapshot["rows"]:
        model_id = row["model_id"]
        cfg = profile[row["profile_id"]]
        config_id = f"vals_{model_id}_{slug(row['profile_id'])}_unverified"
        conf = {"id": config_id, "model_id": model_id, "reasoning_label": None, "mode": "unknown"}
        old_conf = configs.get(config_id)
        if old_conf is not None and any(old_conf.get(k) != v for k, v in conf.items()):
            raise ValueError(f"configuration collision: {config_id}")
        if old_conf is None and config_id not in added_config_ids:
            out["configurations"].append(conf); added_config_ids.add(config_id)

        label = row["benchmark_label"]
        page = pages[row["source_slug"]]
        version = row.get("benchmark_version") or "unversioned-as-reported"
        bench_id = row.get("existing_benchmark_id") or f"vals_{slug(label)}_{slug(version)}"
        if bench_id in benchmarks:
            benchmark = benchmarks[bench_id]
            if benchmark["unit"] != row["unit"]:
                raise ValueError(f"unit mismatch against curated benchmark {bench_id}")
        elif bench_id not in added_benchmark_ids:
            out["benchmarks"].append({"id": bench_id, "family_id": f"vals_{slug(label)}",
                "name": label, "version": version, "category": _category(page), "modality": _modality(page),
                "metric_name": row["score_header"], "unit": row["unit"], "lower_bound": 0 if row["unit"] == "%" else None,
                "upper_bound": 100 if row["unit"] == "%" else None, "direction": "higher", "owner": "Vals AI",
                "documentation_url": row["benchmark_url"]})
            added_benchmark_ids.add(bench_id)

        extra = row.get("protocol_cells", {})
        series_key = (row["source_slug"], bench_id, json.dumps(extra, sort_keys=True))
        series_id = f"vals_{row['source_slug']}_{slug(label)}_{slug(json.dumps(extra, sort_keys=True))}"
        if series_key not in added_series_ids:
            out["series"].append({"id": series_id, "benchmark_id": bench_id,
                "protocol": f"Vals AI benchmark page; metric label {row['score_header']}; exact row cells are in the source snapshot.",
                "evaluator": "Vals AI", "comparability_status": "unknown",
                "comparability": "The leaderboard page does not disclose complete row-level evaluation setup.",
                "tools": "; ".join(f"{k}: {v}" for k, v in extra.items()) or None})
            added_series_ids.add(series_key)
        observation_id = row["observation_id"]
        if any(x["id"] == observation_id for x in out["observations"]):
            observation_id += "_" + slug(json.dumps(extra, sort_keys=True))
        out["observations"].append({"id": observation_id, "configuration_id": config_id,
            "benchmark_id": bench_id, "series_id": series_id, "value": row["value"], "unit": row["unit"],
            "source_id": row["source_id"], "locator": row["locator"], "evaluator": "Vals AI",
            "reporting_relationship": "evaluator_measurement", "setup": {
                "source_model_label": row["model_label"], "source_model_profile_url": cfg["url"],
                "source_model_profile_source_id": cfg["source_id"],
                "profile_setting_label": cfg.get("setting_label"), "profile_setting_value": cfg.get("setting_value"),
                "profile_setting_application": "not established for this leaderboard row",
                "model_mapping_evidence": cfg.get("mapping_evidence", "Exact source model display name matches canonical curated release."),
                "row_configuration_status": "unknown",
                "rank": row["rank"], "score_header": row["score_header"], "raw_score": row["raw_score"],
                "protocol_cells": extra, "benchmark_page_url": row["benchmark_url"],
                "uncertainty": "not displayed on the source leaderboard page"},
            "uncertainty": None, "review_state": "candidate", "supersedes": []})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", type=Path, required=True)
    ap.add_argument("--dataset", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    result = build_expansion(json.loads(a.snapshot.read_text()), json.loads(a.dataset.read_text()))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
