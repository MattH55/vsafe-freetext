"""Confirmatory statistics fixed before registration (synthetic data only until then).

Q1 coherence: do PACVS domains co-occur in the same people beyond chance? The null keeps
each domain's marginal frequency exactly: every permutation shuffles each domain column
independently across people, which destroys any person-level dependence between domains
and nothing else.

Attrition: prevalence among long-term responders, bounded by assuming every non-responder
is well (lower) or unwell (upper).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class CooccurrenceResult:
    domains: list[str]
    observed_pairs: int               # PRIMARY: sum over domain pairs of people having both
    observed_multi: int               # secondary, descriptive: people with >= 2 domains
    null_mean_pairs: float
    null_mean_multi: float
    p_pairs: float                    # one-sided, (1 + #null >= obs) / (1 + B)
    p_multi: float
    pair_observed: np.ndarray = field(repr=False)   # k x k co-occurrence counts
    pair_p: np.ndarray = field(repr=False)          # k x k one-sided permutation p-values
    permutations: int = 0
    seed: int | None = None


def _pairs(X: np.ndarray) -> np.ndarray:
    Xi = X.astype(np.int64)
    return Xi.T @ Xi


def cooccurrence_test(X, domains: list[str] | None = None, permutations: int = 1000,
                      seed: int | None = None) -> CooccurrenceResult:
    """Permutation test of domain co-occurrence against a marginal-preserving null.

    X: people x domains boolean matrix (one row per person with any long-term data).

    The primary statistic is the total pairwise co-occurrence (`p_pairs`, and `pair_p` per
    pair). `p_multi` (people with >= 2 domains) is descriptive only: when domains cluster in
    few people, those people carry many domains each, so the count of multi-domain people
    can fall below the null even though co-occurrence is far above it.
    """
    X = np.asarray(X, dtype=bool)
    k = X.shape[1]
    domains = domains or [f"d{j}" for j in range(k)]
    iu = np.triu_indices(k, 1)
    obs_c = _pairs(X)
    obs_pairs = int(obs_c[iu].sum())
    obs_multi = int((X.sum(1) >= 2).sum())

    rng = np.random.default_rng(seed)
    ge_pairs = ge_multi = 0
    ge_pair = np.zeros((k, k), dtype=np.int64)
    sum_pairs = sum_multi = 0.0
    for _ in range(permutations):
        P = rng.permuted(X, axis=0)          # each column shuffled independently
        c = _pairs(P)
        sp, sm = int(c[iu].sum()), int((P.sum(1) >= 2).sum())
        ge_pairs += sp >= obs_pairs
        ge_multi += sm >= obs_multi
        ge_pair += c >= obs_c
        sum_pairs += sp
        sum_multi += sm
    B = permutations
    return CooccurrenceResult(
        domains=list(domains), observed_pairs=obs_pairs, observed_multi=obs_multi,
        null_mean_pairs=sum_pairs / B if B else float("nan"),
        null_mean_multi=sum_multi / B if B else float("nan"),
        p_pairs=(1 + ge_pairs) / (1 + B), p_multi=(1 + ge_multi) / (1 + B),
        pair_observed=obs_c, pair_p=(1 + ge_pair) / (1 + B), permutations=B, seed=seed,
    )


@dataclass(frozen=True)
class AttritionBounds:
    observed: float        # cases / responders
    lower: float           # all non-responders well
    upper: float           # all non-responders unwell (counted as cases)


def attrition_bounds(cases: int, responders: int, non_responders: int) -> AttritionBounds:
    if cases < 0 or responders <= 0 or non_responders < 0 or cases > responders:
        raise ValueError("need 0 <= cases <= responders, responders > 0, non_responders >= 0")
    eligible = responders + non_responders
    return AttritionBounds(
        observed=cases / responders,
        lower=cases / eligible,
        upper=(cases + non_responders) / eligible,
    )
