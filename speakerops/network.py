from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from speakerops.audit import AuditLogger


class NetworkPolicyViolation(Exception):
    """Raised when a requested network domain is not allowed."""


@dataclass(frozen=True)
class NetworkPolicy:
    mode: str
    allowed_domains: tuple[str, ...]
    audit_logger: AuditLogger

    @classmethod
    def from_config(cls, config: dict[str, Any] | None, audit_logger: AuditLogger) -> "NetworkPolicy":
        data = config if isinstance(config, dict) else {}
        domains = data.get("allowed_domains") or []
        return cls(
            mode=str(data.get("mode") or "allowlist"),
            allowed_domains=tuple(str(domain).lower() for domain in domains),
            audit_logger=audit_logger,
        )

    def check_url(self, url: str) -> str:
        domain = urlparse(url).hostname
        if not domain:
            raise NetworkPolicyViolation(f"Network request has no domain: {url}")
        domain = domain.lower()

        if self.mode != "allowlist":
            self.audit_logger.log("network_request", domain, "allowed")
            return domain

        if self._is_allowed(domain):
            self.audit_logger.log("network_request", domain, "allowed")
            return domain

        self.audit_logger.log("network_request", domain, "denied")
        raise NetworkPolicyViolation(f"Network request to '{domain}' is not allowed by policy.")

    def _is_allowed(self, domain: str) -> bool:
        return any(domain == allowed or domain.endswith(f".{allowed}") for allowed in self.allowed_domains)
