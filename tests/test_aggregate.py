import duckdb
import pytest

from vsafe_ft import aggregate


@pytest.mark.parametrize("days,label", [(0, "0"), (1, "1-7"), (7, "1-7"), (8, "8-42"),
                                        (42, "8-42"), (43, "43-120"), (121, "121-240"),
                                        (400, "241-400"), (401, None), (-3, None), (None, None)])
def test_days_bins(days, label):
    assert aggregate.days_bin(days) == label
    sql = duckdb.connect().execute(
        f"SELECT {aggregate.days_bin_sql('d')} FROM (SELECT {days if days is not None else 'NULL'}::INT AS d)"
    ).fetchall()[0][0]
    assert sql == label


@pytest.fixture
def con():
    c = duckdb.connect()
    c.execute("CREATE TABLE vax AS SELECT 'p' || i AS registrant, DATE '2021-03-01' AS vax_date "
              "FROM range(30) t(i)")
    # 30 people x (1 day-3 check-in, 1 day-100 check-in) + 30 extra day-3 check-ins
    c.execute("""CREATE TABLE checkins AS
        SELECT 'c' || i AS survey_static_id, 'p' || (i % 30) AS registrant,
               CASE WHEN i < 60 THEN 'daily' ELSE '3m' END AS survey_type,
               CASE WHEN i < 60 THEN '3' ELSE '100' END AS survey_day,
               NULL AS medical_care, NULL AS health_impact, NULL AS health_now,
               CASE WHEN i < 60 THEN '2021-03-04' ELSE '2021-06-09' END AS started_on
        FROM range(90) t(i)""")
    c.execute("""CREATE TABLE entry_themes AS
        SELECT i AS entry_id, 'fatigue_pem' AS theme, 1.0 AS confidence, 1 AS layer, 'x' AS method
        FROM range(24) t(i)""")
    c.execute("""CREATE TABLE entries_survey AS
        SELECT i AS entry_id, 'p' || (i % 12) AS registrant, NULL AS medical_care,
               CASE WHEN i < 12 THEN 'daily' ELSE '3m' END AS survey_type,
               CASE WHEN i < 12 THEN 3 ELSE 100 END AS days_since_dose,
               '1' AS dose_number, 'X' AS manufacturer, '30-39' AS age_band
        FROM range(24) t(i)""")
    aggregate.build_checkin_denominators(c)
    aggregate.build_themed(c)
    return c


def test_rates_per_1000_checkins_of_that_type(con):
    df = aggregate.theme_table(con, ["survey_type"])
    got = dict(zip(df["survey_type"], df["per_1000_checkins"]))
    assert got == {"daily": pytest.approx(12 * 1000 / 60), "3m": pytest.approx(12 * 1000 / 30)}
    assert "entries" not in df.columns                 # never raw counts in time tables


def test_rates_per_1000_by_dose_time_bin(con):
    df = aggregate.theme_table(con, ["days_since_dose_bin"])
    got = dict(zip(df["days_since_dose_bin"], df["per_1000_checkins"]))
    assert got == {"1-7": pytest.approx(200.0), "43-120": pytest.approx(400.0)}


def test_write_aggregates_is_safe(con, tmp_path):
    sums = aggregate.write_aggregates(con, tmp_path)
    assert "theme_by_days_since_dose_bin.csv" in sums
    assert (tmp_path / "SHA256SUMS").read_text().count("\n") == len(sums)
