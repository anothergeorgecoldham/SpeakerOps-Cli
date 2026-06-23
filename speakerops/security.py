from __future__ import annotations

import getpass
import hashlib
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from speakerops.audit import AuditLogger
from speakerops.files import read_text_if_exists, read_yaml, utc_timestamp, write_yaml


class SecurityPolicyViolation(Exception):
    """Raised when a configured security policy denies an action."""


@dataclass(frozen=True)
class SecurityPolicy:
    hardened: bool
    allowed_operators: tuple[str, ...]
    scan_generated_content: bool
    provenance_enabled: bool

    @classmethod
    def from_profile(cls, profile: dict[str, Any]) -> "SecurityPolicy":
        config = profile.get("security")
        data = config if isinstance(config, dict) else {}
        allowed_operators = data.get("allowed_operators") or []
        hardened = bool(data.get("hardened", True))
        return cls(
            hardened=hardened,
            allowed_operators=tuple(str(operator) for operator in allowed_operators),
            scan_generated_content=hardened and bool(data.get("scan_generated_content", True)),
            provenance_enabled=hardened and bool(data.get("provenance_enabled", True)),
        )

    def require_operator_allowed(self, audit_logger: AuditLogger) -> str:
        operator = current_operator()
        if not self.hardened:
            audit_logger.log("operator_authorization", operator, "skipped")
            return operator
        if not self.allowed_operators:
            audit_logger.log("operator_authorization", operator, "allowed")
            return operator
        if operator in self.allowed_operators:
            audit_logger.log("operator_authorization", operator, "allowed")
            return operator
        audit_logger.log("operator_authorization", operator, "denied")
        raise SecurityPolicyViolation(f"Operator '{operator}' is not allowed by security policy.")


@dataclass(frozen=True)
class SecretFinding:
    kind: str
    line_number: int


SECRET_PATTERNS = {
    "openai_api_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "generic_assignment": re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"),
}


def current_operator() -> str:
    return os.getenv("SPEAKEROPS_OPERATOR") or getpass.getuser()


def scan_for_secrets(content: str) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        for kind, pattern in SECRET_PATTERNS.items():
            if pattern.search(line):
                findings.append(SecretFinding(kind=kind, line_number=line_number))
        for candidate in re.findall(r"\b[A-Za-z0-9_./+=-]{32,}\b", line):
            if _shannon_entropy(candidate) >= 4.5:
                findings.append(SecretFinding(kind="high_entropy_value", line_number=line_number))
                break
    return findings


def enforce_generated_content_policy(target: str, content: str, policy: SecurityPolicy, audit_logger: AuditLogger) -> None:
    if not policy.scan_generated_content:
        audit_logger.log("secret_scan", target, "skipped")
        return
    findings = scan_for_secrets(content)
    if not findings:
        audit_logger.log("secret_scan", target, "passed")
        return
    summary = ", ".join(f"{finding.kind} on line {finding.line_number}" for finding in findings)
    audit_logger.log("secret_scan", target, f"denied: {summary}")
    raise SecurityPolicyViolation(f"Generated content for {target} may contain secrets: {summary}")


def write_provenance_record(
    talk_dir: Path,
    target: str,
    action: str,
    content: str,
    inputs: dict[str, str],
    policy: SecurityPolicy,
    audit_logger: AuditLogger,
) -> None:
    if not policy.provenance_enabled:
        audit_logger.log("provenance", target, "skipped")
        return

    path = talk_dir / "provenance.yaml"
    current = read_yaml(path) if path.exists() else {}
    records = current.get("records")
    if not isinstance(records, list):
        records = []

    records.append(
        {
            "timestamp": utc_timestamp(),
            "operator": current_operator(),
            "action": action,
            "target": target,
            "content_sha256": sha256_text(content),
            "inputs": {name: sha256_text(value) for name, value in inputs.items()},
        }
    )
    write_yaml(path, {"records": records})
    audit_logger.log("provenance", target, "recorded")


def provenance_inputs(talk_dir: Path) -> dict[str, str]:
    inputs: dict[str, str] = {}
    for name in ["talk.yaml", "idea.md", "research.md", "cfp.md", "outline.md", "review.md"]:
        inputs[name] = read_text_if_exists(talk_dir / name)
    return inputs


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    entropy = 0.0
    for character in set(value):
        probability = value.count(character) / len(value)
        entropy -= probability * math.log2(probability)
    return entropy
