"""Q1-Q2 wiring on synthetic data (no participant data)."""

import duckdb
import numpy as np

from vsafe_ft import analysis, phenotype

P = "pacvs"


def test_q1_test_detects_clustering_and_returns_pairs():
    rng = np.random.default_rng(1)
    n = 2000
    latent = rng.random(n) < 0.2
    X = np.column_stack([latent & (rng.random(n) < 0.8) | (rng.random(n) < 0.05)
                         for _ in range(3)])
    res, pairs = analysis.q1_test(X, ["a", "b", "c"], permutations=99, seed=1)
    assert res.p_pairs <= 0.01
    assert pairs.height == 3
    assert set(pairs.columns) >= {"domain_a", "domain_b", "both_people", "p", "p_holm"}


def test_q1_test_null_not_rejected():
    rng = np.random.default_rng(2)
    X = rng.random((3000, 3)) < 0.2
    res, _ = analysis.q1_test(X, ["a", "b", "c"], permutations=199, seed=2)
    assert res.p_pairs > 0.05


def _con():
    con = duckdb.connect()
    con.execute("""CREATE TABLE ph_surveys (registrant VARCHAR, dose_number VARCHAR,
                   response_id VARCHAR, survey_type VARCHAR, worse BOOLEAN, impact BOOLEAN)""")
    con.executemany("INSERT INTO ph_surveys VALUES (?, ?, ?, ?, ?, ?)", [
        ("A", "1", "A1", "w1", False, False), ("A", "1", "A3", "3m", True, False),
        ("A", "1", "A6", "6m", False, False),
        ("B", "1", "B1", "w1", False, False), ("B", "1", "B3", "3m", False, True),
        ("C", "1", "C1", "w1", False, True), ("C", "1", "C3", "3m", False, False),
        ("C", "1", "C6", "6m", False, False),
    ])
    con.execute("""CREATE TABLE ph_entry_themes (registrant VARCHAR, dose_number VARCHAR,
                   response_id VARCHAR, theme VARCHAR, domain VARCHAR)""")
    con.executemany("INSERT INTO ph_entry_themes VALUES (?, ?, ?, ?, ?)", [
        ("A", "1", "A1", "pain", P),                                     # early onset
        ("A", "1", "A3", "pain", P), ("A", "1", "A3", "sleep", P),
        ("A", "1", "A6", "sleep", P),                                    # persists
        ("B", "1", "B3", "fatigue_pem", P), ("B", "1", "B3", "cognitive", P),
        ("C", "1", "C6", "pain", P),                                     # group c, later domain
    ])
    phenotype.build(con)
    rank = " ".join(f"WHEN '{k}' THEN {v}" for k, v in analysis.SURVEY_RANK.items())
    con.execute(f"""CREATE TABLE ph_rank AS SELECT registrant, dose_number, response_id,
        survey_type, CASE survey_type {rank} END AS rnk, worse, impact FROM ph_surveys""")
    con.execute("CREATE TABLE entries_survey (registrant VARCHAR, dose_number VARCHAR, "
                "response_id VARCHAR, redacted BOOLEAN, text VARCHAR)")
    analysis.helper_tables(con)
    return con


def test_q2_onset_and_persistence_counts(monkeypatch):
    monkeypatch.setattr(analysis, "safe", lambda df, *a: df)    # tiny synthetic cells
    out = analysis.q2(_con())
    onset = out["onset"].row(0, named=True)
    assert onset["people"] == 2 and onset["early_onset_people"] == 1
    pers = out["persistence"].row(0, named=True)
    assert (pers["case_people"], pers["case_persist_people"]) == (1, 1)     # only A has a later survey
    assert (pers["group_c_people"], pers["group_c_persist_people"]) == (1, 1)
