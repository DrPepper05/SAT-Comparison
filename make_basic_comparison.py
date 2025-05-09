#!/usr/bin/env python3
"""
make_basic_comparison.py

Compare the three “basic” solvers—Resolution “basic”, DP “basic”, and DPLL “fixed”—on the SAT CNFs.

Reads pregenerated CNFs from cnfs/SAT/v{v}_c{c}.cnf for
  v in [VAR_START..VAR_END]
  c in {CLAUSE_STEP, 2*CLAUSE_STEP, …, MAX_CLAUSES}

Plots a single figure “graphs/basic_comparison.png” with all three curves:
  • Resolution (basic)
  • DP (basic)
  • DPLL (fixed)

X‐axis: decimal v + c/DIV (e.g. v=3,c=105 → 3.105), tick‐labels “3.105”.
Y‐axis: log‐scale runtime.
"""

import signal
import pathlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from time import perf_counter_ns
from tqdm import tqdm
from helpers import load_dimacs
from solvers.resolution_solver import resolution_solver
from solvers.dp_solver import dp_solver
from solvers.dpll_solver import dpll_solver

# ===== CONFIGURATION =====
VAR_START = 6
VAR_END = 8
VAR_COUNTS = list(range(VAR_START, VAR_END+1))

MAX_CLAUSES = 40
CLAUSE_STEP = 5
CLAUSE_COUNTS = list(range(CLAUSE_STEP, MAX_CLAUSES+1, CLAUSE_STEP))

# compute digits & divisor for decimal encoding
DIGITS = len(str(MAX_CLAUSES))
DIV = 10 ** DIGITS

TIMEOUT_SEC = 120
CNF_BASE = pathlib.Path("cnfs")
SAT_DIR = CNF_BASE / "SAT"
OUT_PATH = pathlib.Path("graphs") / "basic_comparison.png"
# =========================


class Timeout:
    def __init__(self, sec): self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM,
                      lambda *_: (_ for _ in ()).throw(TimeoutError))
        signal.alarm(self.sec)

    def __exit__(self, *_):
        signal.alarm(0)


def load_entries(folder):
    entries = []
    for f in sorted(folder.glob("v*_c*.cnf")):
        v = int(f.stem.split("_")[0][1:])
        c = int(f.stem.split("_")[1][1:])
        if v in VAR_COUNTS and c in CLAUSE_COUNTS:
            entries.append((v, c, load_dimacs(f)))
    # sort by v then c
    entries.sort(key=lambda t: (
        VAR_COUNTS.index(t[0]), CLAUSE_COUNTS.index(t[1])))
    return entries


def bench(entries, solver_fn):
    xs, ys = [], []
    for v, c, cnf in tqdm(entries, desc=solver_fn.__name__, leave=False):
        x = v + c / DIV
        try:
            with Timeout(TIMEOUT_SEC):
                t0 = perf_counter_ns()
                solver_fn(cnf)
                t = (perf_counter_ns() - t0) / 1e9
        except TimeoutError:
            t = float(TIMEOUT_SEC)
        xs.append(x)
        ys.append(t)
    return xs, ys


def main():
    # load and encode entries
    entries = load_entries(SAT_DIR)
    xs_nums = [v + c/DIV for v, c, _ in entries]
    xs_lbls = [f"{v}.{c:0{DIGITS}d}" for v, c, _ in entries]

    # define the three basic runners
    runners = [
        ("Resolution (basic)", lambda cnf: resolution_solver(cnf, strategy=None)),
        ("DP (basic)", lambda cnf: dp_solver(cnf, strategy=None)),
        ("DPLL (fixed)", lambda cnf: dpll_solver(cnf, heuristic="fixed")),
    ]

    plt.figure(figsize=(12, 5))
    for label, fn in runners:
        xs, ys = bench(entries, fn)
        plt.plot(xs, ys, marker=".", label=label)

    plt.xlabel("variable.clauses (v.ccc)")
    plt.ylabel("runtime (s)")
    plt.title("Basic‐solver Comparison on SAT CNFs")
    plt.legend()
    ax = plt.gca()
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(
        lambda x, _: f"{x:.2f}s" if x >= 1 else (
            f"{x*1e3:.1f}ms" if x >= 1e-3 else f"{x*1e6:.1f}µs")
    ))

    # subsample ~25 ticks for readability
    n = len(xs_nums)
    step = max(1, n // 25)
    plt.xticks(xs_nums[::step], xs_lbls[::step], rotation=90, fontsize=8)
    ax.grid(axis="y", alpha=0.3)

    OUT_PATH.parent.mkdir(exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUT_PATH)
    plt.close()

    print(f"✓ saved comparison plot to {OUT_PATH}")


if __name__ == "__main__":
    main()
