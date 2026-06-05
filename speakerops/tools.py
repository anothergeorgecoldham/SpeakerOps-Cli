from __future__ import annotations

from collections.abc import Callable
from typing import Any

from speakerops.audit import AuditLogger


class ToolNotAllowed(Exception):
    """Raised when a workflow asks for a tool that is not registered."""


class ToolAllowlist:
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, tool: Callable[..., Any]) -> None:
        self._tools[name] = tool

    def execute(self, name: str, *args: Any, **kwargs: Any) -> Any:
        tool = self._tools.get(name)
        if not tool:
            self.audit_logger.log("tool_call", name, "denied")
            raise ToolNotAllowed(f"Tool '{name}' is not registered.")
        self.audit_logger.log("tool_call", name, "allowed")
        return tool(*args, **kwargs)
