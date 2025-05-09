#!/usr/bin/env python3
"""
create_cnfs.py

For each v=1..6 and c in {5,10,…,MAX_CLAUSES}, generate CNFs as requested.
Use --mode to select:
  sat     ⇒ generate only SAT CNFs (into cnfs/SAT/)
  unsat   ⇒ generate only UNSAT CNFs (into cnfs/UNSAT/)
  both    ⇒ generate both (default)
"""

import random
import signal
import pathlib
import argparse
from solvers.dpll_solver import dpll_solver

# optional cnfgen for speed
try:
    from cnfgen import RandomCNF
    USE_CNFGEN = True
except ImportError:
    USE_CNFGEN = False

# ========== PARAMETERS ==========
VAR_COUNTS = range(40, 50)
MAX_CLAUSES = 500
CLAUSE_STEP = 5
CLAUSE_COUNTS = list(range(CLAUSE_STEP, MAX_CLAUSES+1, CLAUSE_STEP))
CLASSIFY_TIMEOUT = 5      # seconds per DPLL classification
MAX_ATTEMPTS = 10000000
BASE_DIR = pathlib.Path("cnfs")
SAT_DIR = BASE_DIR / "SAT"
UNSAT_DIR = BASE_DIR / "UNSAT"
# ================================

SAT_DIR.mkdir(parents=True, exist_ok=True)
UNSAT_DIR.mkdir(parents=True, exist_ok=True)


class Timeout:
    def __init__(self, sec): self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM,
                      lambda *_: (_ for _ in ()).throw(TimeoutError))
        signal.alarm(self.sec)

    def __exit__(self, *_):
        signal.alarm(0)


def gen_random_cnf(v, c, k=3, seed=0):
    """Generate a random k-CNF as list of clauses of length k."""
    if USE_CNFGEN:
        rc = RandomCNF(v, num_clauses=c, clause_size=k, seed=seed)
        return [cl.literals for cl in rc.clauses]
    rnd = random.Random(seed)
    return [
        [rnd.randint(1, v) * (1 if rnd.random() < 0.5 else -1)
         for _ in range(k)]
        for __ in range(c)
    ]


def classify(cnf):
    """Return True if CNF is SAT under DPLL-mostfreq within timeout."""
    try:
        with Timeout(CLASSIFY_TIMEOUT):
            return bool(dpll_solver(cnf, heuristic="mostfreq").get("sat", False))
    except TimeoutError:
        return False


def write_dimacs(path, cnf):
    nvars = max(abs(l) for cl in cnf for l in cl) if cnf else 0
    with open(path, "w") as f:
        f.write(f"p cnf {nvars} {len(cnf)}\n")
        for cl in cnf:
            f.write(" ".join(map(str, cl)) + " 0\n")


def make_sat(v, c):
    # Attempt to find a random SAT instance, else fallback
    for i in range(1, MAX_ATTEMPTS+1):
        cnf = gen_random_cnf(v, c, seed=v*1000 + c*10 + i)
        if classify(cnf):
            print(f"[SAT]   v={v},c={c}  found in {i} tries")
            return cnf
    # fallback: c clauses each containing at least one positive literal
    print(f"[SAT]   v={v},c={c}  fallback generating satisfiable")
    rnd = random.Random(v*1234 + c*5678)
    sat_cnf = []
    for _ in range(c):
        clause = set()
        while len(clause) < 3:
            lit = rnd.randint(1, v)
            sign = 1 if rnd.random() < 0.7 else -1
            clause.add(lit * sign)
        # ensure at least one positive
        if not any(l > 0 for l in clause):
            clause.pop()
            clause.add(rnd.randint(1, v))
        sat_cnf.append(list(clause))
    rnd.shuffle(sat_cnf)
    return sat_cnf


def make_unsat(v, c):
    # Attempt to find a random UNSAT instance, else fallback
    for i in range(1, MAX_ATTEMPTS+1):
        cnf = gen_random_cnf(v, c, seed=v*2000 + c*20 + i)
        if not classify(cnf):
            print(f"[UNSAT] v={v},c={c}  found in {i} tries")
            return cnf
    # fallback: contradictory full-v clauses + (c-2) random
    print(f"[UNSAT] v={v},c={c}  fallback contradiction")
    pos = list(range(1, v+1))
    neg = [-x for x in pos]
    rnd = random.Random(v*3000 + c*30)
    rest = [
        [rnd.randint(1, v)*(1 if rnd.random() < 0.5 else -1)
         for _ in range(3)]
        for __ in range(c-2)
    ]
    cnf = rest + [pos, neg]
    rnd.shuffle(cnf)
    return cnf


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["sat", "unsat", "both"], default="both",
                   help="which CNFs to generate")
    args = p.parse_args()

    for v in VAR_COUNTS:
        for c in CLAUSE_COUNTS:
            if args.mode in ("sat", "both"):
                sat_cnf = make_sat(v, c)
                write_dimacs(SAT_DIR / f"v{v}_c{c}.cnf", sat_cnf)
            if args.mode in ("unsat", "both"):
                unsat_cnf = make_unsat(v, c)
                write_dimacs(UNSAT_DIR / f"v{v}_c{c}.cnf", unsat_cnf)

    print("Done.")


if __name__ == "__main__":
    import argparse
    main()
