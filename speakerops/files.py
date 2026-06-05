from __future__ import annotations

import re
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any

import yaml


MARKDOWN_FILES = ["idea.md", "research.md", "cfp.md", "outline.md", "review.md"]


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


def load_talk_context(talk_path: Path) -> tuple[dict[str, Any], dict[str, str]]:
    talk = read_yaml(talk_path / "talk.yaml")
    markdown = {name: read_text_if_exists(talk_path / name) for name in MARKDOWN_FILES}
    return talk, markdown
