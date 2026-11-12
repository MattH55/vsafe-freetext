"""Validation against CDC MedDRA coding (amendment 1) on synthetic entries."""

import duckdb
import pytest

from vsafe_ft import config, validate


@pytest.fixture
def con(tmp_path):
    c = duckdb.connect()
    c.execute("""CREATE TABLE entries_survey (entry_id BIGINT, registrant VARCHAR, text VARCHAR,
                 redacted BOOLEAN, survey_matched BOOLEAN, survey_type VARCHAR)""")
    c.execute("CREATE TABLE entry_meddra (entry_id BIGINT, meddra_release VARCHAR, pt VARCHAR)")
    c.execute("""CREATE TABLE entry_themes (entry_id BIGINT, theme VARCHAR, confidence DOUBLE,
                 layer INTEGER, method VARCHAR)""")
    c.execute("CREATE TABLE entry_flags (entry_id BIGINT, third_party BOOLEAN, pre_vaccine BOOLEAN)")
    e, m, t, f = [], [], [], []
    i = 0
    # 40 long-term people: CDC codes Fatigue on all; lexicon labels fatigue on 36 (recall .9)
    for p in range(40):
        i += 1
        e.append((i, f"a{p}", f"t{i}", False, True, "6 month"))
        m.append((i, "2024-11", "Fatigue"))
        if p < 36:
            t.append((i, "fatigue_pem", 1.0, 1, "lexicon"))
    # 4 more: lexicon says fatigue, CDC coded Headache only (precision 36/40)
    for p in range(4):
        i += 1
        e.append((i, f"b{p}", f"t{i}", False, True, "12 month"))
        m.append((i, "2024-11", "Headache"))
        t.append((i, "fatigue_pem", 1.0, 1, "lexicon"))
    # excluded: early survey, pre-vaccine, uncoded, other release
    i += 1; e.append((i, "c", "x", False, True, "day 1")); m.append((i, "2024-11", "Fatigue"))
    i += 1; e.append((i, "d", "y", False, True, "3 month")); m.append((i, "2024-11", "Fatigue"))
    f.append((i, False, True))
    i += 1; e.append((i, "g", "z", False, True, "3 month"))
    i += 1; e.append((i, "h", "w", False, True, "3 month")); m.append((i, "2023-06", "Fatigue"))
    c.executemany("INSERT INTO entries_survey VALUES (?, ?, ?, ?, ?, ?)", e)
    c.executemany("INSERT INTO entry_meddra VALUES (?, ?, ?)", m)
    c.executemany("INSERT INTO entry_themes VALUES (?, ?, ?, ?, ?)", t)
    c.executemany("INSERT INTO entry_flags VALUES (?, ?, ?)", f)
    mp = tmp_path / "map.csv"
    mp.write_text("theme,pt,people\nfatigue_pem,Fatigue,40\npain,Headache,4\n", encoding="utf-8")
    return c, mp


def _registered(monkeypatch, amendment):
    real = config.analysis()
    monkeypatch.setattr(config, "analysis", lambda: {**real, "osf_registration": "osf.io/x",
                                                     "amendment_1": amendment})


def test_refused_before_amendment(con, monkeypatch):
    con, mp = con
    _registered(monkeypatch, None)
    with pytest.raises(PermissionError):
        validate.meddra_reference(con, map_path=mp)


def test_precision_recall_and_gate(con, monkeypatch):
    con, mp = con
    _registered(monkeypatch, "osf.io/x/amendment")
    out = validate.meddra_reference(con, map_path=mp)
    fat = out.filter(out["theme"] == "fatigue_pem").row(0, named=True)
    assert fat["reference_entries"] == 40 and fat["predicted_entries"] == 40
    assert fat["both_entries"] == 36
    assert fat["precision"] == pytest.approx(0.9) and fat["recall"] == pytest.approx(0.9)
    assert fat["precision_lo"] < 0.9 < fat["precision_hi"] and fat["passes_gate"]
    pain = out.filter(out["theme"] == "pain").row(0, named=True)   # 4 people: suppressed
    assert pain["suppressed"] and pain["passes_gate"] is None and pain["recall"] is None
    assert "text" not in out.columns and "registrant" not in out.columns
