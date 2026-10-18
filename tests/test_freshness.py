from datetime import datetime, timezone

from pipeline.freshness import build_report, main


AS_OF = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)


def _raw(price_time="2026-10-17T11:00:00Z", usage_as_of="2026-10-17T10:00:00Z"):
    return {
        "sources": [
            {"id": "market", "url": "https://example.test/market", "title": "Market",
             "publisher": "Example", "published_at": "2020-01-01T00:00:00Z"},
            {"id": "benchmark", "url": "https://example.test/bench", "title": "Paper",
             "publisher": "Lab", "published_at": "2020-01-01T00:00:00Z"},
        ],
        "prices": [{"id": "p1", "route_id": "r1", "source_id": "market", "observed_at": price_time}],
        "usage": [{"id": "u1", "platform": "example", "source_id": "market",
                   "period_end": "2026-10-17", "source_as_of": usage_as_of}],
        "observations": [{"id": "o1", "source_id": "benchmark"}],
    }


def test_recent_mutable_records_pass_and_historical_sources_are_age_only():
    report = build_report(_raw(), AS_OF)
    assert report["stale_count"] == 0
    assert report["missing_provenance_count"] == 0
    historical = report["historical_benchmark_sources"][0]
    assert historical["source_id"] == "benchmark"
    assert historical["age_days"] > 2000
    assert historical["expiry"] is None
    assert report["issues"] == []


def test_stale_price_and_usage_fail_independently():
    raw = _raw("2026-10-15T11:59:00Z", "2026-10-15T11:59:00Z")
    report = build_report(raw, AS_OF)
    assert report["stale_count"] == 2
    assert all(item["stale"] for item in report["mutable_data"]["prices"] + report["mutable_data"]["usage"])


def test_missing_source_metadata_and_timestamp_are_reported():
    raw = _raw()
    raw["sources"][0]["url"] = ""
    raw["prices"][0]["observed_at"] = None
    raw["usage"][0]["source_id"] = "unknown"
    report = build_report(raw, AS_OF)
    assert report["missing_provenance_count"] == 2
    assert {row["record_type"] for row in report["missing_provenance"]} == {"price", "usage"}
    assert all("reason" not in row for row in report["missing_provenance"])


def test_performance_window_and_future_timestamps_are_checked():
    raw = _raw()
    raw["performance"] = [
        {"id": "perf-old", "route_id": "r1", "source_id": "market",
         "observed_at": "2026-10-17T11:29:00Z", "metric": "latency", "percentile": "p50",
         "sample_window_seconds": 1800},
        {"id": "perf-future", "route_id": "r1", "source_id": "market",
         "observed_at": "2026-10-17T12:06:00Z", "metric": "latency", "percentile": "p50",
         "sample_window_seconds": 1800},
    ]
    report = build_report(raw, AS_OF)
    assert report["stale_count"] == 1
    assert report["future_count"] == 1
    assert {item["reason"] for item in report["issues"]} == {
        "missing or older than 30 minutes", "timestamp is more than five minutes in the future"
    }


def test_invalid_explicit_as_of_fails(tmp_path):
    data = tmp_path / "dataset.json"
    data.write_text("{}", encoding="utf-8")
    assert main(["--input", str(data), "--report", str(tmp_path / "report.json"), "--as-of", "not-a-date"]) == 1
    assert not (tmp_path / "report.json").exists()
