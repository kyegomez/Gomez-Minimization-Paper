"""Experiment 2 harness: differential-testing oracle, Gomez reducer, line collapse.

Run:  python3 harness.py   -> writes exp2.json
"""
import ast, json, random, resource, signal, sys, warnings, copy, string
from tasks import T

sys.setrecursionlimit(5000)
resource.setrlimit(resource.RLIMIT_AS, (3 << 30, 3 << 30))


class Timeout(Exception):
    pass


def _alarm(*_):
    raise Timeout()


signal.signal(signal.SIGALRM, _alarm)


def chars(p):
    return len(p)


def lines(p):
    return 1 + p.count("\n")


def compiles(p):
    """Valid program = compiles with every warning promoted to an error."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            return compile(p, "<cand>", "exec")
    except Exception:
        return None


def observe(x):
    return (type(x).__name__, repr(x))


def call(fn, args):
    try:
        return observe(fn(*copy.deepcopy(args)))
    except Timeout:
        raise
    except BaseException as e:  # noqa
        return ("EXC", type(e).__name__, repr(e.args))


def load(p, name):
    code = compiles(p)
    if code is None:
        return None
    g = {"__name__": "cand"}
    signal.setitimer(signal.ITIMER_REAL, 1.0)
    try:
        exec(code, g)
    except BaseException:
        return None
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    return g.get(name)


def trace_fn(fn, inputs):
    return [call(fn, a) for a in inputs]


def trace_cls(C, spec, r):
    _, _, ctor, ops, attrs = spec
    out = []
    for _ in range(60):
        args = ctor(r)
        try:
            obj = C(*args)
        except BaseException as e:
            out.append(("EXC", type(e).__name__))
            continue
        for _ in range(r.randint(0, 25)):
            m, ag = r.choice(ops)
            a = ag(r)
            try:
                res = observe(getattr(obj, m)(*a))
            except Timeout:
                raise
            except BaseException as e:
                res = ("EXC", type(e).__name__, repr(e.args))
            out.append((m, a, res) + tuple(observe(getattr(obj, k, None)) for k in attrs))
    return out


class Oracle:
    """E_L(p) ~= f, decided by differential testing on the task domain D."""

    def __init__(self, t, seed=0):
        self.t = t
        self.kind = t["kind"]
        self.name = "f" if self.kind == "fn" else self.kind[1]
        r = random.Random(seed)
        if self.kind == "fn":
            self.inputs = t["gen"](r)
        self.ref = self.run(t["canonical"])
        assert self.ref is not None
        self.calls = 0

    def run(self, p):
        obj = load(p, self.name)
        if obj is None:
            return None
        signal.setitimer(signal.ITIMER_REAL, 2.0)
        try:
            if self.kind == "fn":
                return trace_fn(obj, self.inputs)
            return trace_cls(obj, self.kind, random.Random(1))
        except BaseException:
            return None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def __call__(self, p):
        self.calls += 1
        return self.run(p) == self.ref


# ------------------------------------------------------------- Phase 1 (safe)
def strip_docstrings(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
            b = node.body
            if b and isinstance(b[0], ast.Expr) and isinstance(getattr(b[0], "value", None), ast.Constant) \
                    and isinstance(b[0].value.value, str):
                node.body = b[1:] or [ast.Pass()]
    return tree


def alpha_rename(tree):
    """Consistently rename parameters and locals of every function to fresh 1-letter names.
    Sibling functions reuse the same fresh names; nested functions avoid their ancestors' names."""
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | \
           {n.arg for n in ast.walk(tree) if isinstance(n, ast.arg)} | \
           {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))} | \
           {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    pool = [c for c in string.ascii_letters if c not in used]

    def visit(node, taken):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, ast.FunctionDef):
                local = [a.arg for a in ch.args.args]
                for n in ast.walk(ch):
                    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id not in local:
                        local.append(n.id)
                free = [c for c in pool if c not in taken]
                mapping = {nm: free.pop(0) for nm in local if len(nm) > 1 and free}
                for n in ast.walk(ch):
                    if isinstance(n, ast.Name) and n.id in mapping:
                        n.id = mapping[n.id]
                    if isinstance(n, ast.arg) and n.arg in mapping:
                        n.arg = mapping[n.arg]
                visit(ch, taken | set(mapping.values()))
            else:
                visit(ch, taken)
    visit(tree, set())
    return tree


def same_ast(a, b):
    try:
        return ast.dump(ast.parse(a)) == ast.dump(ast.parse(b))
    except SyntaxError:
        return False


def ast_invariant_squeeze(p):
    """Delete spaces and join lines whenever the AST is unchanged (provably safe)."""
    ref = ast.dump(ast.parse(p))
    ok = lambda q: compiles(q) is not None and ast.dump(ast.parse(q)) == ref
    # 1 space per indentation level
    out = []
    for ln in p.split("\n"):
        k = len(ln) - len(ln.lstrip(" "))
        out.append(" " * (k // 4) + ln.lstrip(" "))
    q = "\n".join(out)
    assert ok(q)
    # delete inner spaces
    i = len(q) - 1
    while i >= 0:
        if q[i] == " " and i > 0 and q[i - 1] != "\n" and q[i - 1] != " ":
            c = q[:i] + q[i + 1:]
            if ok(c):
                q = c
        i -= 1
    # delete redundant parenthesis pairs
    i = len(q) - 1
    while i >= 0:
        if q[i] == "(":
            for j in range(i + 1, len(q)):
                if q[j] == ")":
                    c = q[:i] + q[i + 1:j] + q[j + 1:]
                    if ok(c):
                        q = c
                        break
        i -= 1
    # delete spaces again (paren removal can expose new ones)
    i = len(q) - 1
    while i >= 0:
        if q[i] == " " and i > 0 and q[i - 1] != "\n" and q[i - 1] != " ":
            c = q[:i] + q[i + 1:]
            if ok(c):
                q = c
        i -= 1
    # join lines: "\n<indent>" -> ";" or "" (suite onto its header)
    changed = True
    while changed:
        changed = False
        i = q.rfind("\n")
        while i >= 0:
            j = i + 1
            while j < len(q) and q[j] == " ":
                j += 1
            for rep in ("", ";"):
                c = q[:i] + rep + q[j:]
                if ok(c):
                    q, changed = c, True
                    break
            i = q.rfind("\n", 0, i)
    return q


def phase1(p):
    tree = alpha_rename(strip_docstrings(ast.parse(p)))
    return ast_invariant_squeeze(ast.unparse(tree))


# ----------------------------------------------------- Phase 2 (test-guided)
def ddmin(p, oracle):
    """Complement-based delta debugging over characters; returns a 1-minimal p."""
    n = 2
    while len(p) >= 2:
        k = max(1, len(p) // n)
        chunks = [(i, min(i + k, len(p))) for i in range(0, len(p), k)]
        for a, b in chunks:
            c = p[:a] + p[b:]
            if oracle(c):
                p, n = c, max(n - 1, 2)
                break
        else:
            if k == 1:
                break
            n = min(2 * n, len(p))
    return p


def kdel(p, oracle, K=8):
    """Delete any contiguous substring of length <= K while the oracle accepts (to fixpoint)."""
    changed = True
    while changed:
        changed = False
        for k in range(K, 0, -1):
            i = 0
            while i + k <= len(p):
                c = p[:i] + p[i + k:]
                if oracle(c):
                    p, changed = c, True
                else:
                    i += 1
    return p


def gomez_reduce(p, oracle):
    q = phase1(p)
    assert oracle(q), "phase 1 must preserve semantics"
    q = ddmin(q, oracle)
    q = kdel(q, oracle)
    try:
        q = ast_invariant_squeeze(q)
    except Exception:
        pass
    return q


# --------------------------------------------------------- line collapse tau
def tau(p):
    """Newline-free equivalent: exec("...") with escapes (Python is escape-complete)."""
    if "\n" not in p:
        return p
    qc = '"' if p.count('"') <= p.count("'") else "'"
    body = p.replace("\\", "\\\\").replace(qc, "\\" + qc).replace("\n", "\\n")
    return "exec(" + qc + body + qc + ")"


def tau_bound(p):
    qc = '"' if p.count('"') <= p.count("'") else "'"
    return len(p) + 8 + p.count("\n") + p.count("\\") + p.count(qc)


def pareto(points):
    pts = sorted(set(points))
    front = []
    for c, l in pts:
        if not any(c2 <= c and l2 <= l and (c2, l2) != (c, l) for c2, l2 in pts):
            front.append((c, l))
    return front


if __name__ == "__main__":
    res = {}
    for name, t in T.items():
        o = Oracle(t)
        cands = {"canonical": t["canonical"], "multi": t["multi"], "oneline": t["oneline"], **t["extra"]}
        for k in ("multi", "oneline"):
            assert o(cands[k]), (name, k)
        cands["phase1"] = phase1(t["canonical"])
        assert o(cands["phase1"]), (name, "phase1")
        o.calls = 0
        import time; t0 = time.time()
        cands["reduced"] = gomez_reduce(t["canonical"], o)
        calls = o.calls; secs = round(time.time() - t0, 1)
        for k in list(cands):
            if "\n" in cands[k]:
                cands["tau_" + k] = tau(cands[k])
        for k, v in cands.items():
            assert o(v), (name, k)
        # fresh-seed re-validation guards against over-fitting the reducer to the test set
        o2 = Oracle(t, seed=12345)
        revalid = o2(cands["reduced"])
        stats = {k: (chars(v), lines(v)) for k, v in cands.items()}
        res[name] = dict(stats=stats, code=cands, oracle_calls=calls, secs=secs, revalidated=revalid,
                         pareto=pareto(list(stats.values())),
                         tau=[(k, chars(cands[k]), chars(cands["tau_" + k]), tau_bound(cands[k]))
                              for k in ("canonical", "multi", "phase1", "reduced") if "tau_" + k in cands])
        print(name, stats["canonical"], stats["phase1"], stats["reduced"], stats["multi"], stats["oneline"],
              "calls", calls, secs, "revalid", revalid, "pareto", res[name]["pareto"], flush=True)
        print("   reduced:", repr(cands["reduced"]))
    json.dump(res, open("exp2.json", "w"), indent=1)
