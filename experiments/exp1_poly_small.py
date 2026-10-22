"""Experiment 1: exact C_min in a decidable fragment.

Language P over alphabet Sigma = {x,1,2,+,-,*,(,)}, |Sigma| = 8.
Grammar (unambiguous, usual precedence, left associative):
    S -> S + T | S - T | T
    T -> T * A | A
    A -> x | N | ( S )
    N -> D | N D,   D in {1,2}
Semantics: integer polynomial in x, canonical form = coefficient tuple.
Equivalence is decidable (polynomial identity), so C_min is computable here.

We run the semantic dynamic program (Algorithm 2 in the paper): for every
nonterminal X and length n we keep the SET of meanings of X-strings of
length n, plus one witness string per meaning. Because the semantics is
compositional this is exact.
"""
import json, sys, time
from math import log2

MAXN = 11


def trim(p):
    p = list(p)
    while len(p) > 1 and p[-1] == 0:
        p.pop()
    return tuple(p)


def add(p, q, s=1):
    n = max(len(p), len(q))
    r = [0] * n
    for i, c in enumerate(p):
        r[i] += c
    for i, c in enumerate(q):
        r[i] += s * c
    return trim(r)


def mul(p, q):
    r = [0] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        if a:
            for j, b in enumerate(q):
                r[i + j] += a * b
    return trim(r)


# counts of syntactically valid strings (exact, via DP; no enumeration)
cS, cT, cA = [0] * (MAXN + 1), [0] * (MAXN + 1), [0] * (MAXN + 1)
# semantic tables: dict meaning -> witness string
S = [dict() for _ in range(MAXN + 1)]
T = [dict() for _ in range(MAXN + 1)]
A = [dict() for _ in range(MAXN + 1)]

first = {}  # meaning -> (C_min, witness)
rows = []
t0 = time.time()
for n in range(1, MAXN + 1):
    # A
    cA[n] = (1 if n == 1 else 0) + 2 ** n + (cS[n - 2] if n >= 3 else 0)
    if n == 1:
        A[n][(0, 1)] = "x"
    from itertools import product
    for digs in product("12", repeat=n):
        s = "".join(digs)
        A[n].setdefault((int(s),), s)
    if n >= 3:
        for m, w in S[n - 2].items():
            A[n].setdefault(m, "(" + w + ")")
    # T
    cT[n] = cA[n] + sum(cT[i] * cA[n - 1 - i] for i in range(1, n - 1))
    T[n] = dict(A[n])
    for i in range(1, n - 1):
        j = n - 1 - i
        for m1, w1 in T[i].items():
            for m2, w2 in A[j].items():
                m = mul(m1, m2)
                if m not in T[n]:
                    T[n][m] = w1 + "*" + w2
    # S
    cS[n] = cT[n] + sum(2 * cS[i] * cT[n - 1 - i] for i in range(1, n - 1))
    S[n] = dict(T[n])
    for i in range(1, n - 1):
        j = n - 1 - i
        for m1, w1 in S[i].items():
            for m2, w2 in T[j].items():
                m = add(m1, m2)
                if m not in S[n]:
                    S[n][m] = w1 + "+" + w2
                m = add(m1, m2, -1)
                if m not in S[n]:
                    S[n][m] = w1 + "-" + w2
    new = 0
    for m, w in S[n].items():
        if m not in first:
            first[m] = (n, w)
            new += 1
    rows.append(dict(n=n, all_strings=8 ** n, valid=cS[n], distinct_len_n=len(S[n]),
                     new=new, cum=len(first), secs=round(time.time() - t0, 2)))
    pass


def show(m):
    terms = []
    for k, c in enumerate(m):
        if c:
            terms.append(f"{c}x^{k}")
    return " + ".join(terms) or "0"


examples = {
    "x^2+2x+1": (1, 2, 1), "x^2-1": (-1, 0, 1), "x^3": (0, 0, 0, 1),
    "x^4": (0, 0, 0, 0, 1), "2x^2+2x": (0, 2, 2), "x^2+x+1": (1, 1, 1),
    "0": (0,), "100": (100,), "x^2+4x+4": (4, 4, 1), "5x": (0, 5), "3": (3,),
    "x^3-x": (0, -1, 0, 1), "x^4+1": (1, 0, 0, 0, 1),
}
ex = {k: first.get(v) for k, v in examples.items()}
for k, v in ex.items():
    pass

