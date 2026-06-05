from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


class AuditLogger:
    def __init__(self, log_path: Path | None = None):
        self.log_path = log_path or Path(".speakerops") / "audit.log"

    def log(self, action: str, target: str | Path, result: str) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{timestamp} | {action} | {target} | {result}\n")
