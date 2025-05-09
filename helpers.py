# helpers.py
import json
import pathlib


def load_dimacs(path):
    """Read DIMACS CNF → list[list[int]] without trailing zero."""
    cnf = []
    with open(path) as f:
        for line in f:
            if line.startswith(("c", "p")):
                continue
            nums = list(map(int, line.split()))
            if nums:
                cnf.append(nums[:-1])
    return cnf


def save_json(obj, path):
    path = pathlib.Path(path)
    path.write_text(json.dumps(obj, indent=2))
