"""Load YAML configs from the repo's config/ directory."""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"
# Participant data must not live in a cloud-synced folder (OneDrive, Dropbox, iCloud):
# set VSAFE_DATA_DIR to a local path outside any synced tree. Defaults to ./data.
DATA_DIR = Path(os.environ.get("VSAFE_DATA_DIR") or REPO_ROOT / "data").resolve()
# Which working database under <DATA_DIR>/interim: "vsafe" (release 1, phase 1) by default;
# "vsafe_full" for the all-release corpus after registration. Aggregates of a non-default
# database go to <DATA_DIR>/aggregates/<DB_NAME>/ so phase-1 tables are not overwritten.
DB_NAME = os.environ.get("VSAFE_DB", "vsafe")
if not re.fullmatch(r"[a-z0-9_]{1,40}", DB_NAME):
    raise ValueError(f"VSAFE_DB must be a short lower-case name, got {DB_NAME!r}")


def source_dir(spec: dict) -> Path:
    """Directory of a source in config/sources.yaml, resolved against DATA_DIR."""
    return DATA_DIR / spec["dir"]


def synced_roots() -> list[Path]:
    """Cloud-sync roots known from the environment (OneDrive sets these on Windows)."""
    names = ["OneDrive", "OneDriveConsumer", "OneDriveCommercial"]
    return [Path(os.environ[n]).resolve() for n in names if os.environ.get(n)]


def assert_local_data_dir(data_dir: Path | None = None) -> None:
    """Refuse to put participant data under a cloud-synced folder (data-use rule 2)."""
    d = (data_dir or DATA_DIR).resolve()
    for root in synced_roots():
        if d == root or root in d.parents:
            raise RuntimeError(
                f"Data directory {d} is inside a cloud-synced folder ({root}). "
                "Set VSAFE_DATA_DIR to a local path outside it."
            )


@lru_cache
def load(name: str) -> dict:
    with open(CONFIG_DIR / f"{name}.yaml") as fh:
        return yaml.safe_load(fh)


def columns(
    table: str, *, require: bool = True, keys: list[str] | None = None, release: str | None = None
) -> dict[str, str]:
    """Canonical -> source column mapping; fails on unconfirmed (TODO) columns.

    `keys` limits the TODO check to the columns a step uses. `release` applies an override
    from `<table>_by_release: {<release label>: {...}}` when names differ between files.
    """
    spec = load("columns")
    mapping = dict(spec[table])
    if release is not None:
        mapping.update((spec.get(f"{table}_by_release") or {}).get(release) or {})
    if require:
        todo = [k for k, v in mapping.items() if v in (None, "TODO") and (keys is None or k in keys)]
        if todo:
            raise ValueError(
                f"Unconfirmed columns for '{table}': {todo}. "
                "Set them in config/columns.yaml after inspecting the files (vsafe-ft inspect)."
            )
    return mapping


def analysis() -> dict:
    return load("analysis")
