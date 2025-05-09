#!/usr/bin/env python3
import argparse
import time
import importlib
import json
import pathlib
import sys
from helpers import load_dimacs, save_json

SOLVERS = {
    "resolution": ("solvers.resolution_solver",  "resolution_solver"),
    "dp": ("solvers.dp_solver",          "dp_solver"),
    "dpll": ("solvers.dpll_solver",        "dpll_solver"),
    "cdcl": ("solvers.cdcl_solver",        "dpll_cdcl_solver"),
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("solver", choices=SOLVERS, help="resolution|dp|dpll|cdcl")
    ap.add_argument("cnf",                  help="path to .cnf file")
    ap.add_argument("--opt", default="",
                    help="comma‑separated kw=value args")
    args = ap.parse_args()

    mod_name, fun_name = SOLVERS[args.solver]
    solver = getattr(importlib.import_module(mod_name), fun_name)

    kwargs = dict(k.split("=") for k in args.opt.split(",") if k)
    cnf_path = pathlib.Path(args.cnf)
    cnf = load_dimacs(cnf_path)

    t0 = time.time()
    result = solver(cnf, **kwargs)      # ←‑ every solver returns dict or bool
    runtime = time.time() - t0

    # Normalise result to dict
    if isinstance(result, bool):
        result = {"sat": result}
    result["seconds"] = round(runtime, 3)

    print(json.dumps(result, indent=2))

    # ---- side files for graphs ----
    stem = f"{cnf_path.stem}_{args.solver}"
    if "decisions" in result or "conflicts" in result:
        save_json(result, f"{stem}.stats.json")
    if "clause_counts" in result:
        save_json(result["clause_counts"], f"{stem}.clause.json")
