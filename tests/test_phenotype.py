"""Case definition and comparison groups on hand-built synthetic people."""

import duckdb
import pytest

from vsafe_ft import phenotype

# (registrant, dose, survey id, survey type, worse, impact)
SURVEYS = [
    ("A", "1", "A3", "3m", True, False),
    ("B", "1", "B3", "3m", False, False), ("B", "1", "B6", "6m", False, True),
    ("C", "1", "C3", "3m", True, False),
    ("D", "1", "D3", "3m", False, False),
    ("E", "1", "E1", "w1", False, False), ("E", "1", "E3", "3m", False, False),
    ("F", "1", "F1", "w1", False, True), ("F", "1", "F3", "3m", False, False),
    ("G", "1", "G3", "3m", True, False),
    ("H", "1", "H3", "3m", False, False),
    ("I", "1", "I1", "w1", False, True),                        # no long-term survey
]
P, X = "pacvs", "exclusion"
THEMES = [
    ("A", "1", "A3", "fatigue_pem", P), ("A", "1", "A3", "cognitive", P),
    ("B", "1", "B3", "fatigue_pem", P), ("B", "1", "B6", "sleep", P),
    ("C", "1", "C3", "fatigue_pem", P), ("C", "1", "C3", "pain", P),
    ("C", "1", "C3", "unrelated_cause", X),
    ("E", "1", "E1", "acute_diagnosis", X),
    ("G", "1", "G3", "fatigue_pem", P),
    ("H", "1", "H3", "fatigue_pem", P), ("H", "1", "H3", "dysautonomia", P),
]


@pytest.fixture
def groups():
    con = duckdb.connect()
    con.execute("""CREATE TABLE ph_surveys (registrant VARCHAR, dose_number VARCHAR,
                   response_id VARCHAR, survey_type VARCHAR, worse BOOLEAN, impact BOOLEAN)""")
    con.executemany("INSERT INTO ph_surveys VALUES (?, ?, ?, ?, ?, ?)", SURVEYS)
    con.execute("""CREATE TABLE ph_entry_themes (registrant VARCHAR, dose_number VARCHAR,
                   response_id VARCHAR, theme VARCHAR, domain VARCHAR)""")
    con.executemany("INSERT INTO ph_entry_themes VALUES (?, ?, ?, ?, ?)", THEMES)
    phenotype.build(con)
    rows = con.execute("SELECT registrant, grp, in_denominator FROM phenotype_groups").fetchall()
    return {r: (g, d) for r, g, d in rows}


@pytest.mark.parametrize("who,grp", [
    ("A", "case"),                  # >= 2 domains at a worse 3-month survey
    ("B", "case"),                  # 2 domains across 2 long-term surveys, impact at 6 months
    ("C", "other"),                 # criterion 3: unrelated cause named at the same survey
    ("D", "no_symptoms"),
    ("E", "acute_event"),
    ("F", "severe_w1_recovered"),
    ("G", "other"),                 # worse, but one domain only
    ("H", "other"),                 # two domains, but neither worse nor impact
])
def test_groups(groups, who, grp):
    assert groups[who][0] == grp


def test_denominator_is_long_term_completers(groups):
    assert all(groups[w][1] for w in "ABCDEFGH")
    assert "I" not in groups or not groups["I"][1]


def test_long_term_prepare_refused_before_registration():
    with pytest.raises(PermissionError):
        phenotype.prepare(duckdb.connect(), {"MONTH_3": "3m"}, [], [], {})


def test_prepare_drops_pre_vaccine_keeps_third_party():
    con = duckdb.connect()
    con.execute("""CREATE TABLE checkins AS SELECT * FROM (VALUES
        ('p', 'r1', 'DAY_1', 'worse', 'none', '2021-01-02')) t(registrant, response_id,
        survey_type, health_now, health_impact, started_on)""")
    con.execute("""CREATE TABLE vax AS SELECT * FROM (VALUES ('p', '1', DATE '2021-01-01'))
                   t(registrant, dose_number, vax_date)""")
    con.execute("""CREATE TABLE entries_survey AS SELECT * FROM (VALUES
        (1, 'p', '1', 'r1'), (2, 'p', '1', 'r1'), (3, 'p', '1', 'r1'))
        t(entry_id, registrant, dose_number, response_id)""")
    con.execute("""CREATE TABLE entry_themes AS SELECT * FROM (VALUES
        (1, 'pain'), (2, 'sleep'), (3, 'cognitive')) t(entry_id, theme)""")
    con.execute("""CREATE TABLE entry_flags AS SELECT * FROM (VALUES
        (1, false, false), (2, true, false), (3, false, true))
        t(entry_id, third_party, pre_vaccine)""")
    phenotype.prepare(con, {"DAY_1": "w1"}, ["worse"], [], {"pain": "pacvs", "sleep": "pacvs",
                                                          "cognitive": "pacvs"})
    kept = {r[0] for r in con.execute("SELECT theme FROM ph_entry_themes").fetchall()}
    assert kept == {"pain", "sleep"}
