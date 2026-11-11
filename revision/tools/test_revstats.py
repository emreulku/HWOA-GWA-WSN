"""Regression tests for revstats (protocol v0.7). Every test stops on failure."""
import sys
import numpy as np
from fractions import Fraction as Fr
from scipy import stats
sys.path.insert(0, sys.argv[1]); import revstats as R
rng = np.random.default_rng(1)


def grid_check(d, deltas):
    """Direct test vs confidence-set membership at every delta (exact)."""
    cs = R.confidence_set(d)
    mc = None
    if len(d) > R.EXACT_MAX_K:
        mc = np.random.default_rng(R.SEED).choice((-1.0, 1.0), size=(R.B_MC, len(d)))
    bad = [x for x in deltas if (R.shift_p(d, x, mc)[0] >= 0.05) != R.in_set(x, cs)]
    return cs, bad


# 1) no ties / zeros: exact p == SciPy exact
mx = max(abs(R.signflip_p(d)[0] - stats.wilcoxon(d, method="exact").pvalue)
         for d in (rng.normal(0.4, 1, 10) for _ in range(200)))
assert mx == 0, mx; print("1 SciPy exact agreement: max diff", mx)

# 2) all zero: p = 1, HL = 0, family size unaffected (Holm keeps 4 entries)
s = R.summarize(np.zeros(10)); assert s["p"] == 1.0 and s["all_zero"] and s["HL"] == 0
assert len(R.holm([1.0, 0.01, 0.2, 0.03])) == 4; print("2 all-zero OK:", s["ci"])

# 3) minimum p values
assert R.signflip_p(np.arange(1, 11))[0] == 2 / 1024
assert R.signflip_p(np.r_[0, 0, np.arange(1, 9)])[0] == 2 / 256; print("3 p_min OK")

# 4) half-integer data with ties and zeros: grid incl. all breakpoints and many off-breakpoint points
d = np.array([2, 1.5, 0, 3, -0.5, 1, 2.5, 0, 1, 4])
W = sorted({(Fr(d[i]) + Fr(d[j])) / 2 for i in range(10) for j in range(i, 10)})
deltas = list(W) + [w + Fr(1, 10**k) for w in W for k in (3, 9, 12)] + [w - Fr(1, 10**k) for w in W for k in (3, 9, 12)] \
         + list(np.linspace(-3, 6, 2001))
cs, bad = grid_check(d, deltas); assert not bad, bad[:5]
print("4 half-integer data: membership == test at", len(deltas), "deltas;", cs)

# 5) k <= 15 inside n > 15 must be exact (also on the confidence-set path)
d = np.r_[np.zeros(22), np.arange(1, 9)]
mc = np.random.default_rng(R.SEED).choice((-1.0, 1.0), size=(R.B_MC, len(d)))
assert R.shift_p(d, 0)[:3] == R.shift_p(d, 0, mc)[:3] == (2 / 256, 8, "exact")
print("5 exact path inside n=30 OK")

# 6) all = 1/3 (non-representable): true shift in set, p = 1 there
d = np.full(10, 1 / 3); cs = R.confidence_set(d)
assert R.shift_p(d, 1 / 3)[0] == 1.0 and R.in_set(1 / 3, cs); print("6 1/3 OK:", [(float(i['lo']), float(i['hi'])) for i in cs])

# 7) reviewer case: all = 1. Points arbitrarily close to 1 must agree with the test,
#    and the practical rule must follow from that consistent set.
d = np.ones(10)
near = [1, 0.9999999995, 1.0000000005, 1 - 1e-12, 1 + 1e-12, 1 - 1e-15, np.nextafter(1, 0), np.nextafter(1, 2)]
cs, bad = grid_check(d, near); assert not bad, bad
print("7 all-ones:", [(float(i['lo']), float(i['hi'])) for i in cs],
      "| p(0.9999999995) =", R.shift_p(d, 0.9999999995)[0], "| rule:", R.practical(R.summarize(d)["ci"], 1))

# 8) decision-boundary sweep: data built around +-1 target; test points straddling +-1
for trial in range(40):
    base = rng.integers(-4, 5, 10) / 2.0 + rng.choice([0, 1e-10, -1e-10, 1 / 3])
    pts = [s * 1 + o for s in (1, -1) for o in (0, 1e-9, -1e-9, 1e-12, -1e-12, np.nextafter(0, 1))]
    pts += list(np.unique([(base[i] + base[j]) / 2 for i in range(10) for j in range(i, 10)]))
    cs, bad = grid_check(base, pts); assert not bad, (trial, bad[:3])
print("8 decision-boundary sweep: 40 data sets, membership == test everywhere")

# 9) continuous SD-difference-like data incl. n=30 Monte Carlo path
for n in (10, 30):
    d = rng.normal(0.3, 0.7, n) / 3
    W = np.unique([(d[i] + d[j]) / 2 for i in range(n) for j in range(i, n)])
    pts = list(W[:: max(1, len(W) // 60)]) + list(np.linspace(d.min() - 1, d.max() + 1, 301))
    cs, bad = grid_check(d, pts); assert not bad, bad[:3]
    s = R.summarize(d); assert R.in_set(s["HL"], s["conf_set"]), (s["HL"], s["ci"])
    print(f"9 continuous n={n}: method={s['method']}, membership == test at {len(pts)} deltas")

# 10) non-empty sets for 200 thirds/sevenths cases
for _ in range(200):
    base = rng.integers(-5, 6, 10) / 3 + rng.integers(-3, 4) / 7
    assert R.confidence_set(base)
print("10 non-empty sets: OK")

# 11) coverage (conservative with ties) and practical rule
hits = sum(R.in_set(1.0, R.confidence_set(np.round(rng.normal(1.0, 2, 10) * 2) / 2)) for _ in range(300))
assert hits / 300 >= 0.93, hits
I = lambda lo, hi, lc=True, hc=True: dict(lo=Fr(lo), hi=Fr(hi), lo_closed=lc, hi_closed=hc)
assert R.practical(I(1, 3), 1) == "pratikte anlamli"
assert R.practical(I(-1, 0.5, lc=False), 1) == "pratikte ihmal edilebilir"
assert R.practical(I(-1, 0.5), 1) == "belirsiz"
assert R.practical(dict(lo=-float("inf"), hi=Fr(2), lo_closed=False, hi_closed=True), 1) == "belirsiz"
print("11 coverage", hits / 300, "and practical rule OK")
print("ALL TESTS PASSED")
