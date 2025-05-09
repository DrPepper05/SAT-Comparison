# SAT Solvers Experimental Suite

This repository contains scripts to generate, benchmark, and plot the performance of several SAT-solving algorithms (Resolution, DP, DPLL) on random CNF instances and on the pigeonhole principle (PHP). Pre-made graphs are provided so you can inspect results without running anything.

## Contents

```
.
├── create_cnfs.py              # generate SAT/UNSAT random CNFs
├── create_php.py               # generate pigeonhole CNFs
├── make_resolution_plots.py    # plot Resolution variants
├── make_dp_plots.py            # plot DP variants
├── make_dpll_plots.py          # plot DPLL variants
├── make_basic_comparison.py    # compare basic solvers
├── run_php.py                  # benchmark solvers on PHP
├── solvers/                    # solver implementations
│   ├── resolution_solver.py
│   ├── dp_solver.py
│   ├── dpll_solver.py
│   └── cdcl_solver.py
├── helpers.py                  # utility (DIMACS loader)
├── cnfs/                       # pre-generated CNF folders
│   ├── SAT/
│   ├── UNSAT/
│   └── PHP/
├── graphs/                     # pre-made PNGs for quick inspection
├── requirements.txt            # Python dependencies
└── README.md
```

## Pre-Made Graphs

The `graphs/` folder contains example output PNGs:

- `sat_resolution.png`, `unsat_resolution.png`
- `sat_dp.png`, `unsat_dp.png`
- `sat_dpll.png`, `unsat_dpll.png`
- `basic_comparison.png`

…so you can explore results immediately.

---

## Installation

1. **Clone the repo**  
   ```bash
   git clone https://github.com/<your-org>/sat-algorithms-comparison.git
   cd sat-algorithms-comparison
   ```

2. **Create a virtual environment** (recommended)  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```
   Or individually:
   ```bash
   pip install matplotlib tqdm numpy cnfgen
   ```

> **Note:** Uses Unix/macOS `signal` for timeouts; on Windows you may need a different timeout mechanism.

---

## Quick Start

### 1. Generate Random CNFs

By default generates SAT and UNSAT 3-CNFs for v=1…6, c=5,10,…,30:

```bash
python create_cnfs.py
```

To generate only SAT or only UNSAT:

```bash
python create_cnfs.py --mode sat
python create_cnfs.py --mode unsat
```

To change clause range (e.g. up to 100, step 10), edit the top of `create_cnfs.py`:

```python
MAX_CLAUSES = 100
CLAUSE_STEP = 10
```

### 2. Plot Random-CNF Benchmarks

Resolution:
```bash
python make_resolution_plots.py
```

DP:
```bash
python make_dp_plots.py
```

DPLL:
```bash
python make_dpll_plots.py
```

Basic comparison:
```bash
python make_basic_comparison.py
```

All figures go to `graphs/`.

### 3. Generate Pigeonhole CNFs

By default for holes=1…10:
```bash
python create_php.py
```

Or specific holes:
```bash
python create_php.py --holes 3 5 7
```

### 4. Benchmark PHP

Run all solvers on PHP instances:
```bash
python run_php.py --holes 3 4 5 --algs all --report php_results.csv
```
- `--holes`: list of hole sizes  
- `--algs`: comma-separated list or `all`  
- `--report`: path to CSV  

At completion, a summary prints the fastest solver.

---

## Advanced

- **Customize ranges:** edit `VAR_START`, `VAR_END`, `MAX_CLAUSES`, `CLAUSE_STEP` at the top of each `make_*` script.  
- **Select strategies:** use flags in `run_php.py` or script code.  
- **Timeouts:** adjust `TIMEOUT_SEC` for longer experiments.  

---

## requirements.txt

```
matplotlib
tqdm
numpy
cnfgen
```

---

Enjoy exploring SAT solver performance! If you have questions or contributions, feel free to open an issue or PR.
