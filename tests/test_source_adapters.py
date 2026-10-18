"""Acquisition boundaries and conservative source contract handling."""
import hashlib
import json

import pytest

from pipeline import source_adapters as adapters


class Archive:
    def __init__(self, root, fixtures):
        self.work = root
        self.fixtures = fixtures
        self.urls = []

    def fetch(self, url):
        self.urls.append(url)
        raw = self.fixtures[url]
        path = self.work / hashlib.sha256(raw).hexdigest()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return path


def test_html_table_extracts_identity_and_entities():
    parser = adapters.Tables()
    parser.feed('<table><tr><th>Model</th><th>Score</th></tr><tr><td><a href="/models/a">A &amp; B</a></td><td><span>1.2</span>%</td></tr></table>')
    assert parser.tables[0][1] == {"cells": ["A & B", "1.2%"], "hrefs": ["/models/a"], "header": False}


def test_arena_uses_resolved_immutable_revision(tmp_path, monkeypatch):
    from pipeline import arena_import as arena
    revision = "a" * 40
    raw = b"parquet fixture"
    path = "text/latest-2026.parquet"
    api = f"https://huggingface.co/api/datasets/{arena.DATASET}"
    archive = Archive(tmp_path, {
        api: json.dumps({"sha": revision}).encode(),
        f"{api}/tree/{revision}?recursive=true&expand=false": json.dumps([
            {"type": "file", "path": path, "lfs": {"oid": hashlib.sha256(raw).hexdigest()}}
        ]).encode(),
        f"{arena.REPO_URL}/resolve/{revision}/{path}": raw,
    })
    def build(dataset, files, manifest, *, revision, retrieved_at):
        assert revision == "a" * 40
        assert retrieved_at == "capture-time"
        assert files["text"].read_bytes() == raw
        return {"sources": []}, {"revision": revision}
    monkeypatch.setattr(arena, "build", build)
    _, coverage = adapters.collect_and_parse("arena", archive, "capture-time", {})
    assert coverage["revision"] == revision
    assert len(archive.urls) == 3


def test_arena_rejects_hash_mismatch(tmp_path):
    from pipeline import arena_import as arena
    revision = "a" * 40
    api = f"https://huggingface.co/api/datasets/{arena.DATASET}"
    archive = Archive(tmp_path, {
        api: json.dumps({"sha": revision}).encode(),
        f"{api}/tree/{revision}?recursive=true&expand=false": json.dumps([
            {"type": "file", "path": "text/latest-a.parquet", "lfs": {"oid": "b" * 64}}
        ]).encode(),
        f"{arena.REPO_URL}/resolve/{revision}/text/latest-a.parquet": b"bad",
    })
    with pytest.raises(ValueError, match="checksum mismatch"):
        adapters.collect_and_parse("arena", archive, "now", {})


def test_vals_rejects_changed_headers(tmp_path):
    baseline = json.loads((adapters.ROOT / "data/expansion/vals-all-source-snapshot-2026-10-18.json").read_text())
    archive = Archive(tmp_path, {baseline["pages"][0]["url"]: b"<table><tr><th>Different metric</th></tr></table>"})
    with pytest.raises(ValueError, match="contract drift"):
        adapters.collect_and_parse("vals", archive, "now", {})


def test_unknown_source_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="Unknown source"):
        adapters.collect_and_parse("unknown", Archive(tmp_path, {}), "now", {})


def test_livebench_changed_existing_score_is_not_discarded():
    from pipeline import livebench_import as lb
    dataset = json.loads((adapters.ROOT / "data/curated/dataset.json").read_text())
    capture = adapters.ROOT / "data/expansion/source-snapshots/livebench"
    paths = [capture / name for name in (
        "table_v1_2026_06_25.csv", "table_2026_09_02.csv", "categories_v1_2026_06_25.json",
        "categories_v2_2026_09_02.json", "breakdown_v2_2026_09_02.json", "frontend_config.json")]
    target = next(o for o in dataset["observations"] if o["benchmark_id"].startswith("livebench_") and o.get("reported_at"))
    actual = target["value"]
    target["value"] = -999
    fragment, _ = lb.build(dataset, *paths)
    correction = next(o for o in fragment["observations"] if target["id"] in o.get("supersedes", []))
    assert correction["value"] == actual
    assert correction["setup"]["correction_previous_value"] == -999


def test_vals_unlinked_row_is_accounted_not_fatal(tmp_path, monkeypatch):
    from pipeline import vals_import
    baseline = json.loads((adapters.ROOT / "data/expansion/vals-all-source-snapshot-2026-10-18.json").read_text())
    baseline["pages"] = [baseline["pages"][0]]
    page = baseline["pages"][0]
    baseline["rows"] = []
    snapshot_path = tmp_path / "data/expansion/vals-all-source-snapshot-2026-10-18.json"
    snapshot_path.parent.mkdir(parents=True)
    snapshot_path.write_text(json.dumps(baseline))
    monkeypatch.setattr(adapters, "ROOT", tmp_path)
    monkeypatch.setattr(vals_import, "build_expansion", lambda snapshot, curated: {"sources": [], "observations": []})
    html = '<table><tr>' + ''.join(f'<th>{x}</th>' for x in page["table_headers"]) + '</tr>'
    html += '<tr><td>1</td><td>Unverified model</td><td>99%</td><td>N/A</td><td>N/A</td></tr></table>'
    _, coverage = adapters.collect_and_parse("vals", Archive(tmp_path, {page["url"]: html.encode()}), "now", {})
    assert coverage["decisions"][0]["status"] == "unresolved_identity"
    assert coverage["counts"]["rows_seen"] == 1


def test_aa_html_flight_chunks_are_decoded_not_executed(tmp_path):
    from pipeline import aa_import as aa
    row = {"id": "fixture", "slug": "mistral-large-4", "gpqa": 0.5}
    payload = '0:{"currentModel":' + json.dumps(row) + ',"models":[' + json.dumps(row) + ']}'
    html = '<html><script>self.__next_f.push(' + json.dumps([1, payload]) + ')</script></html>'
    fragment, coverage = adapters.collect_and_parse("aa", Archive(tmp_path, {
        "https://artificialanalysis.ai/models/mistral-large-4": html.encode(),
    }), "now", aa._CANONICAL)
    assert coverage["counts"]["source_models"] == 1
    assert fragment["observations"]
