"""Discovery collectors. They stage raw source data and never modify curated data."""
from __future__ import annotations

import base64
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


def validate_payload(url: str, body: Any, previous: Any = None) -> int:
    """Reject errors, identity mismatches, empty and implausibly collapsed feeds.

    A drop below half the last accepted count requires manual review. Never
    silently turn upstream deletion or an outage into new curated evidence.
    """
    if not isinstance(body, dict) or any(key in body for key in ("error", "errors")):
        raise ValueError("invalid feed envelope")
    if url.endswith("/endpoints"):
        model_id = url.split("/models/", 1)[1].removesuffix("/endpoints")
        data = body.get("data")
        if not isinstance(data, dict) or data.get("id") != model_id:
            raise ValueError("endpoint model identity mismatch")
        rows = data.get("endpoints")
        identity = lambda row: row.get("model_id") == model_id and bool(row.get("provider_name"))
    elif "openrouter.ai" in url:
        rows = body.get("data")
        key = "model_permaslug" if "rankings-daily" in url else "id"
        identity = lambda row: isinstance(row.get(key), str) and bool(row[key])
    elif url.endswith("taxonomy.json"):
        rows = body.get("architectures")
        identity = lambda row: bool(row.get("id"))
    elif "peacefulcoexistance.com" in url:
        wrapper = "labs" if url.endswith("labs.json") else "entries" if url.endswith("license-evidence.json") else "models"
        rows = body.get(wrapper)
        key = "project_id" if wrapper == "entries" else "id"
        identity = lambda row: bool(row.get(key))
    else:  # models.dev keyed model/provider catalogs
        rows = list(body.values())
        identity = lambda row: bool(row.get("id"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("empty or invalid feed collection")
    if not all(isinstance(row, dict) and identity(row) for row in rows):
        raise ValueError("feed record identity missing or mismatched")
    if previous is not None:
        try:
            old_count = validate_payload(url, previous)
        except ValueError:
            old_count = 0
        if len(rows) * 2 < old_count:
            raise ValueError(f"suspicious feed collapse: {len(rows)} records, previously {old_count}")
    return len(rows)


def response_payload(response: httpx.Response, url: str, previous: Any = None) -> tuple[Any, int]:
    response.raise_for_status()
    if len(response.content) > 50_000_000:
        raise ValueError("feed exceeds 50 MB limit")
    if "json" not in response.headers.get("content-type", "").lower():
        raise ValueError("feed content type is not JSON")
    body = response.json()
    return body, validate_payload(url, body, previous)


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
    old_feeds = {f.get("url"): f for f in (previous or {}).get("feeds", [])}
    now = datetime.now(timezone.utc).isoformat()
    try:
        for url in SOURCES[source]:
            old = old_feeds.get(url, {})
            try:
                response = client.get(url)
                body, count = response_payload(response, url, old.get("data"))
                result = {"url": url, "status": "ok", "sha256": hashlib.sha256(response.content).hexdigest(),
                          "data": body, "record_count": count, "retrieved_at": now}
            except (httpx.HTTPError, ValueError) as exc:
                # Publish only fixed error categories; response bodies/credentials
                # from exception messages never belong in the public manifest.
                error = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
                result = {**old, "url": url, "status": "stale" if old.get("data") else "error", "refresh_error": error}
                if old.get("data") and not result.get("retrieved_at"):
                    result["retrieved_at"] = (previous or {}).get("retrieved_at")
            result["attempted_at"] = now
            results.append(result)
        status = "ok" if all(r["status"] == "ok" for r in results) else "partial" if any(r["status"] == "ok" for r in results) else "stale" if any(r["status"] == "stale" for r in results) else "error"
        envelope = {"source": source, "attempted_at": now, "status": status, "feeds": results}
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
    if not model_ids:
        raise ValueError("no reviewed endpoint IDs supplied")
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
                body, count = response_payload(response, url, endpoints.get(model_id, {}).get("data"))
                raw = response.content
                endpoints[model_id] = {"status":"ok", "url":str(response.url),
                                       "retrieved_at":datetime.now(timezone.utc).isoformat(),
                                       "sha256":hashlib.sha256(raw).hexdigest(), "data":body, "record_count":count,
                                       "body_base64":base64.b64encode(raw).decode("ascii")}
                results.append({"model_id":model_id, "status":"ok"})
            except (httpx.HTTPError, ValueError) as exc:
                old = endpoints.get(model_id)
                if old and old.get("data"):
                    old.update({"status":"stale", "refresh_error":str(exc) if isinstance(exc, ValueError) else type(exc).__name__})
                else:
                    endpoints[model_id] = {"status":"error", "url":url,
                                           "error":str(exc) if isinstance(exc, ValueError) else type(exc).__name__}
                results.append({"model_id":model_id, "status":endpoints[model_id]["status"]})
            endpoints[model_id]["attempted_at"] = datetime.now(timezone.utc).isoformat()
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
