"""Fetch files listed in config/sources.yaml and record sha256 in data/raw/MANIFEST.tsv."""

from __future__ import annotations

import hashlib
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from . import config


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(only: list[str] | None = None) -> None:
    sources = config.load("sources")
    manifest = config.DATA_DIR / "raw" / "MANIFEST.tsv"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    new = not manifest.exists()
    with open(manifest, "a") as log:
        if new:
            log.write("part\tfile\turl\tsha256\tbytes\tdownloaded_utc\n")
        for part, spec in sources.items():
            if only and part not in only:
                continue
            dest_dir = config.REPO_ROOT / spec["dir"]
            dest_dir.mkdir(parents=True, exist_ok=True)
            for f in spec.get("files") or []:
                if not f.get("url"):
                    print(f"[skip] {part}/{f.get('name')}: no URL in config/sources.yaml")
                    continue
                dest = dest_dir / f["name"]
                if not dest.exists():
                    print(f"[get]  {f['url']}")
                    tmp = dest.with_suffix(dest.suffix + ".part")
                    with urllib.request.urlopen(f["url"]) as r, open(tmp, "wb") as out:
                        shutil.copyfileobj(r, out, 1 << 20)
                    tmp.rename(dest)
                digest = sha256(dest)
                now = datetime.now(timezone.utc).isoformat(timespec="seconds")
                log.write(f"{part}\t{f['name']}\t{f['url']}\t{digest}\t{dest.stat().st_size}\t{now}\n")
