"""Check that no run of 5 or more consecutive words in the submission files occurs in the free
text of the corpus. Reports counts only, never the matching words.

Usage: python scripts/quote_scan.py docs/submission/manuscript.txt [more text files...]
Needs VSAFE_DATA_DIR / VSAFE_DB; opens the database read-only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vsafe_ft import config

import os

N = int(os.environ.get("QUOTE_SCAN_N", "5"))     # run length in words; 5 per the brief, 8 as a stricter check


def grams(text: str) -> set[str]:
    words = [w for w in re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split() if w]
    return {" ".join(words[i:i + N]) for i in range(len(words) - N + 1)}


def main(paths: list[str]) -> int:
    g = set()
    for p in paths:
        g |= grams(Path(p).read_text(encoding="utf-8"))
    print(f"{len(g)} distinct {N}-word runs in {len(paths)} file(s)")
    db = config.DATA_DIR / "interim" / f"{config.DB_NAME}.duckdb"
    con = duckdb.connect(str(db), read_only=True)
    con.execute("SET memory_limit = '6GB'")
    con.execute("CREATE TEMP TABLE grams (gram VARCHAR, h UBIGINT)")
    con.executemany("INSERT INTO grams VALUES (?, hash(?))", [(x, x) for x in g])
    hits = con.execute(f"""
        WITH t AS (SELECT list_filter(string_split(regexp_replace(lower(text), '[^a-z0-9 ]+', ' ', 'g'), ' '),
                                      lambda x: x <> '') AS w
                   FROM entries WHERE length(coalesce(text, '')) >= 20),
             x AS (SELECT w, unnest(generate_series(1, len(w) - {N - 1})) AS i FROM t WHERE len(w) >= {N}),
             eh AS (SELECT DISTINCT hash(array_to_string(w[i:i + {N - 1}], ' ')) AS h FROM x)
        SELECT count(*) FROM grams g WHERE g.h IN (SELECT h FROM eh)""").fetchone()[0]
    print(f"{hits} of those runs also occur in the corpus free text (count only; nothing printed)")
    # runs that are part of the survey's own answer options (quoted in Methods) are not quotations
    opts = [r[0] for r in con.execute("""
        SELECT DISTINCT v FROM (SELECT health_impact AS v FROM checkins UNION SELECT medical_care FROM checkins
                                UNION SELECT health_now FROM checkins) WHERE v IS NOT NULL""").fetchall()]
    opt_grams = set()
    for o in opts:
        opt_grams |= grams(o.replace(":", " "))
    con.execute("CREATE TEMP TABLE opt (h UBIGINT)")
    con.executemany("INSERT INTO opt VALUES (hash(?))", [(x,) for x in opt_grams])
    hits2 = con.execute(f"""
        WITH t AS (SELECT list_filter(string_split(regexp_replace(lower(text), '[^a-z0-9 ]+', ' ', 'g'), ' '),
                                      lambda x: x <> '') AS w
                   FROM entries WHERE length(coalesce(text, '')) >= 20),
             x AS (SELECT w, unnest(generate_series(1, len(w) - {N - 1})) AS i FROM t WHERE len(w) >= {N}),
             eh AS (SELECT DISTINCT hash(array_to_string(w[i:i + {N - 1}], ' ')) AS h FROM x)
        SELECT count(*) FROM grams g WHERE g.h IN (SELECT h FROM eh) AND g.h NOT IN (SELECT h FROM opt)""").fetchone()[0]
    print(f"{hits2} of those are not part of a survey answer option quoted in Methods")
    return 0 if hits2 == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
