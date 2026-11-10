"""OpenVSafe match parser and crawler on synthetic pages: no network, no real data."""

import duckdb
import pytest

from vsafe_ft import openvsafe

HEAD = ("<tr><th>VAERS ID</th><th>Confidence</th><th class='num'>Score</th>"
        "<th class='num'>Runner-up</th><th>Shared symptoms</th><th>Dose</th><th>State</th>"
        "<th>VAERS vaccinated / onset / received</th><th>Call case</th></tr>")


def page(rows, banner=True):
    body = "".join(
        f"<tr><td><a class='offsite' href='https://www.openvaers.com/search-vaers/report/{i}'>"
        f"<b>{i}</b></a></td><td><span class='chip conf-{c}'>{c}</span></td>"
        f"<td class='num'>{s} / 11</td><td class='num'>{r}</td><td>SECRET SYMPTOM</td>"
        f"<td>2</td><td>ZZ</td><td>dates</td><td>case</td></tr>" for i, c, s, r in rows)
    sec = (f'<section class="panel vaers-banner"><h2>Possible VAERS report</h2>'
           f'<div class="scroll"><table>{HEAD}{body}</table></div></section>') if banner else ""
    return f"<html><body><p>FREE TEXT ENTRY</p>{sec}<p>MORE TEXT</p></body></html>"


def test_parse_keeps_only_match_fields():
    got = openvsafe.parse(page([(2290599, "high", 10, 4), (1111111, "medium", 6, "")]))
    assert got == [
        {"vaers_id": 2290599, "confidence": "high", "score": 10, "runner_up": 4},
        {"vaers_id": 1111111, "confidence": "medium", "score": 6, "runner_up": None}]
    assert openvsafe.parse(page([], banner=False)) == []


def test_header_change_stops():
    html = page([(1, "high", 9, 2)]).replace("Runner-up", "Second")
    with pytest.raises(ValueError, match="header changed"):
        openvsafe.parse(html)


def test_crawl_resumable_rate_and_nothing_else_stored():
    con = duckdb.connect()
    con.execute(openvsafe.DDL)
    pages = {"A": (200, page([(5, "high", 9, 3)])), "B": (200, page([], banner=False)),
             "C": (404, "")}
    calls, sleeps = [], []

    def get(url, timeout):
        code = url.rsplit("/", 1)[1]
        calls.append(code)
        return pages[code]

    run = openvsafe.crawl(con, ["A", "B", "C"], rate=2, get=get, sleep=sleeps.append,
                          log=lambda *_: None)
    assert run["requested"] == 3 and run["with_match"] == 1 and run["errors"] == 0
    assert all(s <= 0.5 for s in sleeps)
    st = dict(con.execute("SELECT registrant, status FROM ovs_fetch").fetchall())
    assert st == {"A": "match", "B": "no_match", "C": "not_found"}
    dump = str(con.execute("SELECT * FROM ovs_matches").fetchall())
    assert "SECRET" not in dump and "ZZ" not in dump and "FREE TEXT" not in dump
    cols = [c[0] for c in con.execute("DESCRIBE ovs_matches").fetchall()]
    assert cols == ["registrant", "rank", "vaers_id", "confidence", "score", "runner_up"]
    calls.clear()
    openvsafe.crawl(con, ["A", "B", "C", "D"], get=lambda u, t: (200, page([])),
                    sleep=lambda s: None, log=lambda *_: None)
    assert con.execute("SELECT count(*) FROM ovs_fetch").fetchone()[0] == 4   # only D fetched


def test_retries_on_429():
    con = duckdb.connect()
    con.execute(openvsafe.DDL)
    seq = [(429, ""), (200, page([(7, "high", 8, 1)]))]
    openvsafe.crawl(con, ["A"], get=lambda u, t: seq.pop(0), sleep=lambda s: None,
                    log=lambda *_: None)
    assert con.execute("SELECT status FROM ovs_fetch").fetchone()[0] == "match"
