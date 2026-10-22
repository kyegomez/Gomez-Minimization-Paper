"""Witness strings for selected integer constants (constant sub-language, <= 13 chars)."""
from itertools import product
MAXN=13
S=[dict() for _ in range(MAXN+1)];T=[dict() for _ in range(MAXN+1)];A=[dict() for _ in range(MAXN+1)]
best={}
for n in range(1,MAXN+1):
    for d in product("12",repeat=n):
        s="".join(d); A[n].setdefault(int(s),s)
    if n>=3:
        for v,w in S[n-2].items(): A[n].setdefault(v,"("+w+")")
    T[n]=dict(A[n])
    for i in range(1,n-1):
        for a,wa in T[i].items():
            for b,wb in A[n-1-i].items(): T[n].setdefault(a*b,wa+"*"+wb)
    S[n]=dict(T[n])
    for i in range(1,n-1):
        for a,wa in S[i].items():
            for b,wb in T[n-1-i].items():
                S[n].setdefault(a+b,wa+"+"+wb); S[n].setdefault(a-b,wa+"-"+wb)
    for v,w in S[n].items(): best.setdefault(v,(n,w))
for N in [0,3,5,7,10,11,100,121,200,222,359,369,400]: print(N,best[N])
