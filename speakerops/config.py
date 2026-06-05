from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from speakerops.files import read_template, read_yaml, write_text


CONFIG_DIR = ".speakerops"
CONFIG_FILE = "speakerops.yaml"


@dataclass(frozen=True)
class ModelSettings:
    provider: str
    model: str


def profile_path(base_path: Path | None = None) -> Path:
    return (base_path or Path.cwd()) / CONFIG_DIR / CONFIG_FILE


def init_profile(base_path: Path | None = None) -> Path:
    root = base_path or Path.cwd()
    target = profile_path(root)
    write_text(target, read_template("profile.yaml"))
    (root / "talks").mkdir(parents=True, exist_ok=True)
    return target


def load_profile(base_path: Path | None = None) -> dict[str, Any]:
    path = profile_path(base_path)
    if not path.exists():
        raise FileNotFoundError(f"SpeakerOps profile not found at {path}. Run 'speakerops init' first.")
    return read_yaml(path)


def model_settings(profile: dict[str, Any]) -> ModelSettings:
    provider = os.getenv("SPEAKEROPS_MODEL_PROVIDER") or str(profile.get("model_provider") or "local")
    model = os.getenv("SPEAKEROPS_MODEL") or str(profile.get("model") or "local-draft")
    return ModelSettings(provider=provider, model=model)
