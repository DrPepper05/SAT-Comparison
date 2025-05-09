#!/usr/bin/env python3
"""
run_php.py

Benchmark SAT‐solvers (Resolution, DP, DPLL) on pregenerated pigeonhole CNFs:
  cnfs/PHP/php_{p}_{h}.cnf, where p = h+1.

Usage:
  python run_php.py --holes 3 4 5 --algs all --report php_results.csv

At the end it prints a summary table and names the fastest algorithm.
"""
import argparse
import pathlib
import signal
import csv
import sys
from time import perf_counter
from helpers import load_dimacs

# solver imports (no CDCL)
from solvers.resolution_solver import resolution_solver
from solvers.dp_solver import dp_solver
from solvers.dpll_solver import dpll_solver

# timeout context (Unix/macOS)


class Timeout:
    def __init__(self, sec): self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM,
                      lambda *_: (_ for _ in ()).throw(TimeoutError))
        signal.alarm(self.sec)

    def __exit__(self, *_):
        signal.alarm(0)


# all supported algorithm specs
ALL_ALGS = [
    "resolution-basic",
    "resolution-mostfreq",
    "resolution-leastfreq",
    "dp-basic",
    "dp-mostfreq",
    "dp-leastfreq",
    "dpll-fixed",
    "dpll-mostfreq",
    "dpll-jeroslow"
]


def make_runner(alg_spec):
    name, _, param = alg_spec.partition("-")
    if name == "resolution":
        strat = param or "basic"

        def run(cnf):
            return resolution_solver(cnf,
                                     strategy=(None if strat == "basic" else strat))
        label = f"res-{strat}"
    elif name == "dp":
        strat = param or "basic"

        def run(cnf):
            return dp_solver(cnf,
                             strategy=(None if strat == "basic" else strat))
        label = f"dp-{strat}"
    elif name == "dpll":
        heur = param or "fixed"

        def run(cnf):
            return dpll_solver(cnf, heuristic=heur)
        label = f"dpll-{heur}"
    else:
        raise ValueError(f"Unknown algorithm spec: {alg_spec}")
    return label, run


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--holes", "-n", type=int, nargs="+", required=True,
                   help="hole‐counts to test (pigeons = holes+1)")
    p.add_argument("--algs",  "-a", type=str, required=True,
                   help="comma‐sep list of solver variants or 'all'")
    p.add_argument("--timeout", "-t", type=int, default=120,
                   help="timeout per run (seconds)")
    p.add_argument("--report",  "-r", default="php_results.csv",
                   help="output CSV report path")
    p.add_argument("--dir",     "-d", default="cnfs/PHP",
                   help="folder with php_{p}_{h}.cnf files")
    args = p.parse_args()

    # expand --algs all
    if args.algs.strip().lower() == "all":
        alg_specs = ALL_ALGS
    else:
        alg_specs = [s.strip() for s in args.algs.split(",")]

    # prepare runners
    runners = []
    for spec in alg_specs:
        try:
            lbl, fn = make_runner(spec)
            runners.append((lbl, fn))
        except ValueError as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)

    # data collectors
    timings = {lbl: [] for lbl, _ in runners}
    sat_count = {lbl: 0 for lbl, _ in runners}
    unsat_count = {lbl: 0 for lbl, _ in runners}

    # open CSV report
    report_file = pathlib.Path(args.report)
    with report_file.open("w", newline="") as fh:
        writer = csv.DictWriter(fh,
                                fieldnames=["holes", "pigeons", "algorithm", "sat", "time", "decisions", "conflicts"])
        writer.writeheader()

        # run each combination
        for h in args.holes:
            p_count = h + 1
            fname = f"php_{p_count}_{h}.cnf"
            path = pathlib.Path(args.dir) / fname
            if not path.exists():
                print(f"Missing CNF: {path}", file=sys.stderr)
                continue
            cnf = load_dimacs(path)

            for label, run in runners:
                try:
                    with Timeout(args.timeout):
                        t0 = perf_counter()
                        stats = run(cnf)
                        elapsed = perf_counter() - t0
                except TimeoutError:
                    stats = {"sat": False}
                    elapsed = args.timeout

                sat = bool(stats.get("sat", False))
                dec = stats.get("decisions", "")
                conf = stats.get("conflicts", "")

                # record
                timings[label].append(elapsed)
                if sat:
                    sat_count[label] += 1
                else:
                    unsat_count[label] += 1

                # console output
                print(f"[{label:12}] holes={h:2} pigeons={p_count:2} "
                      f"sat={sat} time={elapsed:.3f}s "
                      f"decisions={dec} conflicts={conf}")

                # write CSV row
                writer.writerow({
                    "holes": h,
                    "pigeons": p_count,
                    "algorithm": label,
                    "sat": "SAT" if sat else "UNSAT",
                    "time": f"{elapsed:.6f}",
                    "decisions": dec,
                    "conflicts": conf
                })

    # Summary
    print("\n=== Summary ===")
    print(f"{'Algorithm':15}{'Runs':>6}{'Total(s)':>12}{'Avg(s)':>10}{'SAT':>6}{'UNSAT':>7}")
    summary = []
    for label in timings:
        runs = len(timings[label])
        total = sum(timings[label])
        avg = total / runs if runs else float("inf")
        s_cnt = sat_count[label]
        u_cnt = unsat_count[label]
        summary.append((label, runs, total, avg, s_cnt, u_cnt))
        print(f"{label:15}{runs:6}{total:12.3f}{avg:10.3f}{s_cnt:6}{u_cnt:7}")

    # find fastest by average time
    fastest = min(summary, key=lambda x: x[3])
    print(
        f"\nFastest algorithm: {fastest[0]} with average time {fastest[3]:.3f}s")

    print(f"Report saved to {report_file}")


if __name__ == "__main__":
    main()
