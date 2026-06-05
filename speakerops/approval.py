from __future__ import annotations

from pathlib import Path
from typing import Callable

from speakerops.audit import AuditLogger


class ApprovalGate:
    def __init__(self, audit_logger: AuditLogger, prompt_input: Callable[[str], str] = input):
        self.audit_logger = audit_logger
        self.prompt_input = prompt_input

    def confirm_overwrite(self, target: str | Path) -> bool:
        self.audit_logger.log("approval_required", target, "pending")
        answer = self.prompt_input(f"{target} already exists. Overwrite? [y/N] ").strip().lower()
        approved = answer in {"y", "yes"}
        self.audit_logger.log("approval_decision", target, "approved" if approved else "denied")
        return approved
