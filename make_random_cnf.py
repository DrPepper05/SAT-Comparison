# make_random_cnf.py
import random
import pathlib
import argparse


def gen_random_3sat(n_vars, n_clauses, seed=42):
    rnd = random.Random(seed)
    cnf = []
    for _ in range(n_clauses):
        clause = set()
        while len(clause) < 3:
            lit = rnd.randint(1, n_vars)
            if rnd.random() < 0.5:
                lit = -lit
            clause.add(lit)
        cnf.append(list(clause))
    return cnf


def save_dimacs(path, cnf, n_vars):
    with open(path, "w") as f:
        f.write(f"p cnf {n_vars} {len(cnf)}\n")
        for c in cnf:
            f.write(" ".join(map(str, c))+" 0\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--vars", type=int, default=6)
    ap.add_argument("--clauses", type=int, default=20)
    ap.add_argument("--out", default="benchmarks/random6_20.cnf")
    args = ap.parse_args()

    cnf = gen_random_3sat(args.vars, args.clauses)
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    save_dimacs(args.out, cnf, args.vars)
    print("Wrote", args.out)
