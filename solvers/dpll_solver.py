"""
dpll_solver.py  ––  classical DPLL without learning
Heuristics available:
    • fixed      – first unassigned variable (default)
    • mostfreq   – literal with max occurrence
    • jeroslow   – Jeroslow–Wang score
Returns dict:
    {"sat": bool, "decisions": int}
"""
import sys
import json
import pathlib
from helpers import load_dimacs

# -------------------------------------------------------------------


def jeroslow_wang_literal(formula):
    """Return literal with max Σ 2^-|C| over clauses containing that literal."""
    scores = {}
    for clause in formula:
        weight = 2 ** (-len(clause))
        for lit in clause:
            scores[lit] = scores.get(lit, 0) + weight
    return max(scores, key=scores.get)


def dpll_solver(cnf, heuristic="fixed"):
    formula = [list(c) for c in cnf]
    decisions = 0

    def backtrack(form):
        nonlocal decisions

        # ---- unit propagation ----
        changed = True
        while changed:
            changed = False
            for clause in form:
                if len(clause) == 0:
                    return False
                if len(clause) == 1:
                    lit = clause[0]
                    form[:] = [c for c in form if lit not in c]
                    for c in form:
                        if -lit in c:
                            c.remove(-lit)
                    changed = True
                    break

        # ---- pure literal ----
        lits = {lit for c in form for lit in c}
        pure = [lit for lit in lits if -lit not in lits]
        if pure:
            for lit in pure:
                form[:] = [c for c in form if lit not in c]

        if not form:
            return True
        if any(len(c) == 0 for c in form):
            return False

        # ---- choose branching literal ----
        if heuristic == "mostfreq":
            counts = {}
            for c in form:
                for lit in c:
                    counts[lit] = counts.get(lit, 0) + 1
            lit = max(counts, key=counts.get)
            choices = [lit, -abs(lit) if lit > 0 else abs(lit)]

        elif heuristic == "jeroslow":
            lit = jeroslow_wang_literal(form)
            choices = [lit, -abs(lit) if lit > 0 else abs(lit)]

        else:  # fixed
            var = min(abs(l) for l in lits)
            choices = [var, -var]

        # ---- branch ----
        for lit in choices:
            decisions += 1
            new_form = [c[:] for c in form]
            new_form = [c for c in new_form if lit not in c]
            for c in new_form:
                if -lit in c:
                    c.remove(-lit)
            if backtrack(new_form):
                return True
        return False

    sat = backtrack(formula)
    return {"sat": sat, "decisions": decisions}


# -------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(
            "usage: python dpll_solver.py file.cnf [fixed|mostfreq|jeroslow]")
    path = pathlib.Path(sys.argv[1])
    heur = sys.argv[2] if len(sys.argv) > 2 else "fixed"
    res = dpll_solver(load_dimacs(path), heuristic=heur)
    print(json.dumps(res, indent=2))
