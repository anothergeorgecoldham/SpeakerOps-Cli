from __future__ import annotations

import re
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any

import yaml


MARKDOWN_FILES = ["idea.md", "research.md", "cfp.md", "outline.md", "review.md"]


class PolicyViolation(Exception):
    """Raised when a requested talk file path leaves the selected workspace."""


class WorkspacePolicy:
    def __init__(self, talk_dir: Path):
        self.talk_dir = talk_dir.resolve(strict=False)

    def resolve(self, requested_path: str | Path) -> Path:
        path = Path(requested_path)
        candidate = path if path.is_absolute() else self.talk_dir / path
        resolved = candidate.resolve(strict=False)
        try:
            resolved.relative_to(self.talk_dir)
        except ValueError as exc:
            raise PolicyViolation(f"Path '{requested_path}' is outside talk workspace '{self.talk_dir}'.") from exc
        return resolved

    def read_yaml(self, requested_path: str | Path) -> dict[str, Any]:
        return read_yaml(self.resolve(requested_path))

    def read_text_if_exists(self, requested_path: str | Path) -> str:
        return read_text_if_exists(self.resolve(requested_path))

    def write_text(self, requested_path: str | Path, content: str) -> None:
        write_text(self.resolve(requested_path), content)

    def append_text(self, requested_path: str | Path, content: str) -> None:
        append_text(self.resolve(requested_path), content)


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
