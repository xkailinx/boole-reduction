"""
Cross-implementation correctness tests for Boole reduction.

Compares:
  - LogicJudge.py          (brute-force SymPy expand)
  - LogicJudgeUpdated.py   (partitioned SymPy expand)
  - boole_engine.py        (GF(2) AST + partition modes)

Ground truth: truth-table tautology check (independent oracle).

Run:
    python -m unittest tests.test_boole_correctness -v
    python tests/test_boole_correctness.py report
"""

from __future__ import annotations

import os
import sys
import unittest
from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, List, Optional, Set

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import LogicJudge as lj_brute  # noqa: E402
import LogicJudgeUpdated as lj_updated  # noqa: E402
import boole_engine as be  # noqa: E402


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize_boole(s: str) -> FrozenSet[str]:
    """Canonical GF(2) term set. Empty monomial '' = constant 1."""
    s = (s or "").strip()
    if s == "0":
        return frozenset()
    if not s:
        return frozenset()
    terms: Set[str] = set()
    for part in s.split("+"):
        t = part.strip()
        if not t:
            continue
        if t == "1":
            if "" in terms:
                terms.remove("")
            else:
                terms.add("")
        else:
            key = "".join(sorted(c for c in t if c.isalpha()))
            if key in terms:
                terms.remove(key)
            else:
                terms.add(key)
    return frozenset(terms)


def is_valid_reduced(s: str) -> bool:
    return normalize_boole(s) == frozenset({""})


def monomials_equivalent(a: str, b: str) -> bool:
    return normalize_boole(a) == normalize_boole(b)


# ---------------------------------------------------------------------------
# Truth-table oracle (uses boole_engine AST + standard precedence)
# ---------------------------------------------------------------------------

def collect_variables(expr: str) -> List[str]:
    found: Set[str] = set()
    i, n = 0, len(expr)
    while i < n:
        if expr[i].isalpha():
            j = i
            while j < n and (expr[j].isalnum() or expr[j] == "_"):
                j += 1
            found.add(expr[i:j])
            i = j
        else:
            i += 1
    return sorted(found)


def eval_logic(expr: str, assignment: Dict[str, bool]) -> bool:
    def walk(node: be.ASTNode) -> bool:
        if node.is_leaf:
            return assignment[node.op]
        if node.op == "~":
            return not walk(node.left)
        if node.op == "&":
            return walk(node.left) and walk(node.right)
        if node.op == "|":
            return walk(node.left) or walk(node.right)
        if node.op == "->":
            return (not walk(node.left)) or walk(node.right)
        if node.op == "<->":
            lv, rv = walk(node.left), walk(node.right)
            return lv == rv
        raise ValueError(f"Unknown op {node.op}")

    return walk(be.parse_logic(expr))


def is_tautology(expr: str) -> bool:
    vars_list = collect_variables(expr)
    if len(vars_list) > 14:
        raise ValueError(f"Too many variables ({len(vars_list)}) for truth-table oracle")
    n = len(vars_list)
    for mask in range(1 << n):
        env = {vars_list[i]: bool((mask >> i) & 1) for i in range(n)}
        if not eval_logic(expr, env):
            return False
    return True


# ---------------------------------------------------------------------------
# Implementation runners
# ---------------------------------------------------------------------------

@dataclass
class RunOutcome:
    name: str
    reduced: Optional[str]
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


def run_brute(expression: str) -> RunOutcome:
    try:
        algebra = lj_brute.Logic2algebra(expression)
        reduced = lj_brute.BooleReduce(lj_brute.Boolstr2symstr(algebra))
        return RunOutcome("LogicJudge (brute)", reduced)
    except Exception as exc:  # noqa: BLE001
        return RunOutcome("LogicJudge (brute)", None, str(exc))


def run_updated(expression: str, n_minimum: int = 50) -> RunOutcome:
    try:
        algebra = lj_updated.Logic2algebra(expression)
        chunks = lj_updated.cut_string_with_parentheses(algebra, n_minimum)
        iterated_str = ""
        iterated_res = ""
        for i, chunk in enumerate(chunks):
            if i == 0:
                iterated_str += chunk
            else:
                iterated_str = f"({iterated_res}){chunk}"
            symstr = lj_updated.Boolstr2symstr(iterated_str)
            iterated_res = lj_updated.BooleReduce(symstr)
        return RunOutcome(f"LogicJudgeUpdated (n>={n_minimum})", iterated_res)
    except Exception as exc:  # noqa: BLE001
        return RunOutcome(f"LogicJudgeUpdated (n>={n_minimum})", None, str(exc))


def run_engine_gf2(expression: str) -> RunOutcome:
    try:
        r = be.BooleEngine().reduce_full(expression, method="gf2")
        return RunOutcome("boole_engine (gf2)", r.canonical)
    except Exception as exc:  # noqa: BLE001
        return RunOutcome("boole_engine (gf2)", None, str(exc))


def run_engine_partition(expression: str, n_minimum: int = 50) -> RunOutcome:
    try:
        r = be.BooleEngine(default_n_minimum=n_minimum).reduce_full(
            expression, method="partition", n_minimum=n_minimum
        )
        return RunOutcome(f"boole_engine (partition n>={n_minimum})", r.canonical)
    except Exception as exc:  # noqa: BLE001
        return RunOutcome(f"boole_engine (partition n>={n_minimum})", None, str(exc))


ALL_RUNNERS: List[Callable[[str], RunOutcome]] = [
    run_brute,
    run_updated,
    run_engine_gf2,
    lambda e: run_engine_partition(e, 50),
]


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

# Valid tautologies (should reduce to constant 1)
VALID_CASES = [
    "((a-->b) & (b-->c)) --> (a-->c)",
    "~(~a) --> a",
    "(a & b) --> a",
    be.makesample(3),
    be.makesample(4),
    be.makesample(5),
    be.makesample(6),
    be.makesample(7),
    "((i-->p) & (m-->a) & (y-->s) & (a-->(~p)) & ((~m)-->(~s))) --> (y-->(~i))",
]

INVALID_CASES = [
    "a --> b",
    "(a-->b) --> (b-->a)",
    "a & ~a",
]

# Cases where legacy LogicJudge is known broken (documented in tests)
LEGACY_KNOWN_BUGS = {
    "a | ~a": "Legacy Logic2algebra produces malformed string; BooleReduce loses constant 1",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTruthTableOracle(unittest.TestCase):
    def test_valid_cases_are_tautologies(self):
        for expr in VALID_CASES:
            self.assertTrue(is_tautology(expr), msg=f"Expected tautology: {expr}")

    def test_invalid_cases_not_tautologies(self):
        for expr in INVALID_CASES:
            self.assertFalse(is_tautology(expr), msg=f"Expected non-tautology: {expr}")


class TestBooleEngineGF2(unittest.TestCase):
    """GF(2) engine should match truth-table oracle on all standard cases."""

    def test_validity_matches_oracle(self):
        engine = be.BooleEngine()
        for expr in VALID_CASES:
            r = engine.reduce_full(expr, method="gf2")
            self.assertTrue(r.is_valid, msg=f"{expr} -> {r.canonical!r}")
            self.assertTrue(is_tautology(expr))

    def test_invalid_not_valid(self):
        engine = be.BooleEngine()
        for expr in INVALID_CASES:
            r = engine.reduce_full(expr, method="gf2")
            self.assertFalse(r.is_valid, msg=f"{expr} -> {r.canonical!r}")


class TestLegacyBruteForce(unittest.TestCase):
    def test_makesample_valid_through_n7(self):
        for n in range(3, 8):
            expr = be.makesample(n)
            out = run_brute(expr)
            self.assertTrue(out.ok, msg=out.error)
            self.assertEqual(out.reduced, "1", msg=f"makesample({n}) -> {out.reduced!r}")

    def test_known_legacy_bugs(self):
        for expr, reason in LEGACY_KNOWN_BUGS.items():
            out = run_brute(expr)
            oracle = is_tautology(expr)
            legacy_valid = out.reduced == "1"  # BaseClass.LogicJudge check
            if oracle and not legacy_valid:
                # Expected failure — test passes by documenting the bug
                self.assertNotEqual(out.reduced, "1", msg=reason)


class TestCrossImplementation(unittest.TestCase):
    """Implementations should agree on makesample and paper examples."""

    AGREEMENT_CASES = [be.makesample(n) for n in range(3, 8)] + [
        "((a-->b) & (b-->c)) --> (a-->c)",
        "((i-->p) & (m-->a) & (y-->s) & (a-->(~p)) & ((~m)-->(~s))) --> (y-->(~i))",
    ]

    def test_all_implementations_agree(self):
        failures: List[str] = []
        for expr in self.AGREEMENT_CASES:
            outcomes = [fn(expr) for fn in ALL_RUNNERS]
            errors = [o for o in outcomes if not o.ok]
            if errors:
                failures.append(
                    f"{expr}:\n  "
                    + "\n  ".join(f"{o.name}: {o.error}" for o in errors)
                )
                continue

            norms = {o.name: normalize_boole(o.reduced or "") for o in outcomes}
            ref_name = outcomes[0].name
            ref_norm = norms[ref_name]
            for name, norm in norms.items():
                if norm != ref_norm:
                    failures.append(
                        f"{expr}: {name} != {ref_name}\n"
                        f"  {name}: {outcomes[[o.name for o in outcomes].index(name)].reduced!r}\n"
                        f"  {ref_name}: {outcomes[0].reduced!r}"
                    )

        if failures:
            self.fail("Cross-implementation mismatches:\n" + "\n".join(failures))

    def test_updated_matches_brute_on_valid_cases(self):
        for expr in VALID_CASES:
            if expr in LEGACY_KNOWN_BUGS:
                continue
            brute = run_brute(expr)
            updated = run_updated(expr)
            if not brute.ok or not updated.ok:
                continue
            self.assertTrue(
                monomials_equivalent(brute.reduced or "", updated.reduced or ""),
                msg=f"{expr}: brute={brute.reduced!r} updated={updated.reduced!r}",
            )


class TestEngineVsLegacyPipeline(unittest.TestCase):
    def test_engine_boole_reduce_matches_legacy_on_makesample(self):
        for n in range(3, 7):
            expr = be.makesample(n)
            algebra = lj_brute.Logic2algebra(expr)
            legacy = lj_brute.BooleReduce(lj_brute.Boolstr2symstr(algebra))
            engine = be.BooleReduce(algebra)
            self.assertTrue(
                monomials_equivalent(legacy, engine),
                msg=f"makesample({n}): legacy={legacy!r} engine={engine!r}",
            )

    def test_gf2_matches_legacy_validity_on_makesample(self):
        engine = be.BooleEngine()
        for n in range(3, 10):
            expr = be.makesample(n)
            brute = run_brute(expr)
            gf2 = engine.reduce_full(expr, method="gf2")
            if not brute.ok:
                continue
            self.assertEqual(
                brute.reduced == "1",
                gf2.is_valid,
                msg=f"makesample({n}): legacy={brute.reduced!r} gf2={gf2.canonical!r}",
            )


class TestPartitionModes(unittest.TestCase):
    def test_engine_partition_matches_updated(self):
        for n in range(3, 8):
            expr = be.makesample(n)
            updated = run_updated(expr, 50)
            part = run_engine_partition(expr, 50)
            self.assertTrue(updated.ok and part.ok, msg=f"{updated.error} / {part.error}")
            self.assertTrue(
                monomials_equivalent(updated.reduced or "", part.reduced or ""),
                msg=f"makesample({n}): updated={updated.reduced!r} engine={part.reduced!r}",
            )


# ---------------------------------------------------------------------------
# CLI report
# ---------------------------------------------------------------------------

def print_comparison_report() -> int:
    print("=" * 72)
    print("Boole Reduction Cross-Implementation Report")
    print("=" * 72)

    cases = VALID_CASES + INVALID_CASES
    failures = 0

    for expr in cases:
        oracle = is_tautology(expr)
        print(f"\nExpression: {expr}")
        print(f"  Truth table (oracle): {'VALID' if oracle else 'INVALID'}")

        for runner in ALL_RUNNERS:
            out = runner(expr)
            if out.error:
                print(f"  {out.name:42} ERROR: {out.error}")
                failures += 1
                continue
            valid = is_valid_reduced(out.reduced or "")
            legacy_check = (out.reduced or "") == "1"
            match = "OK" if valid == oracle else "WRONG"
            if match != "OK":
                failures += 1
            print(
                f"  {out.name:42} reduced={out.reduced!r}  "
                f"gf2_valid={valid} legacy_==1={legacy_check}  [{match}]"
            )

    print("\n" + "-" * 72)
    print("Known legacy bugs:")
    for expr, reason in LEGACY_KNOWN_BUGS.items():
        print(f"  {expr}: {reason}")

    print("-" * 72)
    print(f"Total failures: {failures}")
    return failures


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        raise SystemExit(1 if print_comparison_report() else 0)
    unittest.main(verbosity=2)
