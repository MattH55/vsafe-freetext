"""Gold set on synthetic entries: draw, blind sheets, kappa, adjudication, guarded P/R."""

import csv

import duckdb
import pytest

from vsafe_ft import config, gold, themes

THEMES = ["pain", "fatigue_pem"]


@pytest.fixture
def con():
    c = duckdb.connect()
    c.execute("""CREATE TABLE entries_survey (entry_id BIGINT, registrant VARCHAR,
                 response_id VARCHAR, field VARCHAR, text VARCHAR, redacted BOOLEAN,
                 survey_matched BOOLEAN, survey_day VARCHAR, survey_type VARCHAR)""")
    rows, i = [], 0
    for p in range(60):
        rows.append((i := i + 1, f"a{p}", f"r{i}", "SRO", f"headache {p % 20}", False, True,
                     "1", "d"))
    for p in range(30):
        rows.append((i := i + 1, f"b{p}", f"r{i}", "SD", f"tired {p}", False, True, "3", "d"))
    for p in range(20):
        rows.append((i := i + 1, f"c{p}", f"r{i}", "HCVO", f"clinic {p}", False, True, "7", "d"))
    for p in range(20):   # long-term: never drawn before registration
        rows.append((i := i + 1, f"s{p}", f"r{i}", "SD", f"late {p}", False, True, "180",
                     "6 month"))
    rows.append((i := i + 1, "t", f"r{i}", "SD", "redacted (b)(6)", True, True, "1", "d"))
    c.executemany("INSERT INTO entries_survey VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    themes.build_entry_themes(c)
    return c


def test_allocate_floor_and_cap():
    a = gold.allocate({"x": 1000, "y": 10, "z": 0}, 100)
    assert sum(a.values()) == 100 and a["y"] == 10 and "z" not in a
    assert gold.allocate({"x": 5}, 100) == {"x": 5}


def test_draw_early_only_and_never_redrawn(con):
    run = gold.draw(con, size=40, seed=3)
    assert run["entries"] == 40
    per = dict(con.execute("SELECT period, count(*) FROM gold_entries GROUP BY 1").fetchall())
    assert per == {"early": 40}
    # weights sum to the stratum populations (early, non-redacted)
    assert con.execute("SELECT round(sum(weight)) FROM gold_entries").fetchone()[0] == 110
    with pytest.raises(FileExistsError):
        gold.draw(con, size=40, seed=4)
    with pytest.raises(PermissionError):
        gold.draw(con, size=10, period="long_term")


def _rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _fill(path, out, rule):
    """Complete a sheet: rule(text) -> set of labels marked 1."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            on = rule(r["text"])
            w.writerow({k: ("1" if k in on else ("" if r[k] == "?" else r[k]))
                        if k in gold.labels(THEMES) else r[k] for k in r})


def test_sheets_kappa_adjudication_and_guard(con, tmp_path):
    gold.draw(con, size=60, seed=1)
    sa = gold.write_sheet(con, "A", THEMES, out=tmp_path / "a.csv")
    sb = gold.write_sheet(con, "B", THEMES, out=tmp_path / "b.csv")
    ids_a = [r["id"] for r in _rows(sa)]
    ids_b = [r["id"] for r in _rows(sb)]
    assert sorted(ids_a) == sorted(ids_b) and ids_a != ids_b        # own shuffled order
    n_texts = con.execute("SELECT count(DISTINCT text_hash) FROM gold_entries").fetchone()[0]
    assert len(ids_a) == n_texts                                     # each text once

    def coder_a(t):
        return {"pain"} if "headache" in t else ({"fatigue_pem"} if "tired" in t else set())

    def coder_b(t):   # disagrees on "tired 1x" texts
        return {"pain"} if "headache" in t else (
            {"fatigue_pem"} if "tired" in t and not t.startswith("tired 1") else set())

    _fill(sa, tmp_path / "a_done.csv", coder_a)
    _fill(sb, tmp_path / "b_done.csv", coder_b)
    gold.load_codes(con, tmp_path / "a_done.csv", "A", THEMES)
    gold.load_codes(con, tmp_path / "b_done.csv", "B", THEMES)
    k = gold.agreement(con, "A", "B")
    assert "text" not in k.columns and "registrant" not in k.columns
    pain = k.filter(k["label"] == "pain").row(0, named=True)
    assert pain["kappa"] == 1.0
    fat = k.filter(k["label"] == "fatigue_pem").row(0, named=True)
    assert fat["kappa"] is None or fat["kappa"] < 1.0

    adj = gold.write_adjudication(con, "A", "B", THEMES, out=tmp_path / "adj.csv")
    adj_rows = _rows(adj)
    assert adj_rows and all(r["text"].startswith("tired 1") for r in adj_rows)
    assert all(r["fatigue_pem"] == "?" for r in adj_rows)
    _fill(adj, tmp_path / "adj_done.csv", coder_a)
    gold.load_codes(con, tmp_path / "adj_done.csv", "adjudication", THEMES)

    with pytest.raises(PermissionError):
        gold.evaluate(con, "A", "B", layer="lexicon")


def test_load_rejects_bad_cells(con, tmp_path):
    gold.draw(con, size=20)
    s = gold.write_sheet(con, "A", THEMES, out=tmp_path / "a.csv")
    _fill(s, tmp_path / "bad.csv", lambda t: set())
    text = (tmp_path / "bad.csv").read_text(encoding="utf-8-sig").splitlines()
    head = text[0].split(",")
    cells = next(csv.reader([text[1]]))
    cells[head.index("pain")] = "maybe"
    out = tmp_path / "bad2.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(head)
        w.writerow(cells)
        w.writerows(csv.reader(text[2:]))
    with pytest.raises(ValueError, match="neither"):
        gold.load_codes(con, out, "A", THEMES)


def test_evaluate_after_registration(con, tmp_path, monkeypatch):
    gold.draw(con, size=60, seed=1)
    s = gold.write_sheet(con, "A", THEMES, out=tmp_path / "a.csv")

    def rule(t):
        return {"pain"} if "headache" in t else set()

    _fill(s, tmp_path / "done.csv", rule)
    gold.load_codes(con, tmp_path / "done.csv", "A", THEMES)
    gold.load_codes(con, tmp_path / "done.csv", "B", THEMES)
    real = config.analysis()
    monkeypatch.setattr(config, "analysis", lambda: {**real, "osf_registration": "osf.io/x"})
    ev = gold.evaluate(con, "A", "B", layer="lexicon")
    pain = ev.filter(ev["label"] == "pain").row(0, named=True)
    assert pain["recall"] == 1.0 and pain["precision"] == 1.0 and pain["passes_gate"]
