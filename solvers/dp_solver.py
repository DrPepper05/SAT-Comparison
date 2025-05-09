"""
dp_solver.py  ––  Davis–Putnam algorithm (resolution + unit/pure rules)

Run:
    python dp_solver.py path/to/file.cnf [mostfreq|leastfreq]

Returns dict with clause_counts like resolution_solver.
"""
import sys
import json
import pathlib
from helpers import load_dimacs

# -------------------------------------------------------------------


def dp_solver(cnf, strategy="mostfreq"):
    formula = [list(c) for c in cnf]
    clause_counts = []

    def unit_propagate():
        nonlocal formula
        changed = True
        while changed:
            changed = False
            for clause in formula:
                if len(clause) == 0:
                    return False
                if len(clause) == 1:
                    lit = clause[0]
                    formula = [c for c in formula if lit not in c]
                    for c in formula:
                        if -lit in c:
                            c.remove(-lit)
                    changed = True
                    break
        return True

    # outer loop
    while True:
        if not unit_propagate():
            return {"sat": False, "clause_counts": clause_counts}

        # pure literals
        lits = {lit for c in formula for lit in c}
        pure = [lit for lit in lits if -lit not in lits]
        if pure:
            for lit in pure:
                formula = [c for c in formula if lit not in c]
            continue  # restart loop – maybe new unit clauses

        if not formula:
            return {"sat": True, "clause_counts": clause_counts}

        # pick variable appearing both ways
        vars_both = [v for v in {abs(l) for l in lits}
                     if (v in lits) and (-v in lits)]
        if not vars_both:
            return {"sat": True, "clause_counts": clause_counts}

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

        for c1 in pos:
            for c2 in neg:
                res = list({*(x for x in c1 if x != var),
                            *(y for y in c2 if y != -var)})
                if any(-l in res for l in res):
                    continue
                formula.append(res)

        if any(len(c) == 0 for c in formula):
            clause_counts.append(len(formula))
            return {"sat": False, "clause_counts": clause_counts}

        clause_counts.append(len(formula))


# -------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python dp_solver.py file.cnf [mostfreq|leastfreq]")
    path = pathlib.Path(sys.argv[1])
    strat = sys.argv[2] if len(sys.argv) > 2 else "mostfreq"
    res = dp_solver(load_dimacs(path), strategy=strat)
    print(json.dumps(res, indent=2))
