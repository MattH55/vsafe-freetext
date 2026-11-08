"""Load YAML configs from the repo's config/ directory."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"
DATA_DIR = REPO_ROOT / "data"


@lru_cache
def load(name: str) -> dict:
    with open(CONFIG_DIR / f"{name}.yaml") as fh:
        return yaml.safe_load(fh)


def columns(table: str, *, require: bool = True) -> dict[str, str]:
    """Canonical -> source column mapping; fails on unconfirmed (TODO) columns."""
    mapping = load("columns")[table]
    if require:
        todo = [k for k, v in mapping.items() if v in (None, "TODO")]
        if todo:
            raise ValueError(
                f"Unconfirmed columns for '{table}': {todo}. "
                "Set them in config/columns.yaml after inspecting the files (vsafe-ft inspect)."
            )
    return mapping


def analysis() -> dict:
    return load("analysis")
