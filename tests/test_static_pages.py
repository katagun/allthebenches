from xml.etree import ElementTree

from pipeline.schema import Dataset
from pipeline.static_pages import build_static_pages


def fixture():
    return Dataset.model_validate({
        "sources": [
            {"id": "safe", "url": "https://example.test/report?a=1&b=2", "title": "Report <script>", "publisher": "Lab"},
            {"id": "unsafe", "url": "javascript:alert(1)", "title": "Unsafe", "publisher": "Lab"},
        ],
        "labs": [{"id": "lab", "name": "Lab"}],
        "models": [
            {"id": "m<1", "lab_ids": ["lab"], "family_id": "f", "name": "Model <One>"},
            {"id": "empty", "lab_ids": [], "family_id": "f2", "name": "Empty model"},
        ],
        "configurations": [{"id": "c", "model_id": "m<1", "reasoning_label": "high & careful", "mode": "enabled"}],
        "benchmarks": [{"id": "b/1", "family_id": "bf", "name": "Bench <One>", "version": "2", "subset": "full & verified", "category": "coding", "modality": "text", "metric_name": "accuracy", "unit": "%", "direction": "higher", "documentation_url": "javascript:alert(1)"},
                        {"id": "missing", "family_id": "bf2", "name": "No results", "version": "?", "category": "other", "modality": "text", "metric_name": "score", "unit": "points", "direction": "lower"}],
        "observations": [
            {"id": "o", "configuration_id": "c", "benchmark_id": "b/1", "value": 0, "unit": "%", "source_id": "safe", "locator": "Table 1", "evaluator": "Lab", "reporting_relationship": "self_report", "review_state": "reviewed"},
            {"id": "candidate", "configuration_id": "c", "benchmark_id": "b/1", "value": 90, "unit": "%", "source_id": "safe", "locator": "Table 2", "evaluator": "Lab", "reporting_relationship": "self_report", "review_state": "candidate"},
        ],
    })


def test_pages_are_static_escaped_and_include_reviewed_evidence(tmp_path):
    build_static_pages(fixture(), tmp_path)
    model = (tmp_path / "models" / "m%3C1" / "index.html").read_text()
    benchmark = (tmp_path / "benchmarks" / "b%2F1" / "index.html").read_text()
    empty = (tmp_path / "models" / "empty" / "index.html").read_text()
    assert "<script>" not in model and "Model &lt;One&gt;" in model
    assert "<script>" not in benchmark and "Bench &lt;One&gt;" in benchmark
    assert "0 %" in model and "0 %" in benchmark
    assert "candidate" not in model and "90 %" not in model
    assert "high &amp; careful" in model and "full &amp; verified" in benchmark
    assert 'href="javascript:' not in benchmark and 'href="javascript:' not in model
    assert "https://example.test/report?a=1&amp;b=2" in model
    assert "Missing scores mean no reviewed result" in empty
    assert "No reviewed scores are published" in empty
    assert "https://allthebenches.com/#/models/m%3C1" in model
    assert "https://allthebenches.com/#/" in model


def test_indexes_sitemap_and_robots_cover_canonical_pages(tmp_path):
    build_static_pages(fixture(), tmp_path)
    sitemap = ElementTree.parse(tmp_path / "sitemap.xml")
    urls = {element.text for element in sitemap.iter() if element.tag.endswith("loc")}
    assert "https://allthebenches.com/models/m%3C1/" in urls
    assert "https://allthebenches.com/benchmarks/b%2F1/" in urls
    assert "https://allthebenches.com/models/" in urls
    assert "https://allthebenches.com/benchmarks/" in urls
    assert "javascript:" not in (tmp_path / "sitemap.xml").read_text()
    assert "Sitemap: https://allthebenches.com/sitemap.xml" in (tmp_path / "robots.txt").read_text()
    assert "Empty model" in (tmp_path / "models" / "index.html").read_text()
    assert "No results" in (tmp_path / "benchmarks" / "index.html").read_text()


def test_conflicting_reports_are_not_silently_dropped(tmp_path):
    data = fixture()
    original = data.observations[0]
    data.observations.append(original.model_copy(update={"id": "second", "value": 12, "locator": "Table 3"}))
    build_static_pages(data, tmp_path)
    html = (tmp_path / "models" / "m%3C1" / "index.html").read_text()
    benchmark_html = (tmp_path / "benchmarks" / "b%2F1" / "index.html").read_text()
    assert "0 %" in html and "12 %" in html
    assert "Table 3" in html
    assert "Disputed reports" in html
    assert "Evidence status" in benchmark_html and "Disputed reports" in benchmark_html


def test_pruning_removes_only_stale_generated_pages(tmp_path):
    data = fixture()
    build_static_pages(data, tmp_path)
    stale_model = tmp_path / "models" / "m%3C1"
    (stale_model / "keep.txt").write_text("unrelated asset", encoding="utf-8")
    manual_page = tmp_path / "models" / "manual"
    manual_page.mkdir()
    (manual_page / "index.html").write_text("user owned page", encoding="utf-8")

    reduced = data.model_copy(update={
        "models": [model for model in data.models if model.id == "empty"],
        "configurations": [],
        "observations": [],
        "benchmarks": [benchmark for benchmark in data.benchmarks if benchmark.id == "missing"],
    })
    build_static_pages(reduced, tmp_path)

    assert not (stale_model / "index.html").exists()
    assert (stale_model / "keep.txt").read_text(encoding="utf-8") == "unrelated asset"
    assert (manual_page / "index.html").read_text(encoding="utf-8") == "user owned page"
    assert not (tmp_path / "benchmarks" / "b%2F1" / "index.html").exists()
    sitemap = ElementTree.parse(tmp_path / "sitemap.xml")
    urls = {element.text for element in sitemap.iter() if element.tag.endswith("loc")}
    assert "https://allthebenches.com/models/m%3C1/" not in urls
    assert "https://allthebenches.com/benchmarks/b%2F1/" not in urls
