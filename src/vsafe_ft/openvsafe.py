"""OpenVSafe's v-safe-to-VAERS matches, read from its public person pages.

OpenVSafe (openvsafe.org, a project of OpenVAERS) matches each call-center case whose
outcome says a VAERS report was filed to the v-safe-marked VAERS reports, scoring timing,
dose and shared symptoms out of 11 (high confidence: >= 8 and >= 3 ahead of the runner-up).
It publishes no bulk file, so we read the "Possible VAERS report" table on
/registrant/<code> for the people our call-center data marks as VAERS-filed.

- robots.txt (read 2026-11-10) allows /registrant/ pages; /search and /api/ are disallowed
  and never requested. One request per second by default, resumable.
- A person page also shows that person's free text, possibly long-term entries (rule 5).
  The page is parsed in memory and discarded: only VAERS ID, confidence, score and runner-up
  score are kept. Nothing else from the page (state, symptoms, dates, text) is stored,
  logged or printed.
- Results go to their own DuckDB file (<DATA_DIR>/interim/openvsafe.duckdb) so the long
  crawl does not lock the main database.
"""

from __future__ import annotations

import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import duckdb

from . import config

BASE = "https://openvsafe.org/registrant/"
USER_AGENT = "vsafe-freetext-research/0.1"
DDL = """
CREATE TABLE IF NOT EXISTS ovs_fetch (registrant VARCHAR PRIMARY KEY, status VARCHAR,
    http_code INTEGER, candidates INTEGER, fetched_at TIMESTAMP);
CREATE TABLE IF NOT EXISTS ovs_matches (registrant VARCHAR, rank INTEGER, vaers_id BIGINT,
    confidence VARCHAR, score INTEGER, runner_up INTEGER);
"""
_SECTION = re.compile(r'<section class="[^"]*\bvaers-banner\b[^"]*">(.*?)</section>', re.DOTALL)
_ROW = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.DOTALL)
_CELL = re.compile(r"<t([hd])\b[^>]*>(.*?)</t\1>", re.DOTALL)
_TAG = re.compile(r"<[^>]+>")
_ID = re.compile(r"/report/(\d+)")
_SCORE = re.compile(r"^(\d+)\s*/\s*11$")
KEEP = {"VAERS ID": "vaers_id", "Confidence": "confidence", "Score": "score",
        "Runner-up": "runner_up"}


def _text(cell: str) -> str:
    return " ".join(_TAG.sub(" ", cell).split())


def parse(html: str) -> list[dict]:
    """The candidate rows of the 'Possible VAERS report' table, kept columns only.

    Raises ValueError if the table is present but its header has changed (so a site change
    stops the crawl instead of silently storing the wrong column)."""
    m = _SECTION.search(html)
    if not m:
        return []
    rows = _ROW.findall(m.group(1))
    if not rows:
        return []
    head = [_text(c) for _, c in _CELL.findall(rows[0])]
    if not set(KEEP) <= set(head):
        raise ValueError(f"match table header changed: missing {sorted(set(KEEP) - set(head))}")
    pos = {KEEP[h]: i for i, h in enumerate(head) if h in KEEP}
    out = []
    for r in rows[1:]:
        cells = [c for _, c in _CELL.findall(r)]
        if len(cells) < len(head):
            continue
        idm = _ID.search(cells[pos["vaers_id"]]) or re.search(r"(\d+)", _text(cells[pos["vaers_id"]]))
        sc = _SCORE.match(_text(cells[pos["score"]]))
        ru = re.match(r"^(\d+)", _text(cells[pos["runner_up"]]))
        conf = _text(cells[pos["confidence"]]).lower()
        out.append({
            "vaers_id": int(idm.group(1)) if idm else None,
            "confidence": conf if re.fullmatch(r"[a-z]{1,10}", conf) else None,
            "score": int(sc.group(1)) if sc else None,
            "runner_up": int(ru.group(1)) if ru else None,
        })
    return out


def _get(url: str, timeout: float) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""


def connect(path: Path | None = None) -> duckdb.DuckDBPyConnection:
    path = path or config.DATA_DIR / "interim" / "openvsafe.duckdb"
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    con.execute(DDL)
    return con


def crawl(con, registrants: list[str], *, rate: float = 1.0, get=_get, timeout: float = 30,
          sleep=time.sleep, log=print, max_errors: int = 50) -> dict:
    """Fetch and parse each registrant not yet fetched; returns counts only."""
    done = {r for (r,) in con.execute("SELECT registrant FROM ovs_fetch").fetchall()}
    todo = [r for r in registrants if r not in done]
    n = found = errors = 0
    t0 = time.time()
    for code in todo:
        start = time.time()
        for attempt in range(4):
            status, html = get(BASE + code, timeout)
            if status not in (429, 500, 502, 503, 504):
                break
            sleep(30 * (attempt + 1))
        if status == 200:
            rows = parse(html)
            st = "match" if rows else "no_match"
        else:
            rows, st = [], "not_found" if status == 404 else "error"
            errors += st == "error"
        del html
        con.execute("INSERT INTO ovs_fetch VALUES (?, ?, ?, ?, now())",
                    [code, st, status, len(rows)])
        for i, r in enumerate(rows, 1):
            con.execute("INSERT INTO ovs_matches VALUES (?, ?, ?, ?, ?, ?)",
                        [code, i, r["vaers_id"], r["confidence"], r["score"], r["runner_up"]])
        n += 1
        found += bool(rows)
        if errors >= max_errors:
            log(f"stopping: {errors} errors")
            break
        if n % 500 == 0:
            log(f"{n}/{len(todo)} fetched, {found} with a match, {errors} errors, "
                f"{time.time() - t0:.0f} s")
        wait = 1 / rate - (time.time() - start)
        if wait > 0:
            sleep(wait)
    return {"requested": n, "with_match": found, "errors": errors, "already_done": len(done),
            "seconds": round(time.time() - t0)}


def summary(con) -> list[tuple]:
    """Counts by fetch status and by best-match confidence (no identifiers)."""
    return con.execute("""
        SELECT f.status, m.confidence, count(*) AS people
        FROM ovs_fetch f LEFT JOIN ovs_matches m ON m.registrant = f.registrant AND m.rank = 1
        GROUP BY ALL ORDER BY ALL""").fetchall()
