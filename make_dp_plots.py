#!/usr/bin/env python3
"""
make_dp_plots.py

Benchmarks DP (basic, mostfreq, leastfreq) with the same dynamic decimal x-axis.
"""
import signal
import pathlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from time import perf_counter_ns
from tqdm import tqdm
from helpers import load_dimacs
from solvers.dp_solver import dp_solver

# ===== CONFIG =====
VAR_START = 10
VAR_END = 15
VAR_COUNTS = list(range(VAR_START, VAR_END+1))

MAX_CLAUSES = 40
CLAUSE_STEP = 5
CLAUSE_COUNTS = list(range(CLAUSE_STEP, MAX_CLAUSES+1, CLAUSE_STEP))

DIGITS = len(str(MAX_CLAUSES))
DIV = 10 ** DIGITS

TIMEOUT_SEC = 120
CNF_BASE = pathlib.Path("cnfs")
SAT_DIR = CNF_BASE / "SAT"
UNSAT_DIR = CNF_BASE / "UNSAT"
# =================


class Timeout:
    def __init__(self, s): self.s = s

    def __enter__(self):
        signal.signal(signal.SIGALRM,
                      lambda *_: (_ for _ in ()).throw(TimeoutError))
        signal.alarm(self.s)

    def __exit__(self, *_):
        signal.alarm(0)


def load_entries(folder):
    lst = []
    for f in folder.glob("v*_c*.cnf"):
        v = int(f.stem.split("_")[0][1:])
        c = int(f.stem.split("_")[1][1:])
        if v in VAR_COUNTS and c in CLAUSE_COUNTS:
            lst.append((v, c, load_dimacs(f)))
    lst.sort(key=lambda t: (VAR_COUNTS.index(t[0]), CLAUSE_COUNTS.index(t[1])))
    return lst


def bench_dp(entries, strat):
    xs, ys = [], []
    for v, c, cnf in tqdm(entries, desc=f"dp-{strat}", leave=False):
        x = v + c / DIV
        try:
            with Timeout(TIMEOUT_SEC):
                t0 = perf_counter_ns()
                dp_solver(cnf, strategy=(None if strat == "basic" else strat))
                t = (perf_counter_ns() - t0) / 1e9
        except TimeoutError:
            t = float(TIMEOUT_SEC)
        xs.append(x)
        ys.append(t)
    return xs, ys


def fmt_time(x, _):
    if x >= 60:
        return f"{int(x//60)}m{int(x % 60)}s"
    if x >= 1:
        return f"{x:.2f}s"
    if x >= 1e-3:
        return f"{x*1e3:.1f}ms"
    return f"{x*1e6:.1f}µs"


def plot_dp(label):
    folder = SAT_DIR if label == "SAT" else UNSAT_DIR
    entries = load_entries(folder)
    xs_nums = [v + c/DIV for v, c, _ in entries]
    xs_lbls = [f"{v}.{c:0{DIGITS}d}" for v, c, _ in entries]

    plt.figure(figsize=(12, 4))
    for strat in ("basic", "mostfreq", "leastfreq"):
        xs, ys = bench_dp(entries, strat)
        plt.plot(xs, ys, marker=".", label=strat)

    plt.xlabel("variable.clauses (v.ccc)")
    plt.ylabel("runtime (s)")
    plt.title(f"DP on {label} CNFs")
    plt.legend()
    ax = plt.gca()
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_time))

    n = len(xs_nums)
    step = max(1, n // 25)
    plt.xticks(xs_nums[::step], xs_lbls[::step], rotation=90, fontsize=8)
    ax.grid(axis="y", alpha=0.3)

    out = pathlib.Path("graphs")/f"{label.lower()}_dp.png"
    out.parent.mkdir(exist_ok=True)
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    print(f"✓ saved {out}")


if __name__ == "__main__":
    plot_dp("SAT")
    plot_dp("UNSAT")
