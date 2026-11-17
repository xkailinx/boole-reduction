Algebra of Boole

## Quick start

```bash
pip install -r requirements.txt
```

### Reduce only (GF(2), fastest — full reduced form)

```bash
python run_reduce.py --expr "(a-->b)&(b-->c)&(c-->d)"
python run_reduce.py --case syllogism
```

### Compare implementations with timing (CLI)

Runs **boole_engine (GF(2))**, **LogicJudge.py**, **LogicJudgeUpdated.py**, and partition mode on built-in or custom cases:

```bash
python run_compare.py                    # default benchmark set
python run_compare.py --list             # list all example cases
python run_compare.py --case makesample_8
python run_compare.py --expr "a | ~a"
python run_compare.py --quick            # GF(2) only (fast)
```

### Web interface

```bash
python web/app.py
```

Open **http://127.0.0.1:8000** — enter a logic expression or pick an example, then compare timing across all implementations.

### Run tests

```bash
python -m unittest tests.test_boole_correctness -v
```

---

## Core modules

| File | Description |
|------|-------------|
| `src/boole_engine.py` | **New** GF(2) reduction engine (fastest, most correct) |
| `src/LogicJudge.py` | Original brute-force SymPy |
| `src/LogicJudgeUpdated.py` | Partitioned SymPy (paper algorithm) |
| `src/compare_runner.py` | Shared benchmark logic for CLI + web |
| `src/BaseClass.py` | OO syllogism API |

Logic expressions use: `-->` (implies), `|` (or), `&` (and), `~` (not), `()` grouping.

---
