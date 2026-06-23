from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from speakerops.files import read_template, read_yaml, write_text, write_yaml


CONFIG_DIR = ".speakerops"
CONFIG_FILE = "speakerops.yaml"


@dataclass(frozen=True)
class ModelSettings:
    provider: str
    model: str


def profile_path(base_path: Path | None = None) -> Path:
    return (base_path or project_root()) / CONFIG_DIR / CONFIG_FILE


def project_root(start_path: Path | None = None) -> Path:
    start = (start_path or Path.cwd()).resolve(strict=False)
    for candidate in (start, *start.parents):
        if candidate.name == CONFIG_DIR and (candidate / CONFIG_FILE).exists():
            return candidate.parent
        if (candidate / CONFIG_DIR / CONFIG_FILE).exists():
            return candidate
    return start


def init_profile(base_path: Path | None = None) -> Path:
    root = base_path or project_root()
    target = profile_path(root)
    write_text(target, read_template("profile.yaml"))
    (root / "talks").mkdir(parents=True, exist_ok=True)
    return target


def load_profile(base_path: Path | None = None) -> dict[str, Any]:
    path = profile_path(base_path)
    if not path.exists():
        raise FileNotFoundError(f"SpeakerOps profile not found at {path}. Run 'speakerops init' first.")
    return read_yaml(path)


def save_profile(profile: dict[str, Any], base_path: Path | None = None) -> None:
    write_yaml(profile_path(base_path), profile)


def current_talk_path(profile: dict[str, Any]) -> Path | None:
    current_talk = profile.get("current_talk")
    if not current_talk:
        return None
    return Path(str(current_talk))


def set_current_talk(talk_path: Path, base_path: Path | None = None) -> Path:
    root = base_path or project_root()
    profile = load_profile(root)
    candidate = talk_path if talk_path.is_absolute() else root / talk_path
    try:
        stored_path = candidate.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        stored_path = candidate.resolve(strict=False)
    profile["current_talk"] = stored_path.as_posix()
    save_profile(profile, root)
    return stored_path


def model_settings(profile: dict[str, Any]) -> ModelSettings:
    provider = os.getenv("SPEAKEROPS_MODEL_PROVIDER") or str(profile.get("model_provider") or "local")
    model = os.getenv("SPEAKEROPS_MODEL") or str(profile.get("model") or "local-draft")
    return ModelSettings(provider=provider, model=model)
