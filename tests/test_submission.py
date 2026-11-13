"""Curveball null and extended dispersion (submission addendum 2), on synthetic data."""

import numpy as np
import pytest

from vsafe_ft import stats


def test_curveball_keeps_both_margins_and_total_pairs():
    rng = np.random.default_rng(3)
    X = rng.random((4000, 5)) < [0.3, 0.2, 0.1, 0.4, 0.05]
    r = stats.curveball_test(X, permutations=50, seed=1, burn_in=5, thin=2)
    # diagonal of the null-mean pair matrix = column sums (unchanged), total pairs invariant
    assert np.allclose(np.diag(r.pair_null_mean), X.sum(0))
    assert r.null_mean_pairs == pytest.approx(r.observed_pairs, rel=1e-9)
    assert r.pair_p_upper.shape == (5, 5) and (r.pair_p_upper <= 1).all()


def test_curveball_round_preserves_row_and_column_sums():
    rng = np.random.default_rng(4)
    k = 6
    weights = (1 << np.arange(k)).astype(np.uint16)
    X = rng.random((3000, k)) < 0.35
    code = (X.astype(np.uint16) * weights).sum(1, dtype=np.uint16)
    pop = np.array([c.bit_count() for c in range(1 << k)])
    trade = (pop[code] >= 1) & (pop[code] <= k - 1)
    rows = code[trade].copy()
    before_rows = pop[rows].copy()
    before_cols = ((rows[:, None] >> np.arange(k)) & 1).sum(0)
    for _ in range(10):
        stats._curveball_round(rows, k, weights, rng)
    assert np.array_equal(pop[rows], before_rows)
    assert np.array_equal(((rows[:, None] >> np.arange(k)) & 1).sum(0), before_cols)
    assert not np.array_equal(rows, code[trade])          # something actually moved


def test_curveball_detects_pair_structure_beyond_margins():
    rng = np.random.default_rng(5)
    n = 6000
    base = rng.random((n, 4)) < 0.2
    link = rng.random(n) < 0.15                            # domains 0 and 1 travel together
    base[link, 0] = True
    base[link, 1] = True
    r = stats.curveball_test(base, permutations=200, seed=2, burn_in=10, thin=2)
    assert r.pair_p_upper[0, 1] < 0.01
    assert r.pair_observed[0, 1] > 1.3 * r.pair_null_mean[0, 1]


def test_dispersion_extended_fields():
    rng = np.random.default_rng(6)
    a = rng.integers(0, 50, 800)
    b = rng.integers(0, 30, 1200)
    r = stats.dispersion_extended(a, b, permutations=100, seed=1, rarefactions=20)
    assert r["h_a_mm"] >= r["h_a"] and r["h_b_mm"] >= r["h_b"]
    assert r["rare_n"] == 800
    assert 0 < r["p_two"] <= 1 and 0 < r["p_upper"] <= 1
    assert r["h_a"] > r["h_b"]


def test_core_subgraph_sums_core_and_other_pairs():
    import polars as pl

    from vsafe_ft import submission

    doms = ["cognitive", "fatigue_pem", "sleep", "dysautonomia", "pain"]
    rows = []
    for i, a in enumerate(doms):
        for b in doms[i + 1:]:
            rows.append({"null": "x", "domain_a": a, "domain_b": b, "both_people": 100, "expected_people": 50.0})
    out = submission.core_subgraph(pl.DataFrame(rows))
    core = out.filter(pl.col("subgraph") == "core (6 pairs)").row(0, named=True)
    other = out.filter(pl.col("subgraph") == "other pairs").row(0, named=True)
    assert core["pairs"] == 6 and core["observed_people"] == 600 and core["ratio"] == 2.0
    assert other["pairs"] == 4 and other["observed_people"] == 400
    assert "suppressed" in out.columns and not out["suppressed"].any()


def test_q1_by_sex_runs_on_synthetic_matrix(tmp_path):
    import polars as pl

    from vsafe_ft import submission

    rng = np.random.default_rng(7)
    doms = ["cognitive", "fatigue_pem", "sleep", "dysautonomia"]
    n = 3000
    X = rng.random((n, 4)) < 0.3
    df = pl.DataFrame({d: X[:, i] for i, d in enumerate(doms)}).with_columns(
        pl.Series("sex", rng.choice(["Female", "Male", "Unknown"], n, p=[0.6, 0.35, 0.05])),
        pl.Series("dose", rng.choice(["1", "2"], n)),
        pl.Series("n_entries", rng.integers(1, 5, n)),
        pl.Series("chars", rng.integers(10, 500, n)))
    p = tmp_path / "m.parquet"
    df.write_parquet(p)
    out = submission.q1_by_sex(doms, permutations=20, path=p, log=lambda m: None, curveball=False)
    s = out["summary"]
    assert set(s["sex"].unique()) == {"Female", "Male"}
    assert {"registered", "matched: entries x character deciles"} <= set(s["null"].unique())
    assert out["pairs"].height == 2 * 2 * 6
    assert not any("sex" in c and c != "sex" for c in s.columns)
