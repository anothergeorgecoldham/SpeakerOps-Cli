from __future__ import annotations

import re
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from speakerops.audit import AuditLogger
from speakerops.approval import ApprovalGate


MARKDOWN_FILES = ["idea.md", "research.md", "cfp.md", "outline.md", "review.md"]


class PolicyViolation(Exception):
    """Raised when a requested talk file path leaves the selected workspace."""


class WorkspacePolicy:
    def __init__(self, talk_dir: Path, audit_logger: AuditLogger | None = None, approval_gate: ApprovalGate | None = None):
        self.talk_dir = talk_dir.resolve(strict=False)
        self.audit_logger = audit_logger
        self.approval_gate = approval_gate

    def resolve(self, requested_path: str | Path) -> Path:
        path = Path(requested_path)
        candidate = path if path.is_absolute() else self.talk_dir / path
        resolved = candidate.resolve(strict=False)
        try:
            resolved.relative_to(self.talk_dir)
        except ValueError as exc:
            self._log("policy_denied", requested_path, "denied")
            raise PolicyViolation(f"Path '{requested_path}' is outside talk workspace '{self.talk_dir}'.") from exc
        return resolved

    def read_yaml(self, requested_path: str | Path) -> dict[str, Any]:
        try:
            resolved = self.resolve(requested_path)
        except PolicyViolation:
            self._log("file_read", requested_path, "denied")
            raise
        self._log("file_read", requested_path, "allowed")
        return read_yaml(resolved)

    def read_text_if_exists(self, requested_path: str | Path) -> str:
        try:
            resolved = self.resolve(requested_path)
        except PolicyViolation:
            self._log("file_read", requested_path, "denied")
            raise
        self._log("file_read", requested_path, "allowed")
        return read_text_if_exists(resolved)

    def write_text(self, requested_path: str | Path, content: str, require_approval: bool = False) -> bool:
        try:
            resolved = self.resolve(requested_path)
        except PolicyViolation:
            self._log("file_write", requested_path, "denied")
            raise
        if require_approval and resolved.exists() and self.approval_gate and not self.approval_gate.confirm_overwrite(requested_path):
            return False
        action = "file_write" if resolved.exists() else "file_create"
        write_text(resolved, content)
        self._log(action, requested_path, "allowed")
        return True

    def append_text(self, requested_path: str | Path, content: str) -> bool:
        try:
            resolved = self.resolve(requested_path)
        except PolicyViolation:
            self._log("file_write", requested_path, "denied")
            raise
        action = "file_write" if resolved.exists() else "file_create"
        append_text(resolved, content)
        self._log(action, requested_path, "allowed")
        return True

    def _log(self, action: str, target: str | Path, result: str) -> None:
        if self.audit_logger:
            self.audit_logger.log(action, target, result)


def read_template(name: str) -> str:
    return resources.files("speakerops").joinpath("templates", name).read_text(encoding="utf-8")


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping in {path}")
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True)


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(content)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "untitled"


def initial_markdown(title: str) -> dict[str, str]:
    return {
        "idea.md": f"# Idea Notes\n\n## Working Title\n\n{title}\n\n## Notes\n\n",
        "research.md": "# Research Notes\n\n",
        "cfp.md": "# CFP Submission\n\n",
        "outline.md": "# Talk Outline\n\n",
        "review.md": "# Review Summary\n\n",
    }


def load_talk_context(policy: WorkspacePolicy) -> tuple[dict[str, Any], dict[str, str]]:
    talk = policy.read_yaml("talk.yaml")
    markdown = {name: policy.read_text_if_exists(name) for name in MARKDOWN_FILES}
    return talk, markdown
