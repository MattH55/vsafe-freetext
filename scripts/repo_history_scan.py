"""Scan the whole git history for strings shaped like registrant codes.

The code shape (length and character classes) is derived from the database without printing any
code; the history (`git log --all -p`) is then scanned for that shape and only counts are
reported, with the files and commits in which matches occur. Opens the database read-only.

Usage: python scripts/repo_history_scan.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vsafe_ft import config


def code_shape(con) -> tuple[str, dict]:
    """A regular expression for the registrant code shape, from length and class counts."""
    rows = con.execute("""
        SELECT length(registrant) AS n,
               regexp_matches(registrant, '^[0-9]+$') AS digits_only,
               regexp_matches(registrant, '^[A-Za-z0-9]+$') AS alnum,
               count(*) AS c
        FROM (SELECT registrant FROM registrants USING SAMPLE 200000 ROWS)
        GROUP BY ALL ORDER BY c DESC""").fetchall()
    total = sum(r[3] for r in rows)
    lengths = Counter()
    for n, d, a, c in rows:
        lengths[n] += c
    (lo, hi) = (min(lengths), max(lengths))
    digits_only = sum(c for n, d, a, c in rows if d) / total
    alnum = sum(c for n, d, a, c in rows if a) / total
    cls = "[0-9]" if digits_only > 0.99 else "[A-Za-z0-9]" if alnum > 0.99 else r"\S"
    pattern = rf"(?<![A-Za-z0-9]){cls}{{{lo},{hi}}}(?![A-Za-z0-9])"
    return pattern, {"length_min": lo, "length_max": hi, "digits_only_share": round(digits_only, 4),
                     "alnum_share": round(alnum, 4), "sampled": total}


def main() -> int:
    db = config.DATA_DIR / "interim" / f"{config.DB_NAME}.duckdb"
    con = duckdb.connect(str(db), read_only=True)
    pattern, shape = code_shape(con)
    print("code shape:", shape)
    # exact membership check: hash set of all registrant codes (kept in memory, never printed)
    codes = {r[0] for r in con.execute("SELECT registrant FROM registrants").fetchall()}
    con.close()
    log = subprocess.run(["git", "log", "--all", "-p", "--no-color", "--pretty=format:@@COMMIT %H"],
                         check=False, capture_output=True, text=True, encoding="utf-8", errors="replace",
                         cwd=Path(__file__).resolve().parents[1]).stdout
    commit, file = None, None
    shape_hits, exact_hits = Counter(), Counter()
    rx = re.compile(pattern)
    for line in log.splitlines():
        if line.startswith("@@COMMIT "):
            commit = line.split()[1][:10]
        elif line.startswith("+++ b/"):
            file = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            for m in rx.findall(line):
                shape_hits[(commit, file)] += 1
                if m in codes:
                    exact_hits[(commit, file)] += 1
    print(f"shape-like matches in added lines: {sum(shape_hits.values())} across {len(shape_hits)} (commit, file) pairs")
    for (c, f), n in shape_hits.most_common(15):
        print(f"  {n:6}  {c}  {f}")
    print(f"EXACT registrant-code matches: {sum(exact_hits.values())} across {len(exact_hits)} (commit, file) pairs")
    for (c, f), n in exact_hits.most_common(15):
        print(f"  {n:6}  {c}  {f}")
    return 0 if not exact_hits else 1


if __name__ == "__main__":
    sys.exit(main())
