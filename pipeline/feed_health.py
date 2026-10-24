"""Compact publication metadata; raw discovery payloads stay in staging."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .collectors import SOURCES


def feed_health(staging: Path) -> list[dict[str, Any]]:
    rows = []
    for source in [*SOURCES, "openrouter-endpoints"]:
        path = staging / f"{source}.json"
        if not path.exists():
            rows.append({"source_id": source, "status": "unknown"})
            continue
        try:
            envelope = json.loads(path.read_text())
            feeds = list(envelope.get("endpoints", {}).values()) if source == "openrouter-endpoints" else envelope["feeds"]
            if not feeds:
                raise ValueError("empty envelope")
            for feed in feeds:
                status = feed.get("status", "unknown")
                # Legacy envelopes can retain ok children after a failed attempt.
                if envelope.get("status") == "stale" and status == "ok":
                    status = "stale"
                rows.append({"source_id": source, "url": feed.get("url"), "status": status,
                             "as_of": feed.get("retrieved_at") or envelope.get("retrieved_at"),
                             "attempted_at": feed.get("attempted_at") or envelope.get("attempted_at") or envelope.get("last_attempt_at"),
                             "record_count": feed.get("record_count"),
                             "error": "Refresh rejected or failed; last accepted data retained." if status == "stale" else "Collection failed." if status == "error" else None})
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            rows.append({"source_id": source, "status": "error", "error": "Invalid staging envelope."})
    return rows
