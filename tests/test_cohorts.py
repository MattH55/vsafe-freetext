"""Levi & Lu cohort rules on synthetic check-ins (task 3.9) and the overlap cross-tab (5.4)."""

import duckdb

from vsafe_ft import cohorts


def _con():
    con = duckdb.connect()
    con.execute("""CREATE TABLE ll_people (registrant VARCHAR, sex VARCHAR, max_dose INTEGER)""")
    con.executemany("INSERT INTO ll_people VALUES (?, ?, ?)", [
        ("A", "Female", 2), ("B", "Male", 3), ("C", "Female", 1), ("D", "Female", 2),
        ("E", "Male", 3), ("F", "Female", None)])
    con.execute("""CREATE TABLE ll_checkins (registrant VARCHAR, dose_number INTEGER, rnk INTEGER,
                   worse BOOLEAN, attributed VARCHAR)""")
    con.executemany("INSERT INTO ll_checkins VALUES (?, ?, ?, ?, ?)", [
        ("A", 1, 3, True, "No"), ("A", 2, 3, True, "Yes"),      # mixed No then Yes -> Prolonged-AE
        ("B", 2, 4, True, "Yes"), ("B", 3, 3, False, None),     # qualifies at dose 2 of 3
        ("C", 1, 3, True, "No"), ("C", 1, 4, True, None),       # worse, never Yes -> NoAttr
        ("D", 2, 3, False, "No"),                               # never worse -> control
        # E: no monthly survey at all -> control; F: no dose, no survey -> control, dose group 0
    ])
    return con


def test_cohort_rules():
    con = _con()
    cohorts.build(con)
    rows = dict(con.execute("SELECT registrant, cohort FROM ll_cohorts").fetchall())
    assert rows == {"A": "prolonged_ae", "B": "prolonged_ae", "C": "prolonged_noattr",
                    "D": "control", "E": "control", "F": "control"}
    dg = dict(con.execute("SELECT registrant, dose_group FROM ll_cohorts").fetchall())
    assert dg["B"] == "3+" and dg["A"] == "2" and dg["F"] == "0"
    assert con.execute("SELECT count(*) FROM ll_cohorts").fetchone()[0] == 6   # three groups sum to everyone


def test_counts_table_has_every_target(monkeypatch):
    monkeypatch.setattr(cohorts, "safe", lambda df, *a: df)
    con = _con()
    cohorts.build(con)
    df = cohorts.counts(con)
    assert set(df["group"]) == set(cohorts.TARGETS)
    assert df.filter(df["group"] == "prolonged_ae")["ours"][0] == 2
    assert df.filter(df["group"] == "women_prolonged_ae")["ours"][0] == 1


def test_overlap_kappa(monkeypatch):
    monkeypatch.setattr(cohorts, "safe", lambda df, *a: df)
    con = _con()
    cohorts.build(con)
    con.execute("""CREATE TABLE phenotype_groups AS SELECT * FROM (VALUES
        ('A', '1', 'case', true), ('B', '2', 'other', true), ('C', '1', 'case', true),
        ('D', '2', 'no_symptoms', true), ('E', '1', 'no_symptoms', true))
        t(registrant, dose_number, grp, in_denominator)""")
    df = cohorts.overlap(con)
    cells = dict(zip(df["cell"], df["people"]))
    assert cells["both"] == 1 and cells["text-defined only"] == 1 and cells["Levi & Lu only"] == 1
    assert cells["neither"] == 2 and cells["total"] == 5
    kappa = df.filter(df["cell"] == "Cohen's kappa")["value"][0]
    assert -1 <= kappa <= 1
