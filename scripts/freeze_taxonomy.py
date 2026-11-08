"""Freeze taxonomy/v0 as taxonomy/<version> (default v1.0) with a SHA256SUMS file.

Refuses to overwrite an existing version: amendments after registration get a new
version number and an OSF amendment, never an edit in place.

    python scripts/freeze_taxonomy.py            # -> taxonomy/v1.0
    python scripts/freeze_taxonomy.py --version v1.1
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(src: Path, dst: Path) -> str:
    """Copy src -> dst, write dst/SHA256SUMS, return the digest of SHA256SUMS itself."""
    if dst.exists():
        raise FileExistsError(f"{dst} already exists; frozen versions are never overwritten")
    if not src.is_dir():
        raise FileNotFoundError(src)
    tmp = dst.with_name(dst.name + ".tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(src, tmp)
    files = sorted(p for p in tmp.rglob("*") if p.is_file())
    lines = "".join(f"{sha256(p)}  {p.relative_to(tmp).as_posix()}\n" for p in files)
    (tmp / "SHA256SUMS").write_bytes(lines.encode("utf-8"))   # LF on every OS
    tmp.rename(dst)
    return sha256(dst / "SHA256SUMS")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v1.0")
    ap.add_argument("--src", default=str(ROOT / "taxonomy" / "v0"))
    a = ap.parse_args(argv)
    dst = Path(a.src).parent / a.version
    try:
        digest = freeze(Path(a.src), dst)
    except FileExistsError as e:
        print(e, file=sys.stderr)
        return 1
    print(f"{dst}  SHA256SUMS sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
