"""
revstats: statistics for protocol v0.7 §6.2 / §6.2a.

All comparisons are done in EXACT rational arithmetic (fractions.Fraction)
on the stored double values: no decimal rounding and no tolerance. Hence
zero detection, ties and the location of breakpoints are exact, and
confidence-set membership coincides with the test for every delta.

- Pratt-ranked Wilcoxon signed-rank statistic
- Two-sided sign-flip permutation p: exact enumeration when the number of
  non-zero differences k <= 15, otherwise Monte Carlo, p = (b+1)/(B+1)
- Hodges-Lehmann estimate (exact median of Walsh averages)
- Confidence set by test inversion over all breakpoints (Walsh averages),
  the open gaps between them and the two unbounded ends.
"""
import itertools
from fractions import Fraction
import numpy as np

SEED = 20261110
EXACT_MAX_K = 15
B_MC = 100_000

_EXACT_CACHE = {}


def _F(x):
    return x if isinstance(x, Fraction) else Fraction(float(x))


def _exact_signs(k):
    if k not in _EXACT_CACHE:
        _EXACT_CACHE[k] = np.array(list(itertools.product((-1.0, 1.0), repeat=k)))
    return _EXACT_CACHE[k]


def _pratt(dev):
    """dev: list of Fractions (d_i - delta). Returns (ranks of non-zero, signs).
    Zeros take part in ranking (Pratt); ties get average ranks; all exact."""
    a = [abs(x) for x in dev]
    order = sorted(range(len(a)), key=lambda i: a[i])
    ranks = [0.0] * len(a)
    pos = 0
    while pos < len(order):
        end = pos
        while end + 1 < len(order) and a[order[end + 1]] == a[order[pos]]:
            end += 1
        avg = (pos + 1 + end + 1) / 2.0                 # half-integers: exact in float
        for q in range(pos, end + 1):
            ranks[order[q]] = avg
        pos = end + 1
    nz = [i for i in range(len(dev)) if dev[i] != 0]
    r = np.array([ranks[i] for i in nz], dtype=float)
    s = np.array([1.0 if dev[i] > 0 else -1.0 for i in nz])
    return r, s


def shift_p(d, delta=0, mc_signs=None):
    """Two-sided sign-flip p for H0: shift = delta, computed exactly on d - delta.
    Returns (p, k, method). Method chosen from k of THIS shifted vector."""
    D = [_F(x) for x in d]
    dl = _F(delta)
    r, s = _pratt([x - dl for x in D])
    k = len(r)
    if k == 0:
        return 1.0, 0, "all_zero"
    t_obs = abs(float((r * s).sum()))                  # sums of half-integers: exact
    if k <= EXACT_MAX_K:
        signs = _exact_signs(k)
        b = int((np.abs(signs @ r) >= t_obs).sum())
        return b / signs.shape[0], k, "exact"
    if mc_signs is None:
        mc_signs = np.random.default_rng(SEED).choice((-1.0, 1.0), size=(B_MC, k))
    assert mc_signs.shape[1] >= k
    b = int((np.abs(mc_signs[:, :k] @ r) >= t_obs).sum())
    return (b + 1) / (mc_signs.shape[0] + 1), k, "monte_carlo"


def signflip_p(d, mc_signs=None):
    return shift_p(d, 0, mc_signs)


def _walsh(D):
    n = len(D)
    return [(D[i] + D[j]) / 2 for i in range(n) for j in range(i, n)]


def hodges_lehmann(d):
    W = sorted(_walsh([_F(x) for x in d]))
    m = len(W)
    med = W[m // 2] if m % 2 else (W[m // 2 - 1] + W[m // 2]) / 2
    return float(med)


def rank_biserial(d):
    r, s = _pratt([_F(x) for x in d])
    tot = r.sum()
    return 0.0 if tot == 0 else float((r * s).sum() / tot)


def confidence_set(d, alpha=0.05):
    """Exact test-inversion confidence set.

    Returns a list of intervals dict(lo, hi, lo_closed, hi_closed) with
    Fraction bounds (or -inf/+inf floats for unbounded ends).
    """
    D = [_F(x) for x in d]
    W = sorted(set(_walsh(D)))
    mc = None
    if len(D) > EXACT_MAX_K:
        mc = np.random.default_rng(SEED).choice((-1.0, 1.0), size=(B_MC, len(D)))

    def accept(delta):
        return shift_p(D, delta, mc)[0] >= alpha

    INF = float("inf")
    pieces = [("open", -INF, W[0], W[0] - 1)]
    for a in range(len(W)):
        pieces.append(("point", W[a], W[a], W[a]))
        if a + 1 < len(W):
            pieces.append(("open", W[a], W[a + 1], (W[a] + W[a + 1]) / 2))
        else:
            pieces.append(("open", W[a], INF, W[a] + 1))

    out, cur = [], None
    for kind, lo, hi, rep in pieces:
        if accept(rep):
            if cur is None:
                cur = dict(lo=lo, lo_closed=(kind == "point"), hi=hi, hi_closed=(kind == "point"))
            else:
                cur["hi"], cur["hi_closed"] = hi, (kind == "point")
        elif cur is not None:
            out.append(cur); cur = None
    if cur is not None:
        out.append(cur)
    return out


def in_set(delta, cs):
    x = _F(delta)
    for iv in cs:
        lo_ok = (iv["lo"] == -float("inf")) or x > iv["lo"] or (x == iv["lo"] and iv["lo_closed"])
        hi_ok = (iv["hi"] == float("inf")) or x < iv["hi"] or (x == iv["hi"] and iv["hi_closed"])
        if lo_ok and hi_ok:
            return True
    return False


def summarize(d, alpha=0.05):
    p, k, method = signflip_p(d)
    cs = confidence_set(d, alpha)
    ci = None
    if cs:
        ci = dict(lo=cs[0]["lo"], lo_closed=cs[0]["lo_closed"], hi=cs[-1]["hi"],
                  hi_closed=cs[-1]["hi_closed"], connected=len(cs) == 1)
    return dict(n=len(d), k_nonzero=k, p=p, method=method, all_zero=bool(k == 0),
                HL=hodges_lehmann(d), r_rb=rank_biserial(d), conf_set=cs, ci=ci)


def practical(ci, e):
    """Protocol §6.3 rule on the reported interval, evaluated exactly."""
    INF = float("inf")
    if ci is None or ci["lo"] == -INF or ci["hi"] == INF:
        return "belirsiz"
    E = _F(e); lo, hi = ci["lo"], ci["hi"]
    if lo >= E or hi <= -E:                         # inside (-inf,-e] U [e, inf)
        return "pratikte anlamli"
    lo_in = lo > -E or (lo == -E and not ci["lo_closed"])
    hi_in = hi < E or (hi == E and not ci["hi_closed"])
    if lo_in and hi_in:                             # inside open (-e, e)
        return "pratikte ihmal edilebilir"
    return "belirsiz"


def holm(pvals):
    p = np.asarray(pvals, float); m = len(p)
    order = np.argsort(p); adj = np.empty(m); run = 0.0
    for rank, idx in enumerate(order):
        run = max(run, min(1.0, (m - rank) * p[idx])); adj[idx] = run
    return adj
