"""Fetch files listed in config/sources.yaml and record sha256 in <data dir>/raw/MANIFEST.tsv.

Downloads resume: a partial `<name>.part` is continued with an HTTP Range request, so a
slow or interrupted link does not restart multi-GB files. Each file appears once in the
manifest (re-runs replace its row).
"""

from __future__ import annotations

import hashlib
import shutil
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from . import config

HEADER = ["part", "file", "url", "sha256", "bytes", "downloaded_utc"]
USER_AGENT = "vsafe-ft/0.1 (research download)"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _expected_total(r, have: int) -> int | None:
    """Full file size from Content-Range ('bytes a-b/total') or Content-Length."""
    cr = r.headers.get("Content-Range")
    if cr and "/" in cr and cr.rsplit("/", 1)[1].isdigit():
        return int(cr.rsplit("/", 1)[1])
    cl = r.headers.get("Content-Length")
    return have + int(cl) if cl and cl.isdigit() else None


def fetch(url: str, dest: Path, retries: int = 20) -> None:
    """Download url -> dest, resuming from dest.part; retries with backoff on errors.

    `retries` counts consecutive failures that made no progress, so a long download on a
    flaky link keeps going as long as bytes keep arriving. The file is renamed into place
    only when its size equals the size the server declared.
    """
    tmp = dest.with_name(dest.name + ".part")
    failures = 0
    while failures < retries:
        have = tmp.stat().st_size if tmp.exists() else 0
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        if have:
            req.add_header("Range", f"bytes={have}-")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                if have and r.status != 206:       # server ignored Range: start over
                    have = 0
                total = _expected_total(r, have)
                with open(tmp, "ab" if have else "wb") as out:
                    shutil.copyfileobj(r, out, 1 << 20)
            size = tmp.stat().st_size
            if total is not None and size != total:
                raise ConnectionError(f"stream ended at {size} of {total} bytes")
            tmp.replace(dest)
            return
        except urllib.error.HTTPError as e:
            if e.code == 416 and have:             # already complete
                tmp.replace(dest)
                return
            err = e
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            err = e
        now = tmp.stat().st_size if tmp.exists() else 0
        failures = 0 if now > have else failures + 1
        wait = min(300, 5 * 2 ** failures)
        print(f"[retry] {dest.name}: {err!r}; {now} bytes so far; waiting {wait}s", flush=True)
        time.sleep(wait)
    raise RuntimeError(f"giving up on {url} after {retries} failures without progress")


def read_manifest(path: Path) -> dict[tuple[str, str], list[str]]:
    rows = {}
    if path.exists():
        for line in path.read_text().splitlines()[1:]:
            f = line.split("\t")
            if len(f) == len(HEADER):
                rows[(f[0], f[1])] = f
    return rows


def write_manifest(path: Path, rows: dict) -> None:
    lines = ["\t".join(HEADER)] + ["\t".join(r) for _, r in sorted(rows.items())]
    path.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def download(only: list[str] | None = None, files: list[str] | None = None) -> None:
    sources = config.load("sources")
    manifest = config.DATA_DIR / "raw" / "MANIFEST.tsv"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    rows = read_manifest(manifest)
    for part, spec in sources.items():
        if only and part not in only:
            continue
        dest_dir = config.source_dir(spec)
        dest_dir.mkdir(parents=True, exist_ok=True)
        for f in spec.get("files") or []:
            if files and f.get("name") not in files:
                continue
            if not f.get("url"):
                print(f"[skip] {part}/{f.get('name')}: no URL in config/sources.yaml")
                continue
            dest = dest_dir / f["name"]
            if not dest.exists():
                print(f"[get]  {part}/{f['name']}", flush=True)
                t0 = time.time()
                fetch(f["url"], dest)
                print(f"[done] {part}/{f['name']} {dest.stat().st_size} bytes "
                      f"in {time.time() - t0:.0f}s", flush=True)
            if (part, f["name"]) in rows and rows[(part, f["name"])][4] == str(dest.stat().st_size):
                continue
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            rows[(part, f["name"])] = [part, f["name"], f["url"], sha256(dest),
                                       str(dest.stat().st_size), now]
            write_manifest(manifest, rows)
