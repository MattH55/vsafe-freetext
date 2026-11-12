import numpy as np
import pytest

from vsafe_ft.stats import attrition_bounds, cooccurrence_test


def test_independent_domains_null_wins():
    rng = np.random.default_rng(1)
    X = rng.random((3000, 6)) < [0.05, 0.1, 0.15, 0.08, 0.2, 0.12]   # independent columns
    r = cooccurrence_test(X, permutations=500, seed=7)
    assert r.p_pairs > 0.05 and r.p_multi > 0.05
    assert r.null_mean_pairs == pytest.approx(r.observed_pairs, rel=0.1)


def test_clustered_domains_detected():
    rng = np.random.default_rng(2)
    n = 3000
    latent = rng.random(n) < 0.05                                    # a shared syndrome
    X = (rng.random((n, 6)) < 0.05) | (latent[:, None] & (rng.random((n, 6)) < 0.7))
    r = cooccurrence_test(X, permutations=300, seed=3)
    assert r.p_pairs < 0.01
    assert r.pair_p[0, 1] < 0.01
    assert r.observed_pairs > 1.2 * r.null_mean_pairs


def test_null_preserves_marginals_and_is_seedable():
    X = np.random.default_rng(0).random((200, 4)) < 0.3
    a = cooccurrence_test(X, permutations=50, seed=11)
    b = cooccurrence_test(X, permutations=50, seed=11)
    assert a.p_pairs == b.p_pairs and np.array_equal(a.pair_p, b.pair_p)
    assert np.array_equal(np.diag(a.pair_observed), X.sum(0))      # marginals = diagonal


def test_fast_null_matches_full_permutation_null():
    """The position-sampling null equals shuffling each column: same expected pair counts
    (m_j m_k / n) and the same observed matrix as X.T @ X."""
    rng = np.random.default_rng(5)
    X = rng.random((5000, 4)) < [0.1, 0.2, 0.3, 0.05]
    r = cooccurrence_test(X, permutations=400, seed=9)
    m, n = X.sum(0), X.shape[0]
    expected = sum(m[i] * m[j] / n for i in range(4) for j in range(i + 1, 4))
    assert r.null_mean_pairs == pytest.approx(expected, rel=0.01)
    Xi = X.astype(np.int64)
    assert np.array_equal(r.pair_observed, Xi.T @ Xi)


def test_stratified_null_absorbs_verbosity():
    """Two strata with different rates, independent within each: the plain null calls it
    clustering, the stratum-matched null does not, and its mean is the within-stratum sum."""
    rng = np.random.default_rng(8)
    n = 6000
    verbose = np.arange(n) < n // 2
    X = rng.random((n, 3)) < np.where(verbose, 0.4, 0.02)[:, None]
    plain = cooccurrence_test(X, permutations=200, seed=1)
    matched = cooccurrence_test(X, permutations=200, seed=1, strata=verbose.astype(int))
    assert plain.p_pairs < 0.01
    assert matched.p_pairs > 0.05
    a, b = X[verbose].sum(0), X[~verbose].sum(0)
    expected = sum(a[i] * a[j] / (n // 2) + b[i] * b[j] / (n - n // 2)
                   for i in range(3) for j in range(i + 1, 3))
    assert matched.null_mean_pairs == pytest.approx(expected, rel=0.02)
    assert np.array_equal(np.diag(matched.pair_observed), X.sum(0))


def test_attrition_bounds():
    b = attrition_bounds(cases=50, responders=1000, non_responders=500)
    assert b.observed == pytest.approx(0.05)
    assert b.lower == pytest.approx(50 / 1500)
    assert b.upper == pytest.approx(550 / 1500)
    with pytest.raises(ValueError):
        attrition_bounds(5, 0, 1)


def test_holm():
    from vsafe_ft.stats import holm

    assert holm([0.01, 0.04, 0.03]).tolist() == pytest.approx([0.03, 0.06, 0.06])


def test_onset_exact_and_null():
    from vsafe_ft.stats import onset_test

    r = onset_test([True, True], [0.5, 0.5])
    assert r.p == pytest.approx(0.25) and r.expected == 1.0
    rng = np.random.default_rng(1)
    p0 = rng.uniform(0.2, 0.6, 500)
    null = onset_test(rng.random(500) < p0, p0)          # data from the null
    assert null.p > 0.01
    alt = onset_test(rng.random(500) < np.minimum(p0 + 0.3, 1), p0)
    assert alt.p < 1e-6


def test_risk_difference_newcombe():
    from vsafe_ft.stats import risk_difference

    r = risk_difference(56, 70, 48, 80)      # Newcombe (1998) example: 0.2 (0.0524, 0.3339)
    assert r.diff == pytest.approx(0.2)
    assert (r.lower, r.upper) == pytest.approx((0.0524, 0.3339), abs=1e-3)
    assert r.p_one_sided < 0.01
    assert risk_difference(10, 100, 10, 100).p_one_sided == pytest.approx(0.5)


def test_risk_ratio():
    from vsafe_ft.stats import risk_ratio

    r = risk_ratio(20, 1000, 60, 1000)
    assert r.ratio == pytest.approx(1 / 3) and r.lower_capture
    assert not risk_ratio(50, 1000, 50, 1000).lower_capture
    assert risk_ratio(0, 100, 5, 100).ratio < 1               # zero cell corrected


def test_dispersion():
    from vsafe_ft.stats import dispersion_test, entropy

    assert entropy(["a", "a", "b", "b"]) == pytest.approx(1.0)
    rng = np.random.default_rng(2)
    wide = rng.integers(0, 40, 400).astype(str)
    narrow = rng.integers(0, 4, 400).astype(str)
    assert dispersion_test(wide, narrow, 200, seed=1).p < 0.01
    same = dispersion_test(rng.integers(0, 10, 300).astype(str),
                           rng.integers(0, 10, 300).astype(str), 200, seed=1)
    assert same.p > 0.01
