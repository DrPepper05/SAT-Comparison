#!/usr/bin/env python3
"""
create_php.py

Generate pigeonhole‐principle CNFs (unsatisfiable) for holes h:
  variables x_{i,j} for pigeons i=1..(h+1), holes j=1..h.

Clauses:
  • For each pigeon i: (x_{i,1} ∨ … ∨ x_{i,h})
  • For each hole j and pigeons i<k: (¬x_{i,j} ∨ ¬x_{k,j})

Usage:
  python create_php.py          # holes=1..10
  python create_php.py --holes 3 4 5  # only holes 3,4,5
  python create_php.py --max 20  # holes=1..20

Outputs files:
  cnfs/PHP/php_{p}_{h}.cnf
"""
import argparse
import pathlib


def gen_php_cnf(h):
    """
    Return (num_vars, clauses) for PHP with holes=h and pigeons p=h+1.
    Variables are numbered (i-1)*h + j  for i in [1..p], j in [1..h].
    """
    p = h + 1
    num_vars = p * h
    clauses = []
    # each pigeon in at least one hole
    for i in range(1, p+1):
        clause = [(i-1)*h + j for j in range(1, h+1)]
        clauses.append(clause)
    # no two pigeons share a hole
    for j in range(1, h+1):
        for i in range(1, p+1):
            for k in range(i+1, p+1):
                vi = (i-1)*h + j
                vk = (k-1)*h + j
                clauses.append([-vi, -vk])
    return num_vars, clauses


def write_dimacs(path, num_vars, clauses):
    with open(path, "w") as f:
        f.write(f"p cnf {num_vars} {len(clauses)}\n")
        for cl in clauses:
            f.write(" ".join(str(l) for l in cl) + " 0\n")


def main():
    p = argparse.ArgumentParser()
    group = p.add_mutually_exclusive_group()
    group.add_argument("--holes", "-n", type=int, nargs="+",
                       help="exact hole sizes to generate")
    group.add_argument("--max", type=int, default=10,
                       help="generate holes=1..MAX (default 10)")
    p.add_argument("--dir", "-d", default="cnfs/PHP",
                   help="output directory for php_{p}_{h}.cnf")
    args = p.parse_args()

    if args.holes:
        holes = sorted(set(args.holes))
    else:
        holes = list(range(1, args.max+1))

    outdir = pathlib.Path(args.dir)
    outdir.mkdir(parents=True, exist_ok=True)

    for h in holes:
        p_count = h + 1
        num_vars, clauses = gen_php_cnf(h)
        fname = f"php_{p_count}_{h}.cnf"
        path = outdir / fname
        write_dimacs(path, num_vars, clauses)
        print(f"Generated {path}  (#vars={num_vars}, #cls={len(clauses)})")


if __name__ == "__main__":
    main()
