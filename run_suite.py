#!/usr/bin/env python3
import itertools
import json
import subprocess
import csv
import pathlib
import json
import time
import itertools
import pandas as pd
import matplotlib.pyplot as plt

# ---------- configuration ----------
BENCH_DIR = pathlib.Path("benchmarks")
SOLVER_OPTS = [
    ("resolution", "strategy=mostfreq"),
    ("resolution", "strategy=leastfreq"),
    ("dp",         "strategy=mostfreq"),
    ("dp",         "strategy=leastfreq"),
    ("dpll",       "heuristic=fixed"),
    ("dpll",       "heuristic=mostfreq"),
    ("cdcl",       "use_vsids=False"),
    ("cdcl",       "use_vsids=True"),
]
TIMEOUT = 600          # 10 min
CSV_OUT = "results.csv"
GRAPHS = pathlib.Path("graphs")
GRAPHS.mkdir(exist_ok=True)

# ---------- run ----------
rows = []
for cnf in BENCH_DIR.glob("*.cnf"):
    for name, opt in SOLVER_OPTS:
        cmd = ["python", "run_one.py", name, str(cnf)]
        if opt:
            cmd += ["--opt", opt]
        print("▶", cnf.name, name, opt or "-")
        t0 = time.time()
        try:
            out = subprocess.run(cmd, capture_output=True,
                                 text=True, timeout=TIMEOUT)
            runtime = time.time()-t0
            res = json.loads(out.stdout.strip() or "{}")
            res.setdefault("sat", "?")
        except subprocess.TimeoutExpired:
            runtime = TIMEOUT
            res = {"sat": "timeout"}
        rows.append(dict(instance=cnf.name, solver=f"{name}:{opt}",
                         sat=res.get("sat"), seconds=round(runtime, 3)))
# save csv
pd.DataFrame(rows).to_csv(CSV_OUT, index=False)
print("✓ CSV saved:", CSV_OUT)

# ---------- graph 1 : runtimes ----------
df = pd.read_csv(CSV_OUT)
for inst, sub in df.groupby("instance"):
    sub = sub.sort_values("seconds")
    sub.plot.bar(x="solver", y="seconds", legend=False, rot=45,
                 title=f"Runtime on {inst}")
    plt.ylabel("seconds")
    plt.tight_layout()
    plt.savefig(GRAPHS/f"runtime_{inst}.png")
    plt.close()

# ---------- graph 2 : clause growth (Resolution/DP) ----------
clause_files = list(pathlib.Path().glob("*_*.clause.json"))
if clause_files:
    for clause_path in clause_files:
        data = json.loads(clause_path.read_text())
        label = clause_path.stem
        plt.plot(range(1, len(data)+1), data, label=label)
    plt.legend()
    plt.xlabel("elimination step")
    plt.ylabel("#clauses")
    plt.title("Clause growth during variable elimination")
    plt.tight_layout()
    plt.savefig(GRAPHS/"clause_growth.png")
    plt.close()

# ---------- graph 3 : decision / conflict counts ----------
stats_files = list(pathlib.Path().glob("*_*.stats.json"))
if stats_files:
    stats = []
    for p in stats_files:
        d = json.loads(p.read_text())
        d["solver"] = p.stem.split("_")[-1]
        d["instance"] = "_".join(p.stem.split("_")[:-1])
        stats.append(d)
    sdf = pd.DataFrame(stats)
    # decisions
    if "decisions" in sdf:
        sdf.pivot(index="instance", columns="solver",
                  values="decisions").plot.bar(rot=0)
        plt.title("Decision count per solver per instance")
        plt.tight_layout()
        plt.savefig(GRAPHS/"decisions.png")
        plt.close()
    # conflicts (CDCL only)
    if "conflicts" in sdf:
        sdf.pivot(index="instance", columns="solver",
                  values="conflicts").plot.bar(rot=0)
        plt.title("Conflicts (CDCL)")
        plt.tight_layout()
        plt.savefig(GRAPHS/"conflicts.png")
        plt.close()

print("✓ graphs written to", GRAPHS)
