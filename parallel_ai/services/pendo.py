from __future__ import annotations

import json
import logging
import time
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

PENDO_TRACK_URL = "https://data.pendo.io/data/track"
PENDO_INTEGRATION_KEY = "b1e27122-b963-48df-8c31-84594bbed7a6"


def track(event: str, visitor_id: str = "system", account_id: str = "system", properties: dict[str, Any] | None = None) -> None:
    """Send a server-side Track Event to Pendo. Failures are logged but never raise."""
    payload = {
        "type": "track",
        "event": event,
        "visitorId": visitor_id,
        "accountId": account_id,
        "timestamp": int(time.time() * 1000),
    }
    if properties:
        payload["properties"] = properties
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            PENDO_TRACK_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-pendo-integration-key": PENDO_INTEGRATION_KEY,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        logger.debug("Pendo track event '%s' failed", event, exc_info=True)
