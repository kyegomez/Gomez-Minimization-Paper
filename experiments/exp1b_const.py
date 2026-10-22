"""Experiment 1b: character complexity of integer constants.

Sub-language over {1,2,+,-,*,(,)} (same grammar as Experiment 1 without x).
Computes exact C_min(N) for every integer N reachable with <= MAXN chars,
then reports N in [0, NMAX]. Cross-checks against the full language (with x)
for lengths <= 11, i.e. checks that x never helps to write a constant.
"""
import json, sys
from itertools import product

MAXN = int(sys.argv[1]) if len(sys.argv) > 1 else 14
NMAX = 400

S = [set() for _ in range(MAXN + 1)]
T = [set() for _ in range(MAXN + 1)]
A = [set() for _ in range(MAXN + 1)]
W = {}
best = {}
for n in range(1, MAXN + 1):
    A[n] = {int("".join(d)) for d in product("12", repeat=n)}
    if n >= 3:
        A[n] |= S[n - 2]
    T[n] = set(A[n])
    for i in range(1, n - 1):
        for a in T[i]:
            for b in A[n - 1 - i]:
                T[n].add(a * b)
    S[n] = set(T[n])
    for i in range(1, n - 1):
        for a in S[i]:
            for b in T[n - 1 - i]:
                S[n].add(a + b)
                S[n].add(a - b)
    for v in S[n]:
        best.setdefault(v, n)
    print(n, len(S[n]), len(best), flush=True)

res = {N: best.get(N) for N in range(0, NMAX + 1)}
missing = [N for N, c in res.items() if c is None]
print("missing", missing[:20], len(missing))

# cross check against the full language with x (constants only)
full = json.load(open("exp1_poly.json"))  # only rows there; recompute small DP
import exp1_poly_small as fp  # noqa
bad = [(N, res[N], fp.first[(N,)][0]) for N in range(0, NMAX + 1)
       if (N,) in fp.first and fp.first[(N,)][0] != res[N]]
print("cross-check mismatches (with x vs without x):", bad)
json.dump(dict(cmin={str(k): v for k, v in res.items()}), open("exp1b_const.json", "w"))
