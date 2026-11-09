"""
boole_engine.py — Improved Boole Reduction engine (standalone module).

Implements the Algebra-of-Boole pipeline without modifying existing LogicJudge files:
  logic expression  ->  AST  ->  GF(2) polynomial  ->  canonical form / validity

Key improvements over LogicJudge.py / LogicJudgeUpdated.py:
  - AST parsing with correct precedence (no left-to-right string rewriting)
  - Native GF(2) polynomial arithmetic (no sympy.expand bottleneck)
  - Memoized bottom-up reduction
  - is_valid() fast path for proof checking
  - explain() for step-by-step visualization

Usage:
    from boole_engine import BooleEngine

    engine = BooleEngine()
    result = engine.reduce_full("((a-->b) & (b-->c)) --> (a-->c)")
    print(result.canonical)   # "1"
    print(result.is_valid)    # True
    print(result.elapsed_ms)

    for step in engine.explain("a | ~a"):
        print(step)
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Tuple, Union

import sympy as sp
from sympy.abc import _clash

set(_clash)

# ---------------------------------------------------------------------------
# GF(2) polynomial representation
# ---------------------------------------------------------------------------

Monomial = FrozenSet[str]
Poly = Dict[Monomial, int]

EMPTY: Monomial = frozenset()
ONE: Poly = {EMPTY: 1}
ZERO: Poly = {}


def poly_xor(p: Poly, q: Poly) -> Poly:
    """Addition in GF(2): XOR merge."""
    result = dict(p)
    for m in q:
        if m in result:
            del result[m]
        else:
            result[m] = 1
    return result


def poly_mul(p: Poly, q: Poly) -> Poly:
    """Multiplication: distribute monomial products."""
    if not p or not q:
        return {}
    result: Poly = {}
    for m1 in p:
        for m2 in q:
            m = m1 | m2
            if m in result:
                del result[m]
            else:
                result[m] = 1
    return result


def monomial_to_str(m: Monomial) -> str:
    if not m:
        return "1"
    return "".join(sorted(m))


def poly_to_str(p: Poly) -> str:
    if not p:
        return "0"
    terms = [monomial_to_str(m) for m in sorted(p, key=lambda x: (len(x), sorted(x)))]
    return " + ".join(terms)


def poly_is_one(p: Poly) -> bool:
    return p == ONE


def poly_term_count(p: Poly) -> int:
    return len(p)


# ---------------------------------------------------------------------------
# AST
# ---------------------------------------------------------------------------

@dataclass
class ASTNode:
    op: str
    left: Optional["ASTNode"] = None
    right: Optional["ASTNode"] = None

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


PRECEDENCE = {
    "~": (4, "right"),
    "&": (3, "left"),
    "|": (2, "left"),
    "->": (1, "right"),
    "<->": (0, "right"),
}


def tokenize(expression: str) -> List[Tuple[str, str]]:
    token_spec = [
        ("IFF", r"<->"),
        ("IMPLIES", r"-->"),
        ("IMPLIES_ALT", r"->"),
        ("AND", r"&"),
        ("OR", r"\|"),
        ("NOT", r"~"),
        ("LPAREN", r"\("),
        ("RPAREN", r"\)"),
        ("VAR", r"[A-Za-z][A-Za-z0-9_]*"),
        ("SKIP", r"[ \t]+"),
    ]
    regex = "|".join(f"(?P<{name}>{pat})" for name, pat in token_spec)
    tokens: List[Tuple[str, str]] = []
    for m in re.finditer(regex, expression):
        kind, value = m.lastgroup, m.group()
        if kind == "SKIP":
            continue
        if kind in ("IMPLIES", "IMPLIES_ALT"):
            tokens.append(("OP", "->"))
        elif kind == "IFF":
            tokens.append(("OP", "<->"))
        elif kind == "AND":
            tokens.append(("OP", "&"))
        elif kind == "OR":
            tokens.append(("OP", "|"))
        elif kind == "NOT":
            tokens.append(("OP", "~"))
        elif kind == "LPAREN":
            tokens.append(("LPAREN", "("))
        elif kind == "RPAREN":
            tokens.append(("RPAREN", ")"))
        elif kind == "VAR":
            tokens.append(("VAR", value))
        else:
            raise ValueError(f"Unexpected token: {value}")
    return tokens


def parse_logic(expression: str) -> ASTNode:
    tokens = tokenize(expression)
    if not tokens:
        raise ValueError("Empty expression")

    output: List[ASTNode] = []
    ops: List[str] = []

    def apply_op(op: str) -> None:
        if op == "~":
            if not output:
                raise ValueError("NOT missing operand")
            operand = output.pop()
            output.append(ASTNode("~", left=operand))
        else:
            if len(output) < 2:
                raise ValueError(f"Operator {op} missing operands")
            right = output.pop()
            left = output.pop()
            output.append(ASTNode(op, left=left, right=right))

    i = 0
    while i < len(tokens):
        kind, value = tokens[i]
        if kind == "VAR":
            output.append(ASTNode(value))
        elif kind == "OP" and value == "~":
            ops.append("~")
        elif kind == "OP":
            while ops and ops[-1] != "(":
                top = ops[-1]
                if top not in PRECEDENCE:
                    break
                p_new, assoc_new = PRECEDENCE[value]
                p_top, _ = PRECEDENCE[top]
                if (assoc_new == "left" and p_new <= p_top) or (assoc_new == "right" and p_new < p_top):
                    ops.pop()
                    apply_op(top)
                else:
                    break
            ops.append(value)
        elif kind == "LPAREN":
            ops.append("(")
        elif kind == "RPAREN":
            while ops and ops[-1] != "(":
                apply_op(ops.pop())
            if not ops:
                raise ValueError("Mismatched parentheses")
            ops.pop()
        i += 1

    while ops:
        top = ops.pop()
        if top == "(":
            raise ValueError("Mismatched parentheses")
        apply_op(top)

    if len(output) != 1:
        raise ValueError("Invalid expression")
    return output[0]


# ---------------------------------------------------------------------------
# Logic -> GF(2) encoding (Algebra of Boole rules)
# ---------------------------------------------------------------------------

@dataclass
class Step:
    description: str
    node_repr: str
    boole_str: str
    term_count: int


def ast_to_repr(node: ASTNode) -> str:
    if node.is_leaf:
        return node.op
    if node.op == "~":
        return f"(~{ast_to_repr(node.left)})"
    return f"({ast_to_repr(node.left)} {node.op} {ast_to_repr(node.right)})"


class GF2Encoder:
    """Bottom-up AST -> GF(2) polynomial, with memoization."""

    def __init__(self) -> None:
        self.cache: Dict[int, Poly] = {}
        self.steps: List[Step] = []
        self.record_steps: bool = False

    def encode(self, node: ASTNode) -> Poly:
        key = id(node)
        if key in self.cache:
            return self.cache[key]

        if node.is_leaf:
            p = {frozenset({node.op}): 1}
        elif node.op == "~":
            child = self.encode(node.left)
            p = poly_xor(ONE, child)
        elif node.op == "&":
            left = self.encode(node.left)
            right = self.encode(node.right)
            p = poly_mul(left, right)
        elif node.op == "|":
            left = self.encode(node.left)
            right = self.encode(node.right)
            p = poly_xor(poly_xor(left, right), poly_mul(left, right))
        elif node.op == "->":
            left = self.encode(node.left)
            right = self.encode(node.right)
            p = poly_xor(poly_xor(ONE, left), poly_mul(left, right))
        elif node.op == "<->":
            left = self.encode(node.left)
            right = self.encode(node.right)
            ab = poly_mul(left, right)
            p = poly_xor(poly_xor(poly_xor(ONE, left), right), ab)
        else:
            raise ValueError(f"Unknown operator: {node.op}")

        self.cache[key] = p
        if self.record_steps:
            self.steps.append(
                Step(
                    description=f"Encode {node.op if not node.is_leaf else 'variable'}",
                    node_repr=ast_to_repr(node),
                    boole_str=poly_to_str(p),
                    term_count=poly_term_count(p),
                )
            )
        return p


# ---------------------------------------------------------------------------
# Optional iterative partition (LogicJudgeUpdated-style fallback)
# ---------------------------------------------------------------------------

def logic_to_boole_string(node: ASTNode) -> str:
    """String form matching legacy Logic2algebra output style."""
    if node.is_leaf:
        return node.op
    if node.op == "~":
        return f"(1 + {logic_to_boole_string(node.left)})"
    left = logic_to_boole_string(node.left)
    right = logic_to_boole_string(node.right)
    if node.op == "&":
        return f"({left}{right})"
    if node.op == "|":
        return f"({left} + {right} + {left}{right})"
    if node.op == "->":
        return f"(1 + {left} + {left}{right})"
    if node.op == "<->":
        return f"(1 + {left} + {left}{right} + {right} + {left}{right})"
    raise ValueError(f"Unknown operator: {node.op}")


def cut_string_with_parentheses(s: str, n_minimum: int) -> List[str]:
    result, start, balance = [], 0, 0
    for i, ch in enumerate(s):
        if ch == "(":
            balance += 1
        elif ch == ")":
            balance -= 1
        if balance == 0 and (i - start + 1) >= n_minimum:
            result.append(s[start : i + 1])
            start = i + 1
    if start < len(s):
        result.append(s[start:])
    return result


def _legacy_boolstr_to_poly(string: str) -> Poly:
    """Parse legacy Boole string '(1 + a + ab)(1 + c)' into GF(2) poly."""
    tokens: List[str] = []
    i, n = 0, len(string)

    def is_var_char(ch: str) -> bool:
        return ch.isalpha() or ch == "_"

    while i < n:
        ch = string[i]
        if ch.isspace():
            i += 1
            continue
        if ch == "+":
            tokens.append("+")
            i += 1
        elif ch == "(":
            tokens.append("(")
            i += 1
        elif ch == ")":
            tokens.append(")")
            i += 1
        elif ch == "1" and (i + 1 >= n or not is_var_char(string[i + 1])):
            tokens.append("1")
            i += 1
        elif is_var_char(ch):
            j = i
            while j < n and is_var_char(string[j]):
                j += 1
            tokens.append(string[i:j])
            i = j
        else:
            raise ValueError(f"Unexpected character in Boole string: {ch}")

    def monomial_from_name(name: str) -> Monomial:
        if len(name) == 1:
            return frozenset({name})
        # Legacy single-char vars: "ab" means a*b
        if name.islower() and name.isalpha():
            return frozenset(name)
        return frozenset({name})

    def parse_factor(idx: int) -> Tuple[Poly, int]:
        if idx >= len(tokens):
            raise ValueError("Unexpected end of Boole string")
        tok = tokens[idx]
        if tok == "(":
            poly, idx = parse_sum(idx + 1)
            if idx >= len(tokens) or tokens[idx] != ")":
                raise ValueError("Missing closing parenthesis")
            return poly, idx + 1
        if tok == "1":
            return dict(ONE), idx + 1
        return {monomial_from_name(tok): 1}, idx + 1

    def parse_sum(idx: int) -> Tuple[Poly, int]:
        poly, idx = parse_factor(idx)
        while idx < len(tokens) and tokens[idx] == "+":
            rhs, idx = parse_factor(idx + 1)
            poly = poly_xor(poly, rhs)
        return poly, idx

    def parse_expr(idx: int) -> Tuple[Poly, int]:
        poly, idx = parse_factor(idx)
        while idx < len(tokens) and tokens[idx] not in ("+", ")"):
            factor, idx = parse_factor(idx)
            poly = poly_mul(poly, factor)
        return poly, idx

    poly, end = parse_expr(0)
    if end != len(tokens):
        raise ValueError("Trailing tokens in Boole string")
    return poly


def _reducesymbol(term: str) -> str:
    """Match LogicJudgeUpdated.reducesymbol (strip even coeffs, dedupe vars)."""
    idx = 0
    result = ""
    length = len(term)
    while idx < length and term[idx] == " ":
        idx += 1
    if idx >= length:
        return "1"
    if "1" <= term[idx] <= "9":
        j = idx
        while j < length and "0" <= term[j] <= "9":
            j += 1
        if (int(term[idx:j]) - 0) % 2 == 0:
            return "0"
        idx = j
        while idx < length and term[idx] == " ":
            idx += 1
    if idx >= length:
        return "1"
    while idx < length:
        while idx < length and (term[idx] == "*" or ("0" <= term[idx] <= "9")):
            idx += 1
        if idx >= length:
            break
        ch = term[idx]
        if ch != " ":
            result += ch
        idx += 1
    return result


def _sympy_boole_reduce(symstr: str) -> str:
    """SymPy expand + XOR cancel, matching LogicJudgeUpdated.BooleReduce."""
    expr = sp.sympify(symstr, _clash)
    parts = str(sp.expand(expr)).split("+")
    res: set = set()
    for partstr in parts:
        tempstr = _reducesymbol(partstr)
        if tempstr == "0":
            continue
        if tempstr in res:
            res.remove(tempstr)
        else:
            res.add(tempstr)
    resultlist = sorted(res)
    if not resultlist:
        return ""
    result = ""
    for val in resultlist:
        result += val + " + "
    return result[:-3]


def _reduced_string_to_poly(reduced: str) -> Poly:
    """Parse output of _sympy_boole_reduce / legacy BooleReduce."""
    s = (reduced or "").strip()
    if not s or s == "0":
        return ZERO
    poly: Poly = {}
    for part in s.split("+"):
        t = part.strip()
        if not t:
            continue
        if t == "1":
            poly = poly_xor(poly, ONE)
        else:
            m = frozenset(t) if len(t) == 1 or not t.isalpha() else frozenset(c for c in t if c.isalpha())
            if m in poly:
                del poly[m]
            else:
                poly[m] = 1
    return poly


def reduce_iterative_partition(expression: str, n_minimum: int = 50) -> Poly:
    """
    LogicJudgeUpdated-style chunked reduction on the Boole string.
    Uses SymPy for each chunk (same as LogicJudgeUpdated).
    """
    ast = parse_logic(expression)
    boole_str = logic_to_boole_string(ast)
    chunks = cut_string_with_parentheses(boole_str, n_minimum)
    if not chunks:
        return ZERO

    iterated_str = ""
    iterated_res = ""
    for i, chunk in enumerate(chunks):
        if i == 0:
            iterated_str += chunk
        else:
            iterated_str = f"({iterated_res}){chunk}"
        symstr = Boolstr2symstr(iterated_str)
        iterated_res = _sympy_boole_reduce(symstr)
    return _reduced_string_to_poly(iterated_res)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class ReductionResult:
    expression: str
    boole_string: str
    canonical: str
    is_valid: bool
    term_count: int
    elapsed_ms: float
    method: str
    steps: List[Step] = field(default_factory=list)


class BooleEngine:
    """
    Main entry point for Boole reduction and validity checking.

    Methods:
        reduce_full(expr)     -> canonical GF(2) form
        is_valid(expr)        -> True iff expression reduces to "1"
        explain(expr)         -> list of encoding steps
        compare_methods(expr) -> timing comparison dict
    """

    def __init__(self, default_n_minimum: int = 50) -> None:
        self.default_n_minimum = default_n_minimum

    def _timed(self, fn, *args, **kwargs) -> Tuple[object, float]:
        t0 = time.perf_counter()
        out = fn(*args, **kwargs)
        return out, (time.perf_counter() - t0) * 1000

    def reduce_full(
        self,
        expression: str,
        method: str = "gf2",
        n_minimum: Optional[int] = None,
        record_steps: bool = False,
    ) -> ReductionResult:
        """
        method:
            "gf2"        - native GF(2) bottom-up (recommended)
            "partition"  - iterative chunk strategy from LogicJudgeUpdated
        """
        n_min = n_minimum if n_minimum is not None else self.default_n_minimum
        ast = parse_logic(expression)
        boole_string = logic_to_boole_string(ast)

        if method == "gf2":
            encoder = GF2Encoder()
            encoder.record_steps = record_steps
            poly, elapsed = self._timed(encoder.encode, ast)
            steps = encoder.steps
            method_name = "gf2_bottom_up"
        elif method == "partition":
            poly, elapsed = self._timed(reduce_iterative_partition, expression, n_min)
            steps = []
            method_name = f"partition(n>={n_min})"
        else:
            raise ValueError(f"Unknown method: {method}")

        canonical = poly_to_str(poly)
        return ReductionResult(
            expression=expression,
            boole_string=boole_string,
            canonical=canonical,
            is_valid=poly_is_one(poly),
            term_count=poly_term_count(poly),
            elapsed_ms=elapsed,
            method=method_name,
            steps=steps,
        )

    def is_valid(self, expression: str, method: str = "gf2") -> bool:
        """Fast validity check: True iff reduced form is exactly '1'."""
        return self.reduce_full(expression, method=method).is_valid

    def explain(self, expression: str) -> List[Step]:
        return self.reduce_full(expression, record_steps=True).steps

    def compare_methods(self, expression: str) -> Dict[str, Union[str, float, int, bool]]:
        r_gf2 = self.reduce_full(expression, method="gf2")
        r_part = self.reduce_full(expression, method="partition")
        return {
            "expression": expression,
            "gf2_canonical": r_gf2.canonical,
            "gf2_ms": r_gf2.elapsed_ms,
            "gf2_terms": r_gf2.term_count,
            "gf2_valid": r_gf2.is_valid,
            "partition_canonical": r_part.canonical,
            "partition_ms": r_part.elapsed_ms,
            "partition_terms": r_part.term_count,
            "partition_valid": r_part.is_valid,
            "results_match": r_gf2.canonical == r_part.canonical,
        }


# ---------------------------------------------------------------------------
# Legacy-compatible wrappers (drop-in for BaseClass / UI)
# ---------------------------------------------------------------------------

_engine = BooleEngine()


def Logic2algebra(expression: str) -> str:
    """Compatible with existing Logic2algebra()."""
    return logic_to_boole_string(parse_logic(expression))


def BooleReduce(boole_string: str) -> str:
    """Compatible with existing BooleReduce(); uses SymPy like LogicJudgeUpdated."""
    return _sympy_boole_reduce(Boolstr2symstr(boole_string))


def Boolstr2symstr(string: str) -> str:
    """Kept for compatibility; GF(2) path does not need SymPy strings."""

    def is_symbol(c: str) -> bool:
        return c not in {" ", "+", "(", ")"}

    result, length = "", len(string)
    for idx in range(length):
        c = string[idx]
        result += c
        if is_symbol(c) and idx < length - 1:
            nxt = string[idx + 1]
            if is_symbol(nxt) or nxt == "(":
                result += "*"
        elif c == ")" and idx < length - 1:
            nxt = string[idx + 1]
            if is_symbol(nxt) or nxt == "(":
                result += "*"
    return result


def judge(expression: str) -> bool:
    """Drop-in truth judgment: True iff expression is valid."""
    return _engine.is_valid(expression)


def makesample(n: int) -> str:
    """Same test generator as testeffect.ipynb."""
    s = "("
    for i in range(n - 2):
        s += f"({chr(i + ord('a'))}-->{chr(i + 1 + ord('a'))})&"
    s += f"({chr(n - 2 + ord('a'))}-->{chr(n - 1 + ord('a'))}))"
    s += f"-->(a-->{chr(n - 1 + ord('a'))})"
    return s


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

def _demo() -> None:
    examples = [
        "((a-->b) & (b-->c)) --> (a-->c)",
        "a | ~a",
        makesample(4),
        makesample(8),
    ]
    engine = BooleEngine()
    print("=== Boole Engine Demo ===\n")
    for expr in examples:
        print(f"Expression: {expr}")
        cmp = engine.compare_methods(expr)
        print(f"  GF(2):       {cmp['gf2_canonical']!r}  ({cmp['gf2_ms']:.2f} ms, {cmp['gf2_terms']} terms)")
        print(f"  Partition:   {cmp['partition_canonical']!r}  ({cmp['partition_ms']:.2f} ms, {cmp['partition_terms']} terms)")
        print(f"  Match: {cmp['results_match']}\n")


if __name__ == "__main__":
    _demo()
