"""Network-free importer adapters; all acquisition goes through an evidence archive.

Pinned suites remain pinned until their release/metric contracts are reviewed.
Unknown Vals identities and changed table contracts are reported, never guessed.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
from typing import Protocol
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]


class Archive(Protocol):
    work: Path

    def fetch(self, url: str) -> Path: ...


class Tables(HTMLParser):
    """Extract displayed table cells and model links without executing source HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[dict]] = []
        self.table: list[dict] | None = None
        self.row: dict | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if self.table is not None:
                raise ValueError("Nested Vals tables require review")
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.row = {"cells": [], "hrefs": [], "header": False}
        elif tag in {"td", "th"} and self.row is not None:
            self.cell = []
            self.row["header"] |= tag == "th"
        elif tag == "a" and self.row is not None:
            href = dict(attrs).get("href", "")
            if urlparse(href).path.startswith("/models/"):
                self.row["hrefs"].append(urlparse(href).path)

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            self.row["cells"].append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None


def _vals(archive: Archive, retrieved_at: str, dataset: dict) -> tuple[dict, dict]:
    from pipeline.vals_import import build_expansion

    baseline = json.loads((ROOT / "data/expansion/vals-all-source-snapshot-2026-10-18.json").read_text())
    snapshot = deepcopy(baseline)
    snapshot["retrieved_at"] = retrieved_at
    snapshot["rows"] = []
    decisions = []
    # Only explicitly reviewed protocol fields distinguish repeated model entries.
    # Price, duration, rank and scores are measurements, never identity keys.
    protocol_fields = {"web_search": ("Search Tool",)}

    def identity(slug, label, href, cells):
        return (slug, label, href, *(cells.get(field) for field in protocol_fields.get(slug, ())))

    contracts = {}
    for row in baseline["rows"]:
        key = identity(row["source_slug"], row["model_label"], row["model_page_href"], row["protocol_cells"])
        contracts.setdefault(key, []).append(row)
    for page in snapshot["pages"]:
        raw = archive.fetch(page["url"]).read_bytes()
        parser = Tables()
        parser.feed(raw.decode("utf-8"))
        expected = page["table_headers"]
        matches = [table for table in parser.tables if table and table[0]["cells"] == expected]
        if len(matches) != 1:
            raise ValueError(f"Vals table contract drift at {page['url']}: expected one table with {expected}")
        page["sha256"] = hashlib.sha256(raw).hexdigest()
        page["bytes"] = len(raw)
        rows = matches[0][1:]
        if not rows:
            raise ValueError(f"Empty Vals leaderboard: {page['url']}")
        identity_counts = Counter(
            identity(page["slug"], r["cells"][expected.index("Model")], r["hrefs"][0],
                     dict(zip(expected, r["cells"], strict=True)))
            for r in rows if len(r["cells"]) == len(expected) and len(set(r["hrefs"])) == 1
        )
        for position, row in enumerate(rows, 1):
            cells = row["cells"]
            decision = {"page": page["slug"], "row": position, "cells": cells}
            if len(cells) != len(expected) or len(set(row["hrefs"])) > 1:
                raise ValueError(f"Vals row shape drift: {page['slug']} row {position}")
            label = cells[expected.index("Model")]
            href = row["hrefs"][0] if row["hrefs"] else ""
            key = identity(page["slug"], label, href, dict(zip(expected, cells, strict=True)))
            if identity_counts[key] > 1 or len(contracts.get(key, [])) > 1:
                decisions.append({**decision, "status": "unresolved_duplicate_identity"})
                continue
            templates = contracts.get(key, [])
            if not templates:
                decisions.append({**decision, "status": "unresolved_identity"})
                continue
            template = templates[0]
            score = cells[expected.index(template["score_header"])].strip()
            pattern = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)" + ("%" if template["unit"] == "%" else "")
            if re.fullmatch(pattern, score) is None:
                decisions.append({**decision, "status": "excluded_unreviewed_score_format"})
                continue
            value = float(score.rstrip("%"))
            if not math.isfinite(value) or (template["unit"] == "%" and not 0 <= value <= 100):
                raise ValueError(f"Invalid Vals score: {score}")
            item = deepcopy(template)
            item.update(value=value, raw_score=score, rank=cells[expected.index("Rank")],
                        rank_population=len(rows), cells=cells,
                        protocol_cells={k: v for k, v in zip(expected, cells, strict=True)
                                        if k not in {"Rank", "Model", template["score_header"]}},
                        locator=f"table row {position}; model link {href}; exact displayed score {score}")
            snapshot["rows"].append(item)
            decisions.append({**decision, "status": "candidate_import", "observation_id": item["observation_id"]})
    fragment = build_expansion(snapshot, dataset)
    # Profile evidence remains the reviewed frozen capture, not a fresh observation.
    profiles = {p["source_id"] for p in baseline["model_profiles"].values()}
    for source in fragment["sources"]:
        if source["id"] in profiles:
            source["retrieved_at"] = baseline.get("retrieved_at")
    return fragment, {"source": "Vals", "retrieved_at": retrieved_at, "decisions": decisions,
                      "counts": {"rows_seen": len(decisions), "candidate_observations": len(snapshot["rows"])},
                      "scope": "Reviewed pages and exact page/model/link contracts only; new identities require review."}


def collect_and_parse(source: str, archive: Archive, retrieved_at: str, dataset: dict) -> tuple[dict, dict]:
    """Fetch archived evidence and return candidate entities plus source coverage."""
    if source == "epoch":
        from pipeline.epoch_import import URL, stage
        mappings = json.loads((ROOT / "data/mappings/epoch_models.json").read_text())
        return stage(archive.fetch(URL).read_bytes(), mappings, retrieved_at)
    if source == "vals":
        return _vals(archive, retrieved_at, dataset)
    if source == "aa":
        from pipeline import aa_import as aa
        if any(dataset.get(key) != aa._CANONICAL.get(key) for key in ("models", "configurations", "benchmarks")):
            raise ValueError("AA adapter requires the current canonical dataset; custom identity contracts need review")
        raw = archive.fetch("https://artificialanalysis.ai/models/mistral-large-4").read_bytes()
        try:
            payload = aa._load_payload(raw)
        except ValueError:
            chunks = []
            for encoded in re.findall(r"self\.__next_f\.push\((\[.*?\])\)</script>", raw.decode("utf-8"), re.S):
                chunk = json.loads(encoded)
                if len(chunk) == 2 and chunk[0] == 1 and isinstance(chunk[1], str):
                    chunks.append(chunk[1])
            if not chunks:
                raise ValueError("AA HTML has no recognized Next.js flight chunks") from None
            payload = aa.extract_flight_payload("".join(chunks).encode())
        fragment = aa.build_fragment(payload, raw, retrieved_at)
        models = aa._load_models(payload)
        decisions = []
        for row in models:
            model = aa._resolve_model(row)
            config = aa._resolve_configuration(row, model)[0] if model else None
            decisions.append({"source_model": row.get("slug"), "model_id": model,
                              "status": "mapped" if config else "unresolved_identity_or_configuration"})
        return fragment, {"source": "Artificial Analysis", "decisions": decisions,
                          "counts": {"source_models": len(models), "candidate_observations": len(fragment["observations"])},
                          "scope": "Reviewed FIELD_MAP metrics only; estimated intelligence indices excluded. Embedded metrics outside that contract are not imported."}
    if source == "arena":
        from pipeline import arena_import as arena
        info = json.loads(archive.fetch(f"https://huggingface.co/api/datasets/{arena.DATASET}").read_text())
        revision = info.get("sha", "")
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("Arena API did not return an immutable revision")
        tree_url = f"https://huggingface.co/api/datasets/{arena.DATASET}/tree/{revision}?recursive=true&expand=false"
        listing = json.loads(archive.fetch(tree_url).read_text())
        entries = [e for e in listing if e.get("type") == "file" and "/latest-" in e.get("path", "")]
        if not entries:
            raise ValueError("Arena manifest contains no reviewed latest partitions")
        files = {}
        for entry in entries:
            path = archive.fetch(f"{arena.REPO_URL}/resolve/{revision}/" + entry["path"])
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            expected = (entry.get("lfs") or {}).get("oid")
            if expected and expected != digest:
                raise ValueError(f"Arena checksum mismatch: {entry['path']}")
            partition = entry["path"].split("/", 1)[0]
            if partition in files:
                raise ValueError(f"Ambiguous Arena partition: {partition}")
            files[partition] = path
            entry["sha256"] = digest
        fragment, coverage = arena.build(dataset, files, entries, revision=revision, retrieved_at=retrieved_at)
        coverage["retrieved_at"] = retrieved_at
        coverage["scope"] = "Current HF revision resolved once and archived at immutable SHA; new metrics remain review candidates."
        for item in fragment["sources"]:
            item["retrieved_at"] = retrieved_at
        return fragment, coverage
    if source == "livebench":
        from pipeline import livebench_import as lb
        homepage = archive.fetch("https://livebench.ai/").read_text()
        discovered_assets = re.findall(r'(?:src=["\'])([^"\']*static/js/main\.[^"\']+\.js)', homepage)
        pinned_asset = urlparse(lb.FRONTEND_URL).path
        changed_assets = [asset for asset in discovered_assets if urlparse(urljoin("https://livebench.ai/", asset)).path != pinned_asset]
        paths = [archive.fetch(url) for url in (lb.V1_URL, lb.V2_URL, lb.V1_CATEGORIES_URL,
                                               lb.V2_CATEGORIES_URL, lb.V2_BREAKDOWN_URL)]
        js_path = archive.fetch(lb.FRONTEND_URL)
        metadata = lb.extract_frontend_models(js_path.read_text())
        if not metadata:
            raise ValueError("LiveBench frontend model metadata was empty")
        archive.work.mkdir(parents=True, exist_ok=True)
        config = archive.work / "livebench-frontend-config.json"
        config.write_text(json.dumps({"v2_models": metadata, "source_url": lb.FRONTEND_URL,
                                      "frontend_sha256": hashlib.sha256(js_path.read_bytes()).hexdigest()}, sort_keys=True))
        fragment, coverage = lb.build(dataset, *paths, config, retrieved_at=retrieved_at)
        coverage["scope"] = "Pinned reviewed v1/v2 release keys and frontend asset; new releases require contract review."
        coverage["discovered_frontend_assets"] = discovered_assets
        coverage["release_discovery_required"] = bool(changed_assets) or not discovered_assets
        return fragment, coverage
    raise ValueError(f"Unknown source adapter: {source}")
