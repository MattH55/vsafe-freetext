"""Layer-1 wiring, rule-5 guard and aggregate-only exploration, on synthetic entries."""

import duckdb
import pytest

from vsafe_ft import explore, themes


def _entries(con, rows):
    con.execute("""CREATE TABLE entries_survey (entry_id BIGINT, registrant VARCHAR, field VARCHAR,
                   text VARCHAR, survey_matched BOOLEAN, survey_day VARCHAR, survey_type VARCHAR)""")
    con.executemany("INSERT INTO entries_survey VALUES (?, ?, ?, ?, ?, ?, ?)", rows)


@pytest.fixture
def con():
    c = duckdb.connect()
    rows, i = [], 0
    for p in range(15):                       # 15 people, week 1: lexicon hit
        rows.append((i := i + 1, f"p{p}", "SD", "brain fog and tired", True, "1", "day 1"))
    for p in range(12):                       # 12 people, week 1: unlabelled, shared phrase
        rows.append((i := i + 1, f"q{p}", "SRO", "weird metallic taste", True, "3", "day 3"))
    for p in range(5):                        # 5 people: unlabelled phrase below the cell size
        rows.append((i := i + 1, f"r{p}", "SRO", "purple toes", True, "7", "day 7"))
    for p in range(12):                       # long-term survey: must never be read pre-registration
        rows.append((i := i + 1, f"s{p}", "SD", "brain fog", True, "180", "6 month"))
    rows.append((i + 1, "t0", "SD", "brain fog", False, None, None))   # unmatched survey
    _entries(c, rows)
    return c


def test_only_week1_and_six_week_classified(con):
    n = themes.build_entry_themes(con)
    assert n == 15 + 12 + 5
    ids = {r[0] for r in con.execute("SELECT entry_id FROM entry_flags").fetchall()}
    long_term = {r[0] for r in con.execute(
        "SELECT entry_id FROM entries_survey WHERE survey_type = '6 month' OR NOT survey_matched"
    ).fetchall()}
    assert not ids & long_term


def test_long_term_refused_before_registration(con):
    with pytest.raises(PermissionError):
        themes.build_entry_themes(con, long_term=True)


def test_long_term_label_blocked_even_with_short_day(con):
    con.execute("UPDATE entries_survey SET survey_day = '1' WHERE survey_type = '6 month'")
    themes.build_entry_themes(con)
    assert con.execute("""SELECT count(*) FROM entry_flags f JOIN entries_survey e USING (entry_id)
                          WHERE e.survey_type = '6 month'""").fetchall()[0][0] == 0


def test_entry_themes_shape_and_coverage(con):
    themes.build_entry_themes(con)
    cols = [r[0] for r in con.execute("DESCRIBE entry_themes").fetchall()]
    assert cols == ["entry_id", "theme", "confidence", "layer", "method"]
    cov = themes.lexicon_coverage(con)
    row = cov.filter(cov["field"] == "SD").row(0, named=True)
    assert row["share_themed"] == 1.0 and not row["suppressed"]
    assert cov.filter(cov["field"] == "SRO")["share_themed"][0] is None   # 0 themed people < 10


def test_candidate_ngrams_respect_cell_size(con):
    themes.build_entry_themes(con)
    ng = explore.candidate_ngrams(con)
    grams = set(ng["ngram"])
    assert "weird metallic taste" in grams and "metallic" in grams
    assert not {"purple", "purple toes", "toes"} & grams        # only 5 people
    assert not grams & {"brain fog", "fog"}                       # labelled entries excluded
    assert (ng["people"] >= 10).all()
