"""Benchmark specifications for Experiment 2.

Each task fixes: an interface (binding name, call shape), a domain D of
inputs (a random generator plus edge cases), a canonical reference program,
and hand-written candidates. Candidates are only accepted if the
differential-testing oracle in harness.py finds them observationally
equivalent to the reference on D.
"""
import random

T = {}


def task(name, kind, gen, canonical, multi, oneline, note="", extra=None):
    T[name] = dict(name=name, kind=kind, gen=gen, canonical=canonical.strip("\n"),
                   multi=multi.strip("\n"), oneline=oneline.strip("\n"), note=note, extra=extra or {})


# ---------------------------------------------------------------- functions
task("factorial", "fn", lambda r: [(n,) for n in [0, 1, 2] + [r.randint(0, 60) for _ in range(60)]],
'''
def f(n):
    """Return n! for a non-negative integer n."""
    result = 1
    for i in range(2, n + 1):
        result = result * i
    return result
''',
'''
def f(n):
 r=1
 for i in range(n):r*=i+1
 return r
''',
'''
import math;f=math.factorial
''')

task("fibonacci", "fn", lambda r: [(n,) for n in [0, 1, 2, 70, 71, 80] + [r.randint(0, 90) for _ in range(60)]],
'''
def f(n):
    """Return the n-th Fibonacci number, F(0)=0 and F(1)=1."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
''',
'''
def f(n):
 a,b=0,1
 for _ in range(n):a,b=b,a+b
 return a
''',
'''
f=lambda n,a=0,b=1:n and f(n-1,b,a+b)or a
''')

task("gcd", "fn", lambda r: [(r.randint(-60, 60), r.randint(-60, 60)) for _ in range(150)] + [(0, 0), (0, 5), (5, 0), (-4, 6), (4, -6)],
'''
def f(a, b):
    """Greatest common divisor by Euclid's algorithm."""
    while b != 0:
        a, b = b, a % b
    return a
''',
'''
def f(a,b):
 while b:a,b=b,a%b
 return a
''',
'''
f=lambda a,b:b and f(b,a%b)or a
''')

task("is_prime", "fn", lambda r: [(n,) for n in range(-5, 400)] + [(r.randint(400, 3000),) for _ in range(80)],
'''
def f(n):
    """Return True if n is a prime number."""
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True
''',
'''
def f(n):
 i=2
 while i*i<=n:
  if n%i<1:return False
  i+=1
 return n>1
''',
'''
f=lambda n:n>1 and all(n%i for i in range(2,n))
''')

def _pal(r):
    out = [("",), ("a",), ("ab",), ("aba",), ("abba",), ("abca",)]
    for _ in range(150):
        s = "".join(r.choice("ab") for _ in range(r.randint(0, 7)))
        if r.random() < .4:
            s = s + s[::-1][r.randint(0, 1):]
        out.append((s,))
    return out

task("palindrome", "fn", _pal,
'''
def f(s):
    """Return True if the string s reads the same backwards."""
    i, j = 0, len(s) - 1
    while i < j:
        if s[i] != s[j]:
            return False
        i += 1
        j -= 1
    return True
''',
'''
def f(s):
 return s==s[::-1]
''',
'''
f=lambda s:s==s[::-1]
''')

task("fizzbuzz", "fn", lambda r: [(n,) for n in [0, 1, 15, 16, 100] + [r.randint(0, 120) for _ in range(30)]],
'''
def f(n):
    """Return the FizzBuzz sequence for 1..n as a list of strings."""
    out = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            out.append("FizzBuzz")
        elif i % 3 == 0:
            out.append("Fizz")
        elif i % 5 == 0:
            out.append("Buzz")
        else:
            out.append(str(i))
    return out
''',
'''
def f(n):
 return[i%3//2*"Fizz"+i%5//4*"Buzz"or str(i+1)for i in range(n)]
''',
'''
f=lambda n:[i%3//2*"Fizz"+i%5//4*"Buzz"or str(i+1)for i in range(n)]
''')

def _nested(r, d=0):
    out = []
    for _ in range(r.randint(0, 4)):
        if d < 3 and r.random() < .35:
            out.append(_nested(r, d + 1))
        else:
            out.append(r.randint(0, 9))
    return out

task("flatten", "fn", lambda r: [([],), ([[]],), ([1, [2, [3]]],)] + [(_nested(r),) for _ in range(150)],
'''
def f(xs):
    """Flatten an arbitrarily nested list of integers."""
    out = []
    for x in xs:
        if isinstance(x, list):
            out.extend(f(x))
        else:
            out.append(x)
    return out
''',
'''
def f(x):
 r=[]
 for a in x:r+=f(a)if[]==a*0 else[a]
 return r
''',
'''
f=lambda x:[b for a in x for b in(f(a)if[]==a*0 else[a])]
''')

task("collatz", "fn", lambda r: [(n,) for n in [1, 2, 3, 27, 97] + [r.randint(1, 5000) for _ in range(120)]],
'''
def f(n):
    """Number of Collatz steps needed to reach 1 from n >= 1."""
    steps = 0
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        steps += 1
    return steps
''',
'''
def f(n):
 c=0
 while n>1:n=n%2*(3*n+1)or n//2;c+=1
 return c
''',
'''
f=lambda n:n>1 and-~f(n%2*(3*n+1)or n//2)or 0
''')

def _mat(r):
    out = [([],), ([[]],), ([[1]],), ([[1, 2], [3, 4], [5, 6]],)]
    for _ in range(100):
        h, w = r.randint(1, 4), r.randint(0, 4)
        out.append(([[r.randint(0, 9) for _ in range(w)] for _ in range(h)],))
    return out

task("transpose", "fn", _mat,
'''
def f(m):
    """Transpose a rectangular matrix given as a list of rows."""
    if not m:
        return []
    rows, cols = len(m), len(m[0])
    return [[m[r][c] for r in range(rows)] for c in range(cols)]
''',
'''
def f(m):
 return[*map(list,zip(*m))]
''',
'''
f=lambda m:[*map(list,zip(*m))]
''')

def _ints(r):
    base = ["0", "-7", "+12", " 42 ", "1_000", "abc", "", "3.5", "0x1f", "12a", "--1", "٣"]
    alpha = "0123456789+-_ ax."
    return [(s,) for s in base] + [("".join(r.choice(alpha) for _ in range(r.randint(0, 5))),) for _ in range(300)]

task("safe_int", "fn", _ints,
'''
def f(s):
    """Parse s as an int; return 0 if s is not a valid integer literal."""
    try:
        return int(s)
    except ValueError:
        return 0
''',
'''
def f(s):
 try:return int(s)
 except:return 0
''',
'''
exec("def f(s):\\n try:return int(s)\\n except:return 0")
''', note="no expression-level exception handling in Python")

# ------------------------------------------------------------------ classes
STACK_OPS = [("push", lambda r: (r.randint(0, 9),)), ("pop", lambda r: ()), ("peek", lambda r: ()),
             ("size", lambda r: ()), ("empty", lambda r: ())]

task("stack", ("cls", "S", lambda r: (), STACK_OPS, ()), None,
'''
class S:
    """A LIFO stack."""

    def __init__(self):
        self.items = []

    def push(self, x):
        self.items.append(x)

    def pop(self):
        return self.items.pop()

    def peek(self):
        return self.items[-1]

    def size(self):
        return len(self.items)

    def empty(self):
        return len(self.items) == 0
''',
'''
class S(list):push=list.append;peek=lambda s:s[-1];size=list.__len__;empty=lambda s:s==[]
''',
'''
class S(list):push=list.append;peek=lambda s:s[-1];size=list.__len__;empty=lambda s:s==[]
''')

ACCT_OPS = [("deposit", lambda r: (r.randint(0, 50),)), ("withdraw", lambda r: (r.randint(0, 80),))]

task("account", ("cls", "A", lambda r: r.choice([(), (r.randint(0, 50),)]), ACCT_OPS, ("balance",)), None,
'''
class A:
    """A bank account whose balance never becomes negative."""

    def __init__(self, balance=0):
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount
        return self.balance

    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("insufficient funds")
        self.balance -= amount
        return self.balance
''',
'''
class A:
 def __init__(s,b=0):s.balance=b
 def deposit(s,a):s.balance+=a;return s.balance
 def withdraw(s,a):
  if a>s.balance:raise ValueError("insufficient funds")
  return s.deposit(-a)
''',
'''
class A:__init__=lambda s,b=0:setattr(s,"balance",b);deposit=lambda s,a:setattr(s,"balance",s.balance+a)or s.balance;withdraw=lambda s,a:s.deposit(-a)if a<=s.balance else(_ for _ in()).throw(ValueError("insufficient funds"))
''', extra={
 "exec_withdraw": '''class A:
 def __init__(s,b=0):s.balance=b
 def deposit(s,a):s.balance+=a;return s.balance
 exec("def withdraw(s,a):\\n if a>s.balance:raise ValueError('insufficient funds')\\n return s.deposit(-a)")''',
 "class_exec": '''class A:exec("def __init__(s,b=0):s.balance=b\\ndef deposit(s,a):s.balance+=a;return s.balance\\ndef withdraw(s,a):\\n if a>s.balance:raise ValueError('insufficient funds')\\n return s.deposit(-a)")'''})
