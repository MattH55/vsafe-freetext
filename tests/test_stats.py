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


def test_attrition_bounds():
    b = attrition_bounds(cases=50, responders=1000, non_responders=500)
    assert b.observed == pytest.approx(0.05)
    assert b.lower == pytest.approx(50 / 1500)
    assert b.upper == pytest.approx(550 / 1500)
    with pytest.raises(ValueError):
        attrition_bounds(5, 0, 1)
