"""Exercise the DuckDB link SQL on synthetic Parquet with a stand-in column mapping."""

import duckdb
import polars as pl
import pytest

from vsafe_ft import config, link

COLS = {
    "freetext": {"registrant": "REG", "survey_static_id": "SURVEY_STATIC_ID",
                 "response_id": "RESPONSE_ID", "started_on": "STARTED_ON",
                 "text_sd": "SD", "text_sro": "SRO", "text_hcvo": "HCVO"},
    "vaccinations": {"registrant": "REG", "vaccination_date": "VDATE", "dose_number": "DOSE",
                     "manufacturer": "MFR", "age_band": "AGE"},
    "health_checkins": {"survey_static_id": "SID", "survey_type": "STYPE", "survey_day": "SDAY",
                        "medical_care": "CARE", "health_impact": "IMPACT"},
}


@pytest.fixture
def con(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "columns", lambda t, require=True: COLS[t])
    ft = pl.DataFrame({
        "REG": ["a", "a", "a", "b"], "SURVEY_STATIC_ID": ["s1", "s1", "s2", "s3"],
        "RESPONSE_ID": ["1", "1", "2", "3"],
        "STARTED_ON": ["2021-03-05 10:00:00", "2021-03-05 10:00:00", "2021-07-01 09:00:00",
                       "2021-01-01 00:00:00"],
        "SD": ["tired", "tired", None, "my doctor (b)(6) said"], "SRO": [None, None, "dizzy", None],
        "HCVO": [None, None, None, None],
        "_release": ["r01", "r02", "r01", "r01"], "_row": [1, 1, 2, 3], "_content_hash": ["h"] * 4,
    })
    ft.write_parquet(tmp_path / "ft.parquet")
    pl.DataFrame({"REG": ["a", "a"], "VDATE": ["2021-03-01", "2021-03-29"], "DOSE": ["1", "2"],
                  "MFR": ["X", "X"], "AGE": ["30-39"] * 2}).write_parquet(tmp_path / "vax.parquet")
    pl.DataFrame({"SID": ["s1", "s2"], "STYPE": ["day", "3m"], "SDAY": ["4", "90"],
                  "CARE": [None, "doctor"], "IMPACT": [None, "missed work"]}
                 ).write_parquet(tmp_path / "chk.parquet")
    c = duckdb.connect()
    link.build_entries(c, str(tmp_path / "ft.parquet"))
    link.link_dose(c, str(tmp_path / "vax.parquet"))
    link.link_survey(c, str(tmp_path / "chk.parquet"))
    return c


def test_dedupe_and_redaction(con):
    rows = con.execute("SELECT registrant, field, redacted, n_copies FROM entries ORDER BY 1, 2").fetchall()
    assert rows == [("a", "SD", False, 2), ("a", "SRO", False, 1), ("b", "SD", True, 1)]


def test_days_since_most_recent_dose(con):
    got = dict(con.execute(
        "SELECT survey_static_id, days_since_dose FROM entries_dose WHERE registrant='a'").fetchall())
    assert got == {"s1": 4, "s2": 94}   # s2 anchors to dose 2 (2021-03-29), not dose 1
    assert con.execute(
        "SELECT flag_before_any_dose FROM entries_dose WHERE registrant='b'").fetchone()[0]


def test_join_rates(con):
    r = link.join_rates(con)
    assert r["n_entries"] == 3
    assert r["survey_matched"] == pytest.approx(2 / 3)
