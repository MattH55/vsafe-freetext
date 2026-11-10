"""Exercise the DuckDB link SQL on synthetic Parquet with a stand-in column mapping."""

import duckdb
import polars as pl
import pytest

from vsafe_ft import config, link

COLS = {
    "freetext": {"registrant": "REG", "survey_static_id": "SURVEY_STATIC_ID",
                 "response_id": "RESPONSE_ID", "started_on": "STARTED_ON",
                 "text_sd": "SD", "text_sro": "SRO", "text_hcvo": "HCVO"},
    "registrants": {"registrant": "REG", "sex": "SEX", "zip3": "ZIP3", "registration_date": "RD",
                    "relationship": "REL", "guardian": "GUARD"},
    "vaccinations": {"registrant": "REG", "vaccination_date": "VDATE", "dose_number": "DOSE",
                     "manufacturer": "MFR", "age_band": "AGE"},
    "health_checkins": {"registrant": "REG", "response_id": "RID", "survey_static_id": "SID",
                        "survey_type": "STYPE",
                        "survey_day": "SDAY", "medical_care": "CARE", "health_impact": "IMPACT",
                        "health_now": "TODO"},
    "meddra": {"registrant": "R", "date": "D", "field": "F", "pt": "PT", "llt": "LLT"},
    "call_center": {"registrant": "REG", "report_date": "RDATE", "vaers_filed": "VAERS"},
}


def fake_columns(table, require=True, keys=None, release=None):
    m = dict(COLS[table])
    if table == "meddra" and release == "m2":
        m["pt"] = "PREFERRED_TERM"          # names differ between releases
    return m


def _ft(rows):
    base = {"REG": [], "SURVEY_STATIC_ID": [], "RESPONSE_ID": [], "STARTED_ON": [], "SD": [],
            "SRO": [], "HCVO": [], "_release": [], "_row": [], "_content_hash": [], "_under3": []}
    for r in rows:
        for k, col in base.items():
            col.append(r.get(k))
    return pl.DataFrame(base, schema={k: (pl.Boolean if k == "_under3" else pl.Int64
                                          if k == "_row" else pl.String) for k in base})


def _r(**kw):
    return kw


FT = [
    _r(REG="a", SURVEY_STATIC_ID="s1", RESPONSE_ID="1", STARTED_ON="2021-03-05 10:00:00",
         SD="tired", _release="r01", _row=1, _under3=False),
    _r(REG="a", SURVEY_STATIC_ID="s1", RESPONSE_ID="1", STARTED_ON="2021-03-05 10:00:00",
         SD="tired", _release="r02", _row=1, _under3=False),
    _r(REG="a", SURVEY_STATIC_ID="s2", RESPONSE_ID="2", STARTED_ON="2021-07-01 09:00:00",
         SRO="  dizzy \n  again ", _release="r01", _row=2, _under3=False),
    _r(REG="b", SURVEY_STATIC_ID="s3", RESPONSE_ID="3", STARTED_ON="2021-01-01 00:00:00",
         SD="my doctor (b)(6) said", _release="r01", _row=3, _under3=False),
    _r(REG="c", SURVEY_STATIC_ID="s4", RESPONSE_ID="4", STARTED_ON="2021-04-01 00:00:00",
         SD="fever", _release="r12_under3", _row=1, _under3=True),
]


@pytest.fixture
def con(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "columns", fake_columns)
    _ft(FT).write_parquet(tmp_path / "ft.parquet")
    pl.DataFrame({"REG": ["a", "b", "b"], "SEX": ["F", "M", "M"], "ZIP3": ["123", "456", "456"],
                  "RD": ["2021-02-01"] * 3, "REL": ["self"] * 3, "GUARD": ["g9", None, None]}
                 ).write_parquet(tmp_path / "reg.parquet")
    pl.DataFrame({"REG": ["a", "a"], "VDATE": ["2021-03-01", "2021-03-29"], "DOSE": ["1", "2"],
                  "MFR": ["X", "X"], "AGE": ["30-39"] * 2}).write_parquet(tmp_path / "vax.parquet")
    pl.DataFrame({"REG": ["a", "a"], "RID": ["1", "2"], "SID": ["s1", "s2"], "STYPE": ["day", "3m"],
                  "SDAY": ["4", "90"], "CARE": [None, "doctor"], "IMPACT": [None, "missed work"]}
                 ).write_parquet(tmp_path / "chk.parquet")
    c = duckdb.connect()
    link.build_entries(c, str(tmp_path / "ft.parquet"))
    link.link_registrants(c, str(tmp_path / "reg.parquet"))
    link.link_dose(c, str(tmp_path / "vax.parquet"))
    link.link_survey(c, str(tmp_path / "chk.parquet"))
    return c


def test_dedupe_and_redaction(con):
    rows = con.execute(
        "SELECT registrant, field, redacted, n_copies FROM entries ORDER BY 1, 2").fetchall()
    assert rows == [("a", "SD", False, 2), ("a", "SRO", False, 1), ("b", "SD", True, 1),
                    ("c", "SD", False, 1)]


def test_normalise_is_the_python_definition(con):
    text, orig = con.execute("SELECT text, text_orig FROM entries WHERE field = 'SRO'").fetchall()[0]
    assert text == "dizzy again"
    assert orig == "  dizzy \n  again "            # text_orig untouched


def test_under3_from_flag(con):
    got = dict(con.execute("SELECT registrant, bool_or(under3) FROM entries GROUP BY 1").fetchall())
    assert got == {"a": False, "b": False, "c": True}


def test_registrants_joined_without_zip3(con):
    cols = [r[0] for r in con.execute("DESCRIBE entries_survey").fetchall()]
    assert {"sex", "relationship", "guardian", "registration_date"} <= set(cols)
    assert not any("zip" in c.lower() for c in cols)
    got = dict(con.execute("SELECT registrant, sex FROM entries").fetchall())
    assert got == {"a": "F", "b": "M", "c": None}   # registrant b deduplicated, c unmatched
    g = dict(con.execute("SELECT registrant, guardian FROM entries").fetchall())
    assert g == {"a": True, "b": False, "c": None}  # a boolean, never the guardian's code


def test_days_since_most_recent_dose(con):
    got = dict(con.execute(
        "SELECT survey_static_id, days_since_dose FROM entries_dose WHERE registrant='a'").fetchall())
    assert got == {"s1": 4, "s2": 94}   # s2 anchors to dose 2 (2021-03-29), not dose 1
    assert con.execute(
        "SELECT flag_before_any_dose FROM entries_dose WHERE registrant='b'").fetchall()[0][0]


def test_join_rates(con):
    r = link.join_rates(con)
    assert r["n_entries"] == 4
    assert r["survey_matched"] == pytest.approx(2 / 4)
    assert r["registrant_matched"] == pytest.approx(3 / 4)


def test_link_meddra_keeps_releases(con, tmp_path):
    pl.DataFrame({"R": ["a", "a", "b"], "D": ["2021-03-05", "2021-07-01", "2021-01-01"],
                  "F": ["sd", "SYMPTOM_OTHER", "SD"], "PT": ["Fatigue", "Dizziness", "X"],
                  "LLT": ["Tired", "Dizzy", "X"]}).write_parquet(tmp_path / "m1.parquet")
    pl.DataFrame({"R": ["a"], "D": ["2021-03-05"], "F": ["SD"], "PREFERRED_TERM": ["Fatigue"],
                  "LLT": ["Tiredness"]}).write_parquet(tmp_path / "m2.parquet")
    link.link_meddra(con, [(str(tmp_path / "m1.parquet"), "m1"), (str(tmp_path / "m2.parquet"), "m2")],
                     field_values={"SYMPTOM_OTHER": "SRO"})
    got = con.execute("""SELECT e.registrant, e.field, m.meddra_release, m.pt
                         FROM entry_meddra m JOIN entries e USING (entry_id) ORDER BY ALL""").fetchall()
    assert got == [("a", "SD", "m1", "Fatigue"), ("a", "SD", "m2", "Fatigue"),
                   ("a", "SRO", "m1", "Dizziness"), ("b", "SD", "m1", "X")]


def test_meddra_coverage_is_suppressed(con, tmp_path):
    pl.DataFrame({"R": ["a"], "D": ["2021-03-05"], "F": ["SD"], "PT": ["F"], "LLT": ["F"]}
                 ).write_parquet(tmp_path / "m.parquet")
    link.link_meddra(con, [(str(tmp_path / "m.parquet"), "m1")])
    cov = link.meddra_coverage(con)
    assert cov["suppressed"].all()                 # every synthetic cell has < 10 people
    assert cov["share_coded"].is_null().all()


def test_link_outcomes_window(con, tmp_path, monkeypatch):
    pl.DataFrame({"REG": ["a", "a", "a"], "RDATE": ["2021-03-10", "2021-09-01", "2021-07-15"],
                  "VAERS": ["N", "Y", "yes"]}).write_parquet(tmp_path / "cc.parquet")
    link.link_outcomes(con, [(str(tmp_path / "cc.parquet"), "cc")], vaers_pattern="")
    got = con.execute("""SELECT e.survey_static_id, o.cc_cases, o.vaers_filed
                         FROM entry_outcomes o JOIN entries e USING (entry_id)
                         WHERE e.registrant = 'a' ORDER BY 1""").fetchall()
    # s1 (2021-03-05): only 03-10 is within 90 d (07-15 is 132 d later).
    # s2 (2021-07-01): 07-15 (14 d) and 09-01 (62 d), one of them a VAERS filing.
    assert got == [("s1", 1, False), ("s2", 2, True)]


def test_link_outcomes_merges_two_files(con, tmp_path, monkeypatch):
    """CDC file (trigger, care) and GDIT file (VAERS outcome) describe the same case."""
    cols = {"cdc": {"registrant": "R", "report_date": "D", "survey_static_id": "S",
                    "trigger": "IMPACT", "care": "VISITS", "outcome": None, "vaers_filed": None},
            "gdit": {"registrant": "RegistrantCode", "report_date": "ReportedDate",
                     "survey_static_id": "SurveyStaticID", "trigger": None, "care": None,
                     "outcome": "FinalOutcome", "vaers_filed": "AllReportOutcomes"}}
    monkeypatch.setattr(config, "columns", lambda table, require=True, keys=None, release=None:
                        cols[release] if table == "call_center" else COLS[table])
    pl.DataFrame({"R": ["a", "a"], "D": ["03/10/2021", "07/15/2021"], "S": ["f1", "f2"],
                  "IMPACT": ["x", "y"], "VISITS": ["Emergency room:Hospitalization", None]}
                 ).write_parquet(tmp_path / "cdc.parquet")
    pl.DataFrame({"RegistrantCode": ["a", "a"], "ReportedDate": ["03/10/2021", "07/15/2021"],
                  "SurveyStaticID": ["f1", "f2"], "FinalOutcome": ["Successful", "Unsuccessful"],
                  "AllReportOutcomes": ["Completed over the phone",
                                        "Participant prefers to complete VAERS report online"]}
                 ).write_parquet(tmp_path / "gdit.parquet")
    link.link_outcomes(con, [(str(tmp_path / "cdc.parquet"), "cdc"),
                             (str(tmp_path / "gdit.parquet"), "gdit")],
                       vaers_pattern="(?i)completed over the phone|reported to vaers")
    cases = con.execute("""SELECT survey_static_id, vaers_filed, cc_care IS NOT NULL, cc_outcome,
                                  len(cc_sources) FROM call_center ORDER BY 1""").fetchall()
    assert cases == [("f1", True, True, "Successful", 2), ("f2", False, False, "Unsuccessful", 2)]
    got = con.execute("""SELECT e.survey_static_id, o.cc_cases, o.vaers_filed, o.cc_hospitalised,
                                o.cc_emergency
                         FROM entry_outcomes o JOIN entries e USING (entry_id)
                         WHERE e.registrant = 'a' ORDER BY 1""").fetchall()
    assert got == [("s1", 1, True, True, True), ("s2", 1, False, False, False)]


def test_crosscheck_counts(tmp_path):
    o, u = tmp_path / "o", tmp_path / "u"
    o.mkdir(), u.mkdir()
    pl.DataFrame({"REG": ["a", "b", "c"], "SD": ["x", "y", "z"], "_row": [1, 2, 3]}
                 ).write_parquet(o / "r01.parquet")
    pl.DataFrame({"REG": ["a", "b", "d"], "SD": ["x", "y", "w"], "SURVEY_STATIC_ID": ["1", "2", "3"],
                  "EXTRA": ["", "", ""], "_row": [1, 2, 3]}).write_parquet(u / "r01.parquet")
    df, cols = link.crosscheck(duckdb.connect(), o, u, registrant_col="REG")
    assert cols["r01"]["updated_extra"] == ["EXTRA"]
    assert cols["r01"]["added_present"] == ["SURVEY_STATIC_ID"]
    assert set(df["metric"]) == {"rows_original", "rows_updated", "only_in_original",
                                 "only_in_updated"}
    assert df["suppressed"].all()                  # 3 people per cell: below the minimum


def test_crosscheck_unsuppressed_values(tmp_path, monkeypatch):
    monkeypatch.setattr(link, "safe", lambda df: df)   # inspect raw counts in the test only
    o, u = tmp_path / "o", tmp_path / "u"
    o.mkdir(), u.mkdir()
    pl.DataFrame({"REG": ["a", "a", "c"], "SD": ["x", "x", "z"]}).write_parquet(o / "r01.parquet")
    pl.DataFrame({"REG": ["a", "d"], "SD": ["x", "w"]}).write_parquet(u / "r01.parquet")
    df, _ = link.crosscheck(duckdb.connect(), o, u, registrant_col="REG")
    got = dict(zip(df["metric"], df["rows"]))
    assert got == {"rows_original": 3, "rows_updated": 2, "only_in_original": 2,
                   "only_in_updated": 1}   # duplicated row counted as a multiset


def test_duplicate_report(con, monkeypatch):
    monkeypatch.setattr(link, "safe", lambda df: df)
    df = link.duplicate_report(con)
    got = dict(zip(df["metric"], df["entries"]))
    assert got["raw_rows"] == 5
    assert got["keys_in_more_than_one_release"] == 1
    assert got["extra_copies_removed"] == 1
    assert got["distinct_entries"] == 4
    assert got["keys_in_under3_and_main_files"] == 0


@pytest.mark.parametrize("days,label", [("0", "day 0"), ("7", "day 7"), ("8", "week 2"),
                                        ("14", "week 2"), ("42", "week 6"), ("90", "3m"),
                                        ("180", "6m"), ("365", "12m"), ("x", None), ("-1", None)])
def test_survey_type_from_days(days, label):
    got = duckdb.connect().execute(
        f"SELECT {link.survey_type_from_days('d')} FROM (SELECT '{days}' AS d)").fetchall()[0][0]
    assert got == label


def test_link_meddra_by_response_id_and_file_field(con, tmp_path, monkeypatch):
    cols = dict(COLS, meddra={"registrant": "R", "response_id": "RID", "date": "D",
                              "field": None, "pt": "PT", "llt": "LLT", "active": "A"})
    monkeypatch.setattr(config, "columns",
                        lambda t, require=True, keys=None, release=None: dict(cols[t]))
    # field comes from the file name in _release; the date is deliberately wrong for "1"
    pl.DataFrame({"R": ["a", "a", "a"], "RID": ["1", "1", "2"],
                  "D": ["1999-01-01", "1999-01-01", "2021-07-01"],
                  "PT": ["Fatigue", "Fatigue", "Dizziness"], "LLT": ["T", "T", "D"],
                  "A": ["Y", "Y", "Y"],  # see test below for inactive codes
                  "_release": ["z/covid_meddra_sd", "z/covid_meddra_sro", "z/covid_meddra_SRO"]}
                 ).write_parquet(tmp_path / "m.parquet")
    link.link_meddra(con, [(str(tmp_path / "m.parquet"), "2024-11")])
    got = con.execute("""SELECT e.response_id, e.field, m.meddra_release, m.pt
                         FROM entry_meddra m JOIN entries e USING (entry_id) ORDER BY ALL""").fetchall()
    assert got == [("1", "SD", "2024-11", "Fatigue"), ("2", "SRO", "2024-11", "Dizziness")]


def test_link_meddra_drops_inactive_codes(con, tmp_path, monkeypatch):
    cols = dict(COLS, meddra={"registrant": "R", "response_id": "RID", "date": "D",
                              "field": None, "pt": "PT", "llt": "LLT", "active": "A"})
    monkeypatch.setattr(config, "columns",
                        lambda t, require=True, keys=None, release=None: dict(cols[t]))
    pl.DataFrame({"R": ["a", "a"], "RID": ["1", "1"], "D": ["2021-03-05"] * 2,
                  "PT": ["Fatigue", "Old term"], "LLT": ["T", "O"], "A": ["YES", "NO"],
                  "_release": ["z/covid_meddra_sd"] * 2}).write_parquet(tmp_path / "m.parquet")
    link.link_meddra(con, [(str(tmp_path / "m.parquet"), "2024-11")])
    assert con.execute("SELECT pt FROM entry_meddra").fetchall() == [("Fatigue",)]


def test_build_entries_on_a_connect_connection(tmp_path, monkeypatch):
    """link.connect() registers the UDFs; build_entries must not fail registering them again."""
    monkeypatch.setattr(config, "columns", fake_columns)
    _ft(FT).write_parquet(tmp_path / "ft.parquet")
    c = link.connect(tmp_path / "t.duckdb")
    link.build_entries(c, str(tmp_path / "ft.parquet"))
    assert c.execute("SELECT count(*) FROM entries").fetchall()[0][0] == 4


def test_survey_join_is_on_response_id_not_form_id(tmp_path, monkeypatch):
    """SURVEY_STATIC_ID is a survey FORM id shared by many check-ins; only RESPONSE_ID links."""
    monkeypatch.setattr(config, "columns", fake_columns)
    _ft(FT).write_parquet(tmp_path / "ft.parquet")
    # two check-ins of the same form; response "2" belongs to a different registrant
    pl.DataFrame({"REG": ["a", "z"], "RID": ["1", "2"], "SID": ["form", "form"],
                  "STYPE": ["day", "day"], "SDAY": ["4", "4"], "CARE": [None, None],
                  "IMPACT": [None, None]}).write_parquet(tmp_path / "chk.parquet")
    pl.DataFrame({"REG": ["a"], "VDATE": ["2021-03-01"], "DOSE": ["1"], "MFR": ["X"],
                  "AGE": ["30-39"]}).write_parquet(tmp_path / "vax.parquet")
    c = duckdb.connect()
    link.build_entries(c, str(tmp_path / "ft.parquet"))
    link.link_dose(c, str(tmp_path / "vax.parquet"))
    link.link_survey(c, str(tmp_path / "chk.parquet"))
    assert c.execute("SELECT count(*) FROM checkins").fetchall()[0][0] == 2
    got = c.execute("SELECT response_id, survey_matched FROM entries_survey ORDER BY 1").fetchall()
    assert got == [("1", True), ("2", False), ("3", False), ("4", False)]


def test_us_format_dates_link(tmp_path, monkeypatch):
    """The CSV exports write dates as MM/DD/YYYY; the .xlsx free text as ISO timestamps."""
    monkeypatch.setattr(config, "columns", fake_columns)
    _ft(FT).write_parquet(tmp_path / "ft.parquet")
    pl.DataFrame({"REG": ["a", "a"], "VDATE": ["03/01/2021", "03/29/2021"], "DOSE": ["1", "2"],
                  "MFR": ["X", "X"], "AGE": [None, None]}).write_parquet(tmp_path / "vax.parquet")
    c = duckdb.connect()
    link.build_entries(c, str(tmp_path / "ft.parquet"))
    link.link_dose(c, str(tmp_path / "vax.parquet"))
    got = c.execute("""SELECT response_id, dose_number, days_since_dose FROM entries_dose
                       WHERE registrant = 'a' ORDER BY 1""").fetchall()
    assert got == [("1", "1", 4), ("2", "2", 94)]
    assert link.parse_date("'12/31/2021'") and c.execute(
        f"SELECT {link.parse_date(chr(39) + '12/31/2021' + chr(39))}").fetchall()[0][0].day == 31
