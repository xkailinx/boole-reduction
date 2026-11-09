Algebra of Boole

All the work referenced to [Boole Reduction: A challenge for programmers | MathFoundations 269 | N J Wildberger (youtube.com)](https://www.youtube.com/watch?v=AJr44JgbKho&list=PLIljB45xT85CnIGIWb7tH1F_S2PyOC8rb&index=19)，The relevant code is in [shanyoumu461/Algebra-of-Boole: Algebra Of Boole (github.com)](https://github.com/shanyoumu461/Algebra-of-Boole/tree/main).

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

## Legacy usage

`LogicJudge.py` is used to judge logical expressions. You can use this library to make simple logical judgments. The logical expressions containing specific symbols"-->、|、&、~"：

+ "-->": reasoning,
+ "|": or,
+ "&": and,
+ "~": not.

You can use it in the following ways:

```python
python UI.py
```

![UI1](picture\UI1.png)



 `BaseClass.py` is for object-oriented

+ `SymBol/DesymBol: ` a class or the negation of a class, representing `p or ~p`；
+ `Proposition:` proposition class, representing `p-->q`;
+ `Relation:` relationship class, representing `p|q or p&q`；
+ `LogicalExperssion:` Logical expression class.

You can use it in the following ways:

```python
python BaseClass.py
```

Then there will be the following results:

```python
The original statement is:  ((People-->Die) AND (Socrates-->People))-->((Socrates-->Die))
Convert the original statement into a logical expression: ((a-->b) & (c-->a))-->((c-->b))
The corresponding relationship between original language and logical expression symbols is: {'People': 'a', 'Die': 'b', 'Socrates': 'c'}
The judgment result is: True
```
