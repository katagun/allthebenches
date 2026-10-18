"""Read-only freshness and provenance report for curated data."""
from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta, timezone
import json
from pathlib import Path
import sys
from typing import Any

PRICE_MAX_AGE = timedelta(hours=48)
USAGE_MAX_AGE = timedelta(hours=48)
PERFORMANCE_MAX_AGE = timedelta(minutes=30)
FUTURE_TOLERANCE = timedelta(minutes=5)
DEFAULT_DATASET = Path("data/curated/dataset.json")
DEFAULT_REPORT = Path("freshness-report.json")


def _as_datetime(value: str | datetime | date | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, date):
        result = datetime.combine(value, time.min)
    else:
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def build_report(raw: dict[str, Any], as_of: datetime) -> dict[str, Any]:
    """Analyze a dataset-shaped object; ``as_of`` makes checks deterministic."""
    now = _as_datetime(as_of)
    assert now is not None
    sources = {item.get("id"): item for item in raw.get("sources", []) if item.get("id")}
    missing_provenance: list[dict[str, str]] = []
    issues: list[dict[str, str]] = []
    price_rows = raw.get("prices", [])
    usage_rows = raw.get("usage", [])

    def provenance(kind: str, row: dict[str, Any], required_time: str) -> None:
        row_id = str(row.get("id", "<missing id>"))
        source_id = row.get("source_id")
        source = sources.get(source_id)
        missing = []
        if not source_id:
            missing.append("source_id")
        elif source is None:
            missing.append(f"source record {source_id!r}")
        else:
            for field in ("url", "title", "publisher"):
                if not source.get(field):
                    missing.append(f"source.{field}")
        if not row.get(required_time):
            missing.append(required_time)
        if missing:
            missing_provenance.append({"record_type": kind, "record_id": row_id,
                                       "missing": ", ".join(missing)})

    stale_count = 0
    future_count = 0

    def current_record(kind: str, row: dict[str, Any], timestamp: datetime | None,
                       max_age: timedelta) -> dict[str, Any]:
        nonlocal stale_count, future_count
        age = now - timestamp if timestamp else None
        future = age is not None and age < -FUTURE_TOLERANCE
        stale = age is None or age > max_age
        stale_count += stale
        future_count += future
        if stale:
            issues.append({"record_type": kind, "record_id": str(row.get("id", "<missing id>")),
                           "reason": f"missing or older than {int(max_age.total_seconds() / 60)} minutes"
                           if max_age < timedelta(hours=1) else "missing or older than 48 hours"})
        if future:
            issues.append({"record_type": kind, "record_id": str(row.get("id", "<missing id>")),
                           "reason": "timestamp is more than five minutes in the future"})
        return {"id": row.get("id"), "age_minutes": round(age.total_seconds() / 60, 2) if age is not None else None,
                "stale": stale, "future": future}

    prices = []
    for row in price_rows:
        provenance("price", row, "observed_at")
        item = current_record("price", row, _as_datetime(row.get("observed_at")), PRICE_MAX_AGE)
        item["route_id"] = row.get("route_id")
        prices.append(item)

    usage = []
    for row in usage_rows:
        provenance("usage", row, "period_end")
        observed = _as_datetime(row.get("source_as_of")) or _as_datetime(row.get("period_end"))
        item = current_record("usage", row, observed, USAGE_MAX_AGE)
        item["platform"] = row.get("platform")
        usage.append(item)

    performance = []
    for row in raw.get("performance", []):
        provenance("performance", row, "observed_at")
        item = current_record("performance", row, _as_datetime(row.get("observed_at")), PERFORMANCE_MAX_AGE)
        item.update({"route_id": row.get("route_id"), "metric": row.get("metric"),
                     "percentile": row.get("percentile"), "sample_window_seconds": row.get("sample_window_seconds")})
        performance.append(item)

    observation_sources = {row.get("source_id") for row in raw.get("observations", []) if row.get("source_id")}
    history = []
    for source_id in sorted(observation_sources):
        source = sources.get(source_id, {})
        source_date = _as_datetime(source.get("published_at")) or _as_datetime(source.get("retrieved_at"))
        history.append({"source_id": source_id,
                        "age_days": round((now - source_date).total_seconds() / 86400, 2) if source_date else None,
                        "as_of": source_date.isoformat().replace("+00:00", "Z") if source_date else None,
                        "expiry": None})
    return {
        "as_of": now.isoformat().replace("+00:00", "Z"),
        "policy": {"price_max_age_hours": 48, "usage_max_age_hours": 48,
                   "performance_max_age_minutes": 30, "future_tolerance_minutes": 5},
        "mutable_data": {"prices": prices, "usage": usage, "performance": performance},
        "issues": issues,
        "missing_provenance": missing_provenance,
        "historical_benchmark_sources": history,
        "stale_count": stale_count,
        "future_count": future_count,
        "missing_provenance_count": len(missing_provenance),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--as-of", help="UTC instant for deterministic checks (ISO 8601)")
    args = parser.parse_args(argv)
    try:
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        if args.as_of:
            moment = _as_datetime(args.as_of)
            if moment is None:
                raise ValueError(f"invalid --as-of ISO 8601 datetime: {args.as_of}")
        else:
            moment = datetime.now(timezone.utc)
        report = build_report(raw, moment)
    except Exception as exc:
        print(f"Freshness check failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Freshness report: {args.report}; stale mutable records={report['stale_count']}; future timestamps={report['future_count']}; missing provenance={report['missing_provenance_count']}")
    return 1 if report["stale_count"] or report["future_count"] or report["missing_provenance_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
