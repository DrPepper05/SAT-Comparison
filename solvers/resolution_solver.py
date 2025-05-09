"""
resolution_solver.py  ––  pure resolution refutation (no splitting)

Call resolution_solver(cnf, strategy="mostfreq"|"leastfreq") from Python,
or run as a script:

    python resolution_solver.py path/to/file.cnf  [mostfreq|leastfreq]

Returns dict:
    {
        "sat":  True | False,
        "clause_counts": [int, int, ...]   # clause total after each elim step
    }
"""
from itertools import combinations
import sys
import json
import pathlib

# -------------------------------------------------------------------


def resolution_solver(cnf, strategy="mostfreq"):
    """Resolution SAT solver.  cnf is list[list[int]]"""
    formula = [list(c) for c in cnf]          # deep‑copy
    clause_counts = []

    # quick checks
    if not formula:
        return {"sat": True, "clause_counts": clause_counts}
    if any(len(c) == 0 for c in formula):
        return {"sat": False, "clause_counts": clause_counts}

    while True:
        # ---- pure‑literal elimination ----
        changed = True
        while changed:
            changed = False
            lits = {lit for c in formula for lit in c}
            for v in {abs(l) for l in lits}:
                if (v in lits) != (-v in lits):
                    # v is pure
                    lit = v if v in lits else -v
                    formula = [c for c in formula if lit not in c]
                    changed = True
        if not formula:
            return {"sat": True, "clause_counts": clause_counts}

        # pick variable with both polarities
        vars_both = [v for v in {abs(l) for c in formula for l in c}
                     if any(v in c for c in formula) and any(-v in c for c in formula)]
        if not vars_both:
            return {"sat": True, "clause_counts": clause_counts}

        # choose by frequency
        if strategy in ("mostfreq", "leastfreq"):
            freq = {v: 0 for v in vars_both}
            for c in formula:
                for lit in set(c):
                    if abs(lit) in freq:
                        freq[abs(lit)] += 1
            var = max(freq, key=freq.get) if strategy == "mostfreq" else min(
                freq, key=freq.get)
        else:
            var = vars_both[0]

        pos = [c for c in formula if var in c]
        neg = [c for c in formula if -var in c]
        formula = [c for c in formula if var not in c and -var not in c]

        # generate resolvents
        for c1 in pos:
            for c2 in neg:
                resolvent = list({*(x for x in c1 if x != var),
                                  *(y for y in c2 if y != -var)})
                if any(-l in resolvent for l in resolvent):   # tautology
                    continue
                formula.append(resolvent)

        if any(len(c) == 0 for c in formula):
            clause_counts.append(len(formula))
            return {"sat": False, "clause_counts": clause_counts}

        clause_counts.append(len(formula))


# -------------------------------------------------------------------
if __name__ == "__main__":
    from helpers import load_dimacs
    if len(sys.argv) < 2:
        sys.exit(
            "usage: python resolution_solver.py file.cnf [mostfreq|leastfreq]")
    path = pathlib.Path(sys.argv[1])
    strat = sys.argv[2] if len(sys.argv) > 2 else "mostfreq"
    res = resolution_solver(load_dimacs(path), strategy=strat)
    print(json.dumps(res, indent=2))
