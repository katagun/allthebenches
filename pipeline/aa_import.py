"""Deterministic adapter for extracted Artificial Analysis public model data.

The public page payload is not a stable API contract. Acquisition is separate:
provide an extracted object/list or Next.js flight capture and preserve its
byte hash. Only metrics with a documented score definition and scale are staged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


def _slugify(value: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", value.lower()))


def _dataset() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "data/curated/dataset.json"
    return json.loads(path.read_text(encoding="utf-8"))


_CANONICAL = _dataset()
MODEL_IDS = {_slugify(row["name"]): row["id"] for row in _CANONICAL["models"]}
CONFIGS_BY_MODEL: dict[str, list[dict[str, Any]]] = {}
for _row in _CANONICAL["configurations"]:
    CONFIGS_BY_MODEL.setdefault(_row["model_id"], []).append(_row)

# AA public methodology / evaluation pages define these fields' score concepts.
# Fraction-valued fields are multiplied by 100 only when the destination unit
# is percent. Elo, index points and signed Omniscience points stay unchanged.
BENCHMARKS: dict[str, dict[str, Any]] = {
    "aa_briefcase_v11": dict(family_id="aa_briefcase", name="AA-Briefcase", version="1.1", category="agent", modality="text", metric_name="combined Elo rating", unit="Elo", direction="higher", documentation_url="https://artificialanalysis.ai/methodology/intelligence-benchmarking", owner="Artificial Analysis"),
    "aa_gdpval_v21": dict(family_id="gdpval_aa", name="GDPval-AA", version="2.1", category="agent", modality="text", metric_name="Elo rating", unit="Elo", direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/gdpval-aa", owner="Artificial Analysis"),
    "aa_intelligence_index_v432": dict(family_id="artificial_analysis_index", name="Artificial Analysis Intelligence Index", version="v4.3.2", category="reasoning", modality="text", metric_name="index score", unit="points", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/artificial-analysis-intelligence-index", owner="Artificial Analysis"),
    "aa_automationbench_657": dict(family_id="automationbench_aa", name="AutomationBench-AA", version="unversioned-as-reported", subset="657-task AA held-out split", category="agent", modality="text", metric_name="mean task objective completion (guardrail-gated)", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/automationbench-aa", owner="Artificial Analysis"),
    "aa_scicode": dict(family_id="scicode", name="SciCode", version="1.0.1", category="reasoning", modality="text", metric_name="subproblem pass@1", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/scicode", owner="SciCode / Artificial Analysis"),
    "aa_hle_text": dict(family_id="hle", name="Humanity's Last Exam", version="2025-05 revision", subset="text-only", category="knowledge", modality="text", metric_name="pass@1 accuracy", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/humanitys-last-exam", owner="Center for AI Safety / Artificial Analysis"),
    "aa_gdp_pdf": dict(family_id="gdp_pdf", name="GDP.pdf", version="unversioned-as-reported", subset="100-task AA evaluation", category="agent", modality="text", metric_name="all-pass rate", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/methodology/intelligence-benchmarking", owner="Artificial Analysis"),
    "aa_critpt": dict(family_id="critpt", name="CritPt", version="unversioned-as-reported", subset="70-task AA evaluation", category="reasoning", modality="text", metric_name="pass@1", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/critpt", owner="Artificial Analysis"),
    "aa_omniscience_index": dict(family_id="aa_omniscience", name="AA-Omniscience", version="unversioned-as-reported", subset="Index", category="knowledge", modality="text", metric_name="Omniscience Index", unit="points", lower_bound=-100, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/omniscience", owner="Artificial Analysis"),
    "aa_omniscience_accuracy": dict(family_id="aa_omniscience", name="AA-Omniscience", version="unversioned-as-reported", subset="Accuracy", category="knowledge", modality="text", metric_name="accuracy", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/omniscience", owner="Artificial Analysis"),
    "aa_omniscience_hallucination": dict(family_id="aa_omniscience", name="AA-Omniscience", version="unversioned-as-reported", subset="Hallucination rate", category="knowledge", modality="text", metric_name="hallucination rate", unit="%", lower_bound=0, upper_bound=100, direction="lower", documentation_url="https://artificialanalysis.ai/evaluations/omniscience", owner="Artificial Analysis"),
    "aa_lcr_v11": dict(family_id="aa_lcr", name="Artificial Analysis Long Context Reasoning", version="1.1", category="reasoning", modality="text", metric_name="pass@1", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/artificial-analysis-long-context-reasoning", owner="Artificial Analysis"),
    "aa_gpqa_diamond": dict(family_id="gpqa", name="GPQA Diamond", version="unversioned-as-reported", subset="Diamond (198 questions)", category="knowledge", modality="text", metric_name="accuracy", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/gpqa", owner="GPQA / Artificial Analysis"),
    "aa_mmmu_pro": dict(family_id="mmmu_pro", name="MMMU-Pro", version="unversioned-as-reported", category="multimodal", modality="multimodal", metric_name="accuracy", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/mmmu-pro", owner="MMMU-Pro / Artificial Analysis"),
    "aa_ifbench": dict(family_id="ifbench", name="IFBench", version="unversioned-as-reported", category="reasoning", modality="text", metric_name="pass@1", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/ifbench", owner="Artificial Analysis"),
    "aa_enterprise_ops_657": dict(family_id="enterprise_ops_gym_aa", name="EnterpriseOps-Gym-AA", version="unversioned-as-reported", subset="657-task AA split", category="agent", modality="text", metric_name="strict pass@1 success rate", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/enterprise-ops-gym-aa", owner="Artificial Analysis"),
    "aa_itbench_sre": dict(family_id="itbench_aa", name="ITBench-AA SRE", version="unversioned-as-reported", subset="SRE, 59 tasks", category="agent", modality="text", metric_name="average precision at full recall", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/itbench-aa", owner="Artificial Analysis"),
    "aa_analyst_agent": dict(family_id="analyst_agent_aa", name="AA-AnalystAgent", version="unversioned-as-reported", subset="80-task AA evaluation", category="agent", modality="text", metric_name="headline pass^5 rate", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/aa-analyst-agent", owner="Artificial Analysis"),
    "aa_apex_agents": dict(family_id="apex_agents_aa", name="APEX-Agents-AA", version="unversioned-as-reported", subset="452-task AA split", category="agent", modality="text", metric_name="pass@1 success rate", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/apex-agents-aa", owner="Artificial Analysis"),
    "aa_terminal_hard": dict(family_id="terminal_bench_hard", name="Terminal-Bench Hard", version="unversioned-as-reported", category="agent", modality="text", metric_name="pass@1", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/terminalbench-hard", owner="Terminal-Bench / Artificial Analysis"),
    "aa_aime_2025": dict(family_id="aime", name="AIME", version="2025", subset="2025 exams", category="reasoning", modality="text", metric_name="accuracy", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/methodology", owner="Artificial Analysis"),
    "aa_tau3_banking": dict(family_id="tau3_banking", name="τ³-Banking", version="v1.0.1", subset="Banking", category="agent", modality="text", metric_name="pass@1 averaged across repeats", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/tau3-banking", owner="Sierra Research / Artificial Analysis"),
    "aa_tau2_telecom": dict(family_id="tau2_bench", name="τ²-Bench", version="unversioned-as-reported", subset="Telecom", category="agent", modality="text", metric_name="success rate", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/tau2-bench", owner="Sierra Research / Artificial Analysis"),
    "aa_mlcr_hard": dict(family_id="mlcr_aa", name="MLCR-AA", version="unversioned-as-reported", subset="expert + compound (hard)", category="knowledge", modality="text", metric_name="overall pass@1", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/mlcr-aa", owner="Wisedocs / Artificial Analysis"),
    "aa_livecodebench": dict(family_id="livecodebench", name="LiveCodeBench", version="unversioned-as-reported", category="coding", modality="text", metric_name="pass@1", unit="%", lower_bound=0, upper_bound=100, direction="higher", documentation_url="https://artificialanalysis.ai/evaluations/livecodebench", owner="LiveCodeBench / Artificial Analysis"),
}

# (source key, benchmark id, scale, citation/evidence). Only verified contracts
# are mapped. Potentially ambiguous standalone fields are accounted as excluded
# in the audit instead of being guessed into this list.
FIELD_MAP = [
    ("intelligenceIndex", "aa_intelligence_index_v432", 1, "composite index; excluded when AA marks it estimated"),
    ("hle", "aa_hle_text", 100, "text-only HLE pass@1 fraction"),
    ("gpqa", "aa_gpqa_diamond", 100, "GPQA Diamond accuracy fraction"),
    ("critpt", "aa_critpt", 100, "CritPt pass@1 fraction"),
    ("omniscience", "aa_omniscience_index", 1, "signed index points"),
    ("omniscienceAccuracy", "aa_omniscience_accuracy", 100, "accuracy fraction"),
    ("omniscienceHallucinationRate", "aa_omniscience_hallucination", 100, "hallucination-rate fraction"),
    ("lcr", "aa_lcr_v11", 100, "AA-LCR v1.1 pass@1 fraction"),
    ("ifbench", "aa_ifbench", 100, "IFBench pass@1 fraction"),
    ("terminalbenchHard", "aa_terminal_hard", 100, "Terminal-Bench Hard pass@1 fraction"),
    ("gdpval", "aa_gdpval_v21", 1, "GDPval-AA v2.1 Elo"),
    ("mmmuPro", "aa_mmmu_pro", 100, "MMMU-Pro accuracy fraction"),
    ("aime25", "aa_aime_2025", 100, "AIME 2025 accuracy fraction"),
    ("scicode", "aa_scicode", 100, "SciCode subproblem pass@1 fraction"),
    ("gdpPdfAllPass", "aa_gdp_pdf", 100, "GDP.pdf all-pass rate fraction"),
    ("terminalBench40", "terminal_bench_4", 100, "Terminal-Bench 4.0 pass@1 fraction"),
    ("frontierCode", "frontiercode_v11", 100, "FrontierCode v1.1 Main task success fraction"),
    ("terminalBenchScience", "terminal_science_01", 100, "Terminal-Bench Science 0.1.0 pass@1 fraction"),
    ("terminalBench21", "terminal_bench_21", 100, "Terminal-Bench 2.1 mean pass@1 fraction"),
    ("automationBenchPartialScore", "aa_automationbench_657", 100, "AutomationBench-AA mean objective completion fraction, zeroed on guardrail breach"),
    ("enterpriseOpsGym", "aa_enterprise_ops_657", 100, "EnterpriseOps-Gym-AA strict pass@1 fraction"),
    ("itBenchSre", "aa_itbench_sre", 100, "ITBench-AA SRE average precision at full recall fraction"),
    ("analystAgent", "aa_analyst_agent", 100, "AA-AnalystAgent pass^5 fraction"),
    ("apexAgents", "aa_apex_agents", 100, "APEX-Agents-AA pass@1 fraction"),
    ("harveyLab", "harvey_lab_aa_v11", 100, "Harvey LAB-AA v1.1 hallucination-gated all-pass fraction"),
    ("tauBanking", "aa_tau3_banking", 100, "τ³-Banking pass@1 averaged across repeats fraction"),
    ("tau2", "aa_tau2_telecom", 100, "τ²-Bench Telecom success-rate fraction"),
    ("mlcrOverall", "aa_mlcr_hard", 100, "MLCR-AA overall pass@1 fraction"),
    ("livecodebench", "aa_livecodebench", 100, "LiveCodeBench pass@1 fraction; upstream problem range/version not present in the captured field"),
]


def extract_flight_payload(raw: bytes) -> list[dict[str, Any]]:
    text = raw.decode("utf-8")
    decoder = json.JSONDecoder()
    current_marker, models_marker = '"currentModel":', '"models":['
    current_pos, models_pos = text.find(current_marker), text.find(models_marker)
    if current_pos < 0 or models_pos < 0:
        raise ValueError("payload is not a recognized Artificial Analysis model-page flight capture")
    current, _ = decoder.raw_decode(text, current_pos + len(current_marker))
    models, _ = decoder.raw_decode(text, models_pos + len('"models":'))
    if not isinstance(current, dict) or not isinstance(models, list):
        raise ValueError("flight payload currentModel/models fields have unexpected types")
    if not any(isinstance(row, dict) and row.get("id") == current.get("id") for row in models):
        models.append(current)
    return [row for row in models if isinstance(row, dict)]


def _load_models(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("currentModel"), dict):
        payload = payload["currentModel"]
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list) and all(isinstance(row, dict) for row in payload):
        return payload
    raise ValueError("expected a model object, currentModel wrapper, or list of model objects")


def _resolve_model(row: dict[str, Any]) -> str | None:
    release = row.get("release") if isinstance(row.get("release"), dict) else {}
    for slug in (release.get("slug"), row.get("slug")):
        if isinstance(slug, str) and slug in MODEL_IDS:
            return MODEL_IDS[slug]
    return None


def _resolve_configuration(row: dict[str, Any], model_id: str) -> tuple[str | None, dict[str, Any] | None]:
    effort = row.get("effort") if isinstance(row.get("effort"), dict) else {}
    label = effort.get("slug")
    if not label and isinstance(row.get("suffix"), str):
        suffix = _slugify(row["suffix"])
        if suffix in {"default", "non-reasoning", "minimal", "low", "medium", "high", "xhigh", "max", "none"}:
            label = suffix
        elif suffix.startswith("default-"):
            label = "default"
    if label:
        # Keep configuration identity local to this source adapter. A generic
        # `max` label from another source can carry different runtime defaults;
        # source-specific IDs also keep reruns stable as other fragments merge.
        config_id = f"aa_{model_id}_{label.replace('-', '_')}"
        if any(c.get("id") == config_id for c in CONFIGS_BY_MODEL.get(model_id, [])):
            return config_id, None
        config = {"id": config_id, "model_id": model_id,
                  "reasoning_label": label, "reasoning_budget_tokens": None,
                  "mode": "disabled" if label in {"none", "non-reasoning"} else "default" if label == "default" else "enabled",
                  "precision": None}
        return config_id, config
    # AA exposes a canonical release row but no effort label. Keep it distinct
    # from known-effort observations with a stable AA-specific unknown config.
    unknown_id = f"aa_{model_id}_unknown"
    if any(c.get("id") == unknown_id for c in CONFIGS_BY_MODEL.get(model_id, [])):
        return unknown_id, None
    return unknown_id, {
        "id": unknown_id, "model_id": model_id,
        "reasoning_label": None, "reasoning_budget_tokens": None,
        "mode": "unknown", "precision": None,
    }


def _bench_entity(bench_id: str) -> dict[str, Any]:
    if bench_id not in BENCHMARKS:
        meta = next(b for b in _CANONICAL["benchmarks"] if b["id"] == bench_id)
    else:
        meta = BENCHMARKS[bench_id]
    return {"id": bench_id, **meta}


def _bench_meta(bench_id: str) -> dict[str, Any]:
    if bench_id in BENCHMARKS:
        return BENCHMARKS[bench_id]
    return next(b for b in _CANONICAL["benchmarks"] if b["id"] == bench_id)


def _observation(row: dict[str, Any], canonical_model: str, config_id: str,
                 bench_id: str, field: str, raw_value: float, scale: float,
                 source_id: str, config_key: str) -> tuple[dict[str, Any], dict[str, Any]]:
    meta = _bench_meta(bench_id)
    value = raw_value * scale
    provider_key = _slugify(str(row.get("slug", row.get("id", "provider-model"))))
    series_id = f"series_aa_{canonical_model}_{config_key}_{provider_key}_{bench_id}"
    observation_id = f"o_aa_{canonical_model}_{config_key}_{provider_key}_{bench_id}_20261018"
    series = {
        "id": series_id, "benchmark_id": bench_id,
        "protocol": "Artificial Analysis public model-page result",
        "protocol_version": meta["version"], "evaluator": "Artificial Analysis",
        "comparability": "AA identifies the benchmark and headline metric; detailed prompt, tool, sampling and serving settings are not all exposed in the captured model record.",
        "comparability_status": "unknown", "tools": None, "sampling": None,
        "judge": None, "budget": None, "setup_fingerprint": None,
    }
    if bench_id == "aa_scicode":
        series["comparability"] += " Artificial Analysis marks SciCode under review following an independent audit of the SciCode-Verified dataset."
    setup: dict[str, Any] = {
        "aa_model_id": str(row.get("id", row.get("slug", ""))),
        "aa_release_slug": (row.get("release") or {}).get("slug") if isinstance(row.get("release"), dict) else None,
        "aa_effort_slug": (row.get("effort") or {}).get("slug") if isinstance(row.get("effort"), dict) else None,
        "source_field_value": raw_value,
        "source_field_unit": "fraction" if scale == 100 else meta["unit"],
    }
    if scale == 100:
        setup["normalization"] = {"formula": "source fraction × 100", "reason": "AA serializes this percentage metric as a 0–1 fraction."}
    if bench_id == "aa_scicode":
        setup["source_caveat"] = {
            "status": "Artificial Analysis marks SciCode under review",
            "reason": "Independent audit of the SciCode-Verified dataset.",
            "url": "https://artificialanalysis.ai/evaluations/scicode",
        }
    obs = {
        "id": observation_id, "configuration_id": config_id,
        "benchmark_id": bench_id, "series_id": series_id, "value": value,
        "unit": meta["unit"], "source_id": source_id,
        "locator": f"models[{row.get('slug')}].{field}",
        "evaluator": "Artificial Analysis", "reporting_relationship": "evaluator_measurement",
        "reported_at": None, "evaluated_at": None, "setup": setup,
        "uncertainty": None, "review_state": "candidate", "supersedes": [],
    }
    return obs, series


def build_fragment(payload: Any, raw_bytes: bytes, retrieved_at: str) -> dict[str, Any]:
    digest = hashlib.sha256(raw_bytes).hexdigest()
    models = _load_models(payload)
    source_id = "aa_public_pages_20261018"
    sources = [{
        "id": source_id,
        "url": "https://artificialanalysis.ai/models/mistral-large-4",
        "title": "Artificial Analysis public model-page serialization (18 October 2026)",
        "publisher": "Artificial Analysis", "original_evaluator": "Artificial Analysis",
        "retrieved_at": retrieved_at, "published_at": None,
        "version": "Public model-page serialization captured 2026-10-18",
        "content_sha256": digest, "license": None,
        "attribution": "Artificial Analysis; source page and documented API reference linked in the AA coverage audit.",
        "method": "Extracted public model records from the page's Next.js flight payload. This representation is not a stable API contract.",
        "locator": "Serialized models array and currentModel; field-level locators are recorded on each observation.",
        "excerpt": None,
    }]
    observations: list[dict[str, Any]] = []
    series_by_id: dict[str, dict[str, Any]] = {}
    configurations: dict[str, dict[str, Any]] = {}
    unresolved: list[dict[str, Any]] = []

    # Use the explicit benchmark component records when present. They retain
    # their protocol identity instead of treating cost/time fields as results.
    field_map = list(FIELD_MAP)
    for row in models:
        canonical_model = _resolve_model(row)
        if canonical_model is None:
            continue
        config_id, new_config = _resolve_configuration(row, canonical_model)
        if config_id is None:
            if any(isinstance(row.get(field), (int, float)) and not isinstance(row.get(field), bool) for field, *_ in field_map):
                unresolved.append({"model": canonical_model, "aa_slug": row.get("slug"), "reason": "no unique exact setting mapping"})
            continue
        if new_config:
            configurations[new_config["id"]] = new_config
        config_key = _slugify(config_id)
        # Aggregate index is a derived AA composite. Only import when AA says
        # it is measured rather than an estimated carry-forward.
        for field, bench_id, scale, _evidence in field_map:
            raw_value = row.get(field)
            if not isinstance(raw_value, (int, float)) or isinstance(raw_value, bool):
                continue
            if field == "intelligenceIndex" and row.get("intelligenceIndexIsEstimated") is True:
                continue
            if not isinstance(raw_value, (int, float)):
                continue
            obs, series = _observation(row, canonical_model, config_id, bench_id, field, float(raw_value), scale, source_id, config_key)
            observations.append(obs)
            series_by_id[series["id"]] = series

        # AA publishes component scores in intelligenceIndexEvaluations. Cost,
        # time and token fields in the same objects are intentionally ignored.
        evaluations = row.get("intelligenceIndexEvaluations")
        briefcase = next((x for x in evaluations if isinstance(x, dict) and x.get("slug") == "aa-briefcase"), None) if isinstance(evaluations, list) else None
        elo = briefcase.get("score") if briefcase else None
        if isinstance(elo, (int, float)) and not isinstance(elo, bool):
            bench_id = "aa_briefcase_v11"
            obs, series = _observation(row, canonical_model, config_id, bench_id, "intelligenceIndexEvaluations[aa-briefcase].score", float(elo), 1, source_id, config_key)
            obs["locator"] = f"models[{row.get('slug')}].intelligenceIndexEvaluations[aa-briefcase].score"
            bd = row.get("briefcaseBreakdown")
            overall = bd.get("overall") if isinstance(bd, dict) else None
            lower, upper = (overall or {}).get("lower95ci"), (overall or {}).get("upper95ci")
            if isinstance(lower, (int, float)) and isinstance(upper, (int, float)):
                obs["uncertainty"] = {"type": "confidence_interval", "confidence_level": 0.95, "lower": float(lower), "upper": float(upper), "unit": "Elo"}
            observations.append(obs)
            series_by_id[series["id"]] = series

    # Add configurations only when the matching row publishes the setting.
    # Build these deterministically as part of the fragment, never as aliases.
    existing_benchmarks = {b["id"] for b in _CANONICAL["benchmarks"]}
    used_benchmarks = {o["benchmark_id"] for o in observations}
    benchmarks = [_bench_entity(bid) for bid in sorted(used_benchmarks - existing_benchmarks)]
    return {
        "sources": sources if observations else [],
        "benchmarks": benchmarks,
        "configurations": list(configurations.values()),
        "series": list(series_by_id.values()),
        "observations": observations,
    }


def _load_payload(raw: bytes) -> Any:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return extract_flight_payload(raw)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=Path, help="Extracted AA JSON or Next.js flight capture")
    parser.add_argument("--retrieved-at", default="2026-10-18T14:22:00Z")
    parser.add_argument("--output", type=Path, help="Write the schema-compatible fragment here (stdout by default)")
    args = parser.parse_args()
    raw = args.payload.read_bytes()
    fragment = build_fragment(_load_payload(raw), raw, args.retrieved_at)
    rendered = json.dumps(fragment, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
