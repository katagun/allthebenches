"""Discovery collectors. They stage raw source data and never modify curated data."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any
import httpx

SOURCES = {
    "peacefulcoexistance": [
        "https://peacefulcoexistance.com/labs.json",
        "https://peacefulcoexistance.com/models.json",
        "https://peacefulcoexistance.com/models-dev.json",
        "https://peacefulcoexistance.com/taxonomy.json",
        "https://peacefulcoexistance.com/license-evidence.json",
    ],
    "models.dev": ["https://models.dev/models.json?type=all", "https://models.dev/api.json?type=all"],
    "openrouter": ["https://openrouter.ai/api/v1/models", "https://openrouter.ai/api/v1/datasets/rankings-daily"],
}


def collect(source: str, staging: Path, client: httpx.Client | None = None) -> dict[str, Any]:
    if source not in SOURCES:
        raise ValueError(f"unknown source {source}; choose {', '.join(SOURCES)}")
    staging.mkdir(parents=True, exist_ok=True)
    owns_client = client is None
    client = client or httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "allthebenches/0.1 (metadata collector)"})
    if source == "openrouter" and os.getenv("OPENROUTER_API_KEY"):
        client.headers["Authorization"] = f"Bearer {os.environ['OPENROUTER_API_KEY']}"
    old_path = staging / f"{source}.json"
    previous = json.loads(old_path.read_text()) if old_path.exists() else None
    results = []
    try:
        for url in SOURCES[source]:
            try:
                response = client.get(url)
                response.raise_for_status()
                body = response.json()
                raw = response.content
                results.append({"url": url, "status": "ok", "sha256": hashlib.sha256(raw).hexdigest(), "data": body})
            except (httpx.HTTPError, ValueError) as exc:
                results.append({"url": url, "status": "error", "error": f"{type(exc).__name__}: {exc}"})
        now = datetime.now(timezone.utc).isoformat()
        if all(r["status"] != "ok" for r in results) and previous:
            envelope = previous
            envelope["last_attempt_at"] = now
            envelope["last_attempt"] = results
            envelope["status"] = "stale"
        else:
            old_feeds = {f.get("url"): f for f in (previous or {}).get("feeds", [])}
            for i, result in enumerate(results):
                old = old_feeds.get(result.get("url"))
                if result["status"] == "error" and old and old.get("status") in ("ok", "stale"):
                    results[i] = {**old, "status": "stale", "refresh_error": result["error"]}
                elif result["status"] == "ok":
                    result["retrieved_at"] = now
            envelope = {"source": source, "retrieved_at": now, "status": "ok" if all(r["status"] == "ok" for r in results) else "partial", "feeds": results}
        old_path.write_text(json.dumps(envelope, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        queue = mapping_queue_rows(source, envelope)
        queue_path = staging / f"{source}-mapping-queue.json"
        queue_path.write_text(json.dumps(queue, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        return envelope
    finally:
        if owns_client: client.close()


def mapping_queue_rows(source: str, envelope: dict[str, Any]) -> list[dict[str, Any]]:
    queue = []
    for feed in envelope.get("feeds", []):
        if feed.get("status") not in ("ok", "stale"):
            continue
        for external_id, record in _records(feed.get("data")):
            if isinstance(record, dict) and str(record.get("model_permaslug", "")).lower() == "other":
                continue
            queue.append({"source": source, "feed_url": feed["url"], "external_id": external_id,
                          "name": record.get("name") if isinstance(record, dict) else None,
                          "status": "unresolved", "feed_status": feed.get("status"),
                          "retrieved_at": feed.get("retrieved_at"), "record": record})
    return queue


def collect_openrouter_endpoints(model_ids: list[str], staging: Path, client: httpx.Client | None = None) -> dict[str, Any]:
    """Fetch endpoint-level routes for explicitly reviewed OpenRouter model IDs."""
    staging.mkdir(parents=True, exist_ok=True)
    owns_client = client is None
    headers = {"User-Agent": "allthebenches/0.1 (metadata collector)"}
    if os.getenv("OPENROUTER_API_KEY"):
        headers["Authorization"] = f"Bearer {os.environ['OPENROUTER_API_KEY']}"
    client = client or httpx.Client(timeout=30, follow_redirects=True, headers=headers)
    path = staging / "openrouter-endpoints.json"
    previous = json.loads(path.read_text()) if path.exists() else {"endpoints": {}}
    endpoints = previous.get("endpoints", {})
    results = []
    try:
        for model_id in sorted(set(model_ids)):
            url = f"https://openrouter.ai/api/v1/models/{model_id}/endpoints"
            try:
                response = client.get(url)
                response.raise_for_status()
                raw = response.content
                endpoints[model_id] = {"status":"ok", "url":str(response.url),
                                       "retrieved_at":datetime.now(timezone.utc).isoformat(),
                                       "sha256":hashlib.sha256(raw).hexdigest(), "data":response.json()}
                results.append({"model_id":model_id, "status":"ok"})
            except (httpx.HTTPError, ValueError) as exc:
                old = endpoints.get(model_id)
                if old and old.get("data"):
                    old.update({"status":"stale", "refresh_error":f"{type(exc).__name__}: {exc}"})
                else:
                    endpoints[model_id] = {"status":"error", "url":url,
                                           "error":f"{type(exc).__name__}: {exc}"}
                results.append({"model_id":model_id, "status":endpoints[model_id]["status"]})
        envelope = {"source":"openrouter-endpoints", "attempted_at":datetime.now(timezone.utc).isoformat(),
                    "status":"ok" if all(r["status"] == "ok" for r in results) else "partial",
                    "endpoints":endpoints, "attempts":results}
        path.write_text(json.dumps(envelope, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        return envelope
    finally:
        if owns_client: client.close()


def _records(data: Any):
    """Yield stable external keys while preserving original source records."""
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                external_id = item.get("source_id") or item.get("id") or item.get("slug") or item.get("model_id") or item.get("model_permaslug")
                if item.get("model_permaslug") and item.get("date"):
                    external_id = f"{item['model_permaslug']}@{item['date']}"
                if external_id is not None:
                    yield str(external_id), item
    elif isinstance(data, dict):
        # Upstreams wrap arrays under different collection names. Recognize
        # the documented envelopes and still support keyed model catalogs.
        for wrapper in ("data", "models", "labs", "entries", "results", "items"):
            nested = data.get(wrapper)
            if isinstance(nested, list):
                yield from _records(nested)
                return
        for key, item in data.items():
            if isinstance(item, dict):
                external_id = item.get("source_id") or item.get("id") or item.get("slug") or item.get("model_id") or key
                yield str(external_id), item
