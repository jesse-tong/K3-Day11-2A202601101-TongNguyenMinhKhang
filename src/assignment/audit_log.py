"""
Assignment 11 — Audit Log starter (TODO).

Records every interaction for forensics. Never blocks by itself —
other layers catch attacks; this layer makes them reviewable.
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


class AuditLogPlugin:
    """Framework-agnostic audit logger (wire into ADK callbacks or your pipeline)."""

    def __init__(self):
        self.name = "audit_log"
        self.logs: list[dict] = []
        self._open: dict[str, dict] = {}

    def record_input(self, *, user_id: str, text: str, request_id: str | None = None) -> str:
        """Store input + start timestamp keyed by request_id/user_id."""
        if not request_id:
            request_id = f"req-{uuid.uuid4().hex[:8]}"
        now = time.time()
        iso_time = datetime.now(timezone.utc).isoformat()
        self._open[request_id] = {
            "request_id": request_id,
            "user_id": user_id,
            "input_text": text,
            "start_time": now,
            "timestamp": iso_time,
        }
        return request_id

    def record_output(
        self,
        *,
        user_id: str,
        text: str,
        blocked: bool = False,
        layer: str | None = None,
        request_id: str | None = None,
        reviewer_decision: str | None = None,
        action_decision: str | None = None,
    ) -> dict:
        """Store output, layer decision, latency; append to self.logs."""
        req_info = self._open.pop(request_id, None) if request_id else None
        now = time.time()
        start_time = req_info["start_time"] if req_info else now
        duration_ms = round((now - start_time) * 1000, 2)
        timestamp = req_info["timestamp"] if req_info else datetime.now(timezone.utc).isoformat()
        input_text = req_info["input_text"] if req_info else ""

        log_entry = {
            "request_id": request_id or f"req-{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "input_text": input_text,
            "output_text": text,
            "blocked": blocked,
            "layer": layer or ("blocked_layer" if blocked else "passthrough"),
            "timestamp": timestamp,
            "duration_ms": duration_ms,
            "reviewer_decision": reviewer_decision or ("block" if blocked else "allow"),
            "action_decision": action_decision or ("blocked" if blocked else "approved"),
        }
        self.logs.append(log_entry)
        return log_entry

    def export_json(self, filepath: str = "outputs/audit_log.json"):
        """Write logs to disk (JSON array)."""
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)

    def get_log_by_request_id(self, request_id: str) -> dict | None:
        """Find log entry by request_id for incident investigation."""
        for log in self.logs:
            if log.get("request_id") == request_id:
                return log
        return None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

