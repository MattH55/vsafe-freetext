"""Confirmatory statistics fixed before registration (synthetic data only until then).

Q1 coherence: do PACVS domains co-occur in the same people beyond chance? The null keeps
each domain's marginal frequency exactly: every permutation shuffles each domain column
independently across people, which destroys any person-level dependence between domains
and nothing else.

Attrition: prevalence among long-term responders, bounded by assuming every non-responder
is well (lower) or unwell (upper).
"""

from __future__ import annotations

import math
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


def _pattern_stats(cnt: np.ndarray, bits: np.ndarray, multi: np.ndarray):
    """Pair matrix and multi-domain count from counts of rows per domain pattern."""
    w = bits * cnt[:, None]
    return bits.T @ w, int(cnt[multi].sum())


def cooccurrence_test(X, domains: list[str] | None = None, permutations: int = 1000,
                      seed: int | None = None, strata=None) -> CooccurrenceResult:
    """Permutation test of domain co-occurrence against a marginal-preserving null.

    X: people x domains boolean matrix (one row per person with any long-term data).

    The primary statistic is the total pairwise co-occurrence (`p_pairs`, and `pair_p` per
    pair). `p_multi` (people with >= 2 domains) is descriptive only: when domains cluster in
    few people, those people carry many domains each, so the count of multi-domain people
    can fall below the null even though co-occurrence is far above it.

    Shuffling a column independently is the same as placing its m_j positives at a uniformly
    random set of m_j rows, so each permutation draws those sets directly and counts rows by
    domain pattern (2^k patterns). Same null as permuting the full matrix, much faster at
    millions of rows (implementation changed 2026-11-12 for speed; the null is unchanged).

    strata: optional per-row integer labels. Each domain's positives are then placed at random
    within each stratum, keeping the domain's frequency per stratum (a null matched on, say,
    how much text each person wrote). Exploratory, not registered.
    """
    X = np.asarray(X, dtype=bool)
    n, k = X.shape
    if k > 16:
        raise ValueError("at most 16 domains")
    domains = domains or [f"d{j}" for j in range(k)]
    iu = np.triu_indices(k, 1)
    pats = np.arange(1 << k)
    bits = ((pats[:, None] >> np.arange(k)) & 1).astype(np.int64)
    multi = bits.sum(1) >= 2
    weights = (1 << np.arange(k)).astype(np.uint16)
    code = (X.astype(np.uint16) * weights).sum(1, dtype=np.uint16)
    obs_c, obs_multi = _pattern_stats(np.bincount(code, minlength=1 << k), bits, multi)
    obs_pairs = int(obs_c[iu].sum())
    if strata is None:
        groups = [(np.arange(n), X.sum(0))]
    else:
        st = np.asarray(strata)
        groups = [(idx, X[idx].sum(0)) for idx in
                  (np.flatnonzero(st == v) for v in np.unique(st))]

    rng = np.random.default_rng(seed)
    ge_pairs = ge_multi = 0
    ge_pair = np.zeros((k, k), dtype=np.int64)
    sum_pairs = sum_multi = 0.0
    buf = np.empty(n, dtype=np.uint16)
    for _ in range(permutations):
        buf[:] = 0
        for idx, m in groups:
            for j in range(k):
                buf[idx[rng.choice(idx.size, size=int(m[j]), replace=False)]] |= weights[j]
        c, sm = _pattern_stats(np.bincount(buf, minlength=1 << k), bits, multi)
        sp = int(c[iu].sum())
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


# --- Q1 secondary: Holm adjustment of the per-pair p-values ---------------------------------

def holm(p) -> np.ndarray:
    """Holm step-down adjusted p-values (same shape as p)."""
    p = np.asarray(p, dtype=float)
    flat = p.ravel()
    order = np.argsort(flat)
    m = flat.size
    adj = np.maximum.accumulate((m - np.arange(m)) * flat[order])
    out = np.empty(m)
    out[order] = np.minimum(adj, 1.0)
    return out.reshape(p.shape)


def _phi(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def _z(level: float) -> float:
    """Two-sided normal quantile for a confidence level, by bisection (no scipy)."""
    target, lo, hi = 1 - (1 - level) / 2, 0.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if _phi(mid) < target else (lo, mid)
    return (lo + hi) / 2


# --- Q2 onset: early onset vs onset spread evenly over the surveys completed ------------------

@dataclass(frozen=True)
class OnsetResult:
    cases: int
    early: int            # cases with onset at week 1 or six weeks
    expected: float       # sum of per-case null probabilities
    p: float              # one-sided P(X >= early) under the Poisson-binomial null


def onset_test(early, p0) -> OnsetResult:
    """Exact one-sided test that onset is concentrated in the first six weeks.

    early: per case, True if the case domains first appear at week 1 or six weeks.
    p0: per case, the null probability of early onset = share of that person's completed
        surveys of the dose that are week-1 / six-week (onset uniform over completed surveys).
    X = sum of independent Bernoulli(p0_i) (Poisson-binomial), computed exactly.
    """
    e = np.asarray(early, dtype=bool)
    q = np.asarray(p0, dtype=float)
    if e.shape != q.shape or ((q < 0) | (q > 1)).any():
        raise ValueError("early and p0 must have the same length; p0 in [0, 1]")
    dist = np.zeros(e.size + 1)
    dist[0] = 1.0
    for pi in q:
        dist[1:] = dist[1:] * (1 - pi) + dist[:-1] * pi
        dist[0] *= 1 - pi
    k = int(e.sum())
    return OnsetResult(cases=int(e.size), early=k, expected=float(q.sum()),
                       p=float(min(1.0, dist[k:].sum())))


# --- Q2 persistence: risk difference, cases vs group (c) --------------------------------------

def _wilson(x: int, n: int, z: float) -> tuple[float, float]:
    p = x / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


@dataclass(frozen=True)
class RiskDifference:
    p1: float
    p2: float
    diff: float
    lower: float          # Newcombe hybrid score interval (method 10)
    upper: float
    p_one_sided: float    # pooled z-test, H1: p1 > p2


def risk_difference(x1: int, n1: int, x2: int, n2: int, level: float = 0.95) -> RiskDifference:
    if not (0 <= x1 <= n1 and 0 <= x2 <= n2 and n1 > 0 and n2 > 0):
        raise ValueError("need 0 <= x <= n and n > 0 for both groups")
    z = _z(level)
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = _wilson(x1, n1, z)
    l2, u2 = _wilson(x2, n2, z)
    d = p1 - p2
    lo = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    pp = (x1 + x2) / (n1 + n2)
    se = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
    pval = 0.5 if se == 0 else 1 - _phi(d / se)
    return RiskDifference(p1, p2, d, lo, hi, pval)


# --- Q3 capture: risk ratio, cases vs group (b) -----------------------------------------------

@dataclass(frozen=True)
class RiskRatio:
    ratio: float
    lower: float
    upper: float
    lower_capture: bool   # H1 (cases captured less often): upper < 1


def risk_ratio(x1: int, n1: int, x2: int, n2: int, level: float = 0.95) -> RiskRatio:
    """Ratio of proportions with a log-scale Wald interval (0.5 added to every cell if a
    count is zero)."""
    if not (0 <= x1 <= n1 and 0 <= x2 <= n2 and n1 > 0 and n2 > 0):
        raise ValueError("need 0 <= x <= n and n > 0 for both groups")
    if 0 in (x1, x2, n1 - x1, n2 - x2):
        x1, x2, n1, n2 = x1 + 0.5, x2 + 0.5, n1 + 1, n2 + 1
    rr = (x1 / n1) / (x2 / n2)
    se = math.sqrt(1 / x1 - 1 / n1 + 1 / x2 - 1 / n2)
    z = _z(level)
    lo, hi = rr * math.exp(-z * se), rr * math.exp(z * se)
    return RiskRatio(rr, lo, hi, hi < 1)


# --- Q3 dispersion: Shannon entropy of MedDRA PTs, permutation test ---------------------------

def entropy(labels) -> float:
    _, c = np.unique(np.asarray(labels), return_counts=True)
    q = c / c.sum()
    return float(-(q * np.log2(q)).sum())


@dataclass(frozen=True)
class DispersionResult:
    entropy_cases: float
    entropy_comparison: float
    diff: float
    p: float              # one-sided, H1: cases' PTs more dispersed
    permutations: int


def dispersion_test(pts_cases, pts_comparison, permutations: int = 1000,
                    seed: int | None = None) -> DispersionResult:
    """PT entropy of cases minus comparison; null shuffles the group label of each PT code."""
    a, b = np.asarray(pts_cases), np.asarray(pts_comparison)
    obs = entropy(a) - entropy(b)
    pool = np.concatenate([a, b])
    rng = np.random.default_rng(seed)
    ge = 0
    for _ in range(permutations):
        s = rng.permutation(pool)
        ge += entropy(s[: a.size]) - entropy(s[a.size:]) >= obs
    return DispersionResult(entropy(a), entropy(b), obs, (1 + ge) / (1 + permutations),
                            permutations)


# --- Curveball null: row and column margins both fixed (not pre-registered) ------------------

@dataclass
class CurveballResult:
    domains: list[str]
    observed_pairs: int
    null_mean_pairs: float            # equals observed_pairs: fixed by the row sums
    pair_observed: np.ndarray = field(repr=False)
    pair_null_mean: np.ndarray = field(repr=False)
    pair_p_upper: np.ndarray = field(repr=False)
    pair_p_lower: np.ndarray = field(repr=False)
    permutations: int = 0
    seed: int | None = None


def _curveball_round(rows: np.ndarray, k: int, weights: np.ndarray, rng) -> None:
    """One round of curveball trades in place: rows are paired at random; each pair keeps its
    shared domains and redistributes the rest at random, each row keeping its count."""
    n = rows.size
    if n < 2:
        return
    perm = rng.permutation(n)
    m = n // 2
    ia, ib = perm[:m], perm[m:2 * m]
    a, b = rows[ia], rows[ib]
    shared = a & b
    u = a ^ b
    bits = np.arange(k)
    ubits = ((u[:, None] >> bits) & 1).astype(bool)
    na = (((a ^ shared)[:, None] >> bits) & 1).sum(1)          # unique bits a must keep
    pr = rng.random((m, k))
    pr[~ubits] = -1.0
    order = np.argsort(-pr, axis=1)
    rank = np.empty_like(order)
    np.put_along_axis(rank, order, np.broadcast_to(bits, (m, k)).copy(), axis=1)
    pick = (rank < na[:, None]) & ubits
    rows[ia] = shared | (pick * weights).sum(1).astype(np.uint16)
    rows[ib] = shared | ((ubits & ~pick) * weights).sum(1).astype(np.uint16)


def curveball_test(X, domains: list[str] | None = None, permutations: int = 1000,
                   seed: int | None = None, strata=None, burn_in: int = 30, thin: int = 3,
                   log=None) -> CurveballResult:
    """Pair co-occurrence against a null that keeps every row's domain count and every domain's
    frequency (curveball trades on the 2^k pattern codes, within strata if given). The total
    pair count is invariant under this null, so only per-pair tests are reported: upper-tail
    (observed >= null) and lower-tail p-values, each (1 + #) / (1 + B)."""
    X = np.asarray(X, dtype=bool)
    n, k = X.shape
    if k > 16:
        raise ValueError("at most 16 domains")
    domains = domains or [f"d{j}" for j in range(k)]
    pats = np.arange(1 << k)
    bits = ((pats[:, None] >> np.arange(k)) & 1).astype(np.int64)
    multi = bits.sum(1) >= 2
    weights = (1 << np.arange(k)).astype(np.uint16)
    code = (X.astype(np.uint16) * weights).sum(1, dtype=np.uint16)
    obs_c, _ = _pattern_stats(np.bincount(code, minlength=1 << k), bits, multi)
    iu = np.triu_indices(k, 1)
    obs_pairs = int(obs_c[iu].sum())
    pop = bits.sum(1)
    trade = (pop[code] >= 1) & (pop[code] <= k - 1)     # rows with 0 or k domains never change
    fixed_counts = np.bincount(code[~trade], minlength=1 << k)
    st = np.zeros(n, dtype=np.int64) if strata is None else np.asarray(strata)
    groups = [code[(st == v) & trade].copy() for v in np.unique(st)]
    rng = np.random.default_rng(seed)
    for _ in range(burn_in):
        for g in groups:
            _curveball_round(g, k, weights, rng)
    ge = np.zeros((k, k), dtype=np.int64)
    le = np.zeros((k, k), dtype=np.int64)
    sum_c = np.zeros((k, k))
    for b in range(permutations):
        for _ in range(thin):
            for g in groups:
                _curveball_round(g, k, weights, rng)
        cnt = fixed_counts.copy()
        for g in groups:
            cnt += np.bincount(g, minlength=1 << k)
        c, _ = _pattern_stats(cnt, bits, multi)
        ge += c >= obs_c
        le += c <= obs_c
        sum_c += c
        if log and (b + 1) % 100 == 0:
            log(f"curveball {b + 1}/{permutations}")
    B = permutations
    null_mean = sum_c / B if B else np.full((k, k), np.nan)
    return CurveballResult(domains=list(domains), observed_pairs=obs_pairs,
                           null_mean_pairs=float(null_mean[iu].sum()), pair_observed=obs_c,
                           pair_null_mean=null_mean, pair_p_upper=(1 + ge) / (1 + B),
                           pair_p_lower=(1 + le) / (1 + B), permutations=B, seed=seed)


# --- Q3 dispersion, extended (not pre-registered) --------------------------------------------

def entropy_miller_madow(labels) -> float:
    _, c = np.unique(np.asarray(labels), return_counts=True)
    n = c.sum()
    return entropy(labels) + (c.size - 1) / (2 * n) / math.log(2)


def dispersion_extended(pts_cases, pts_comparison, permutations: int = 1000,
                        seed: int | None = None, rarefactions: int = 200) -> dict:
    """Raw, Miller-Madow and rarefied (equal code counts) Shannon entropies, with one-sided
    (cases more dispersed) and two-sided permutation p-values on the raw difference."""
    a, b = np.asarray(pts_cases), np.asarray(pts_comparison)
    rng = np.random.default_rng(seed)
    obs = entropy(a) - entropy(b)
    pool = np.concatenate([a, b])
    ge = two = 0
    for _ in range(permutations):
        s = rng.permutation(pool)
        d = entropy(s[: a.size]) - entropy(s[a.size:])
        ge += d >= obs
        two += abs(d) >= abs(obs)
    m = int(min(a.size, b.size))
    ra = np.mean([entropy(rng.choice(a, m, replace=False)) for _ in range(rarefactions)])
    rb = np.mean([entropy(rng.choice(b, m, replace=False)) for _ in range(rarefactions)])
    return {"h_a": entropy(a), "h_b": entropy(b), "h_a_mm": entropy_miller_madow(a),
            "h_b_mm": entropy_miller_madow(b), "h_a_rare": float(ra), "h_b_rare": float(rb),
            "rare_n": m, "diff": obs, "p_upper": (1 + ge) / (1 + permutations),
            "p_two": (1 + two) / (1 + permutations)}
