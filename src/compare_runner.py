"""
Compare all Boole reduction implementations with timing.

Runners:
  - LogicJudge.py          (original brute-force SymPy)
  - LogicJudgeUpdated.py   (partitioned SymPy, paper algorithm)
  - boole_engine GF(2)     (new native reduction)
  - boole_engine partition (matches LogicJudgeUpdated)
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional

import LogicJudge as lj_brute
import LogicJudgeUpdated as lj_updated
import boole_engine as be


@dataclass
class ImplResult:
    id: str
    name: str
    reduced: Optional[str] = None
    is_valid: bool = False
    elapsed_ms: float = 0.0
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class CaseResult:
    case_id: str
    label: str
    expression: str
    results: List[ImplResult] = field(default_factory=list)
    mode: str = "compare"  # "compare" | "reduce"
    boole_string: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "label": self.label,
            "expression": self.expression,
            "mode": self.mode,
            "boole_string": self.boole_string,
            "results": [asdict(r) for r in self.results],
        }


def _is_valid_legacy(reduced: str) -> bool:
    s = (reduced or "").strip()
    return s == "1"


def _timed_ms(fn: Callable[[], str]) -> tuple[str, float]:
    t0 = time.perf_counter()
    result = fn()
    return result, (time.perf_counter() - t0) * 1000


def run_brute(expression: str) -> ImplResult:
    impl = ImplResult("brute", "LogicJudge.py (brute force)")
    try:
        def work() -> str:
            alg = lj_brute.Logic2algebra(expression)
            return lj_brute.BooleReduce(lj_brute.Boolstr2symstr(alg))

        impl.reduced, impl.elapsed_ms = _timed_ms(work)
        impl.is_valid = _is_valid_legacy(impl.reduced)
    except Exception as exc:  # noqa: BLE001
        impl.error = str(exc)
    return impl


def run_updated(expression: str, n_minimum: int = 50) -> ImplResult:
    impl = ImplResult("updated", f"LogicJudgeUpdated.py (partition n>={n_minimum})")
    try:
        def work() -> str:
            alg = lj_updated.Logic2algebra(expression)
            chunks = lj_updated.cut_string_with_parentheses(alg, n_minimum)
            iterated_str = ""
            iterated_res = ""
            for i, chunk in enumerate(chunks):
                if i == 0:
                    iterated_str += chunk
                else:
                    iterated_str = f"({iterated_res}){chunk}"
                symstr = lj_updated.Boolstr2symstr(iterated_str)
                iterated_res = lj_updated.BooleReduce(symstr)
            return iterated_res

        impl.reduced, impl.elapsed_ms = _timed_ms(work)
        impl.is_valid = _is_valid_legacy(impl.reduced)
    except Exception as exc:  # noqa: BLE001
        impl.error = str(exc)
    return impl


def run_engine_gf2(expression: str) -> ImplResult:
    impl = ImplResult("gf2", "boole_engine (GF(2) — new)")
    try:
        t0 = time.perf_counter()
        r = be.BooleEngine().reduce_full(expression, method="gf2")
        impl.elapsed_ms = (time.perf_counter() - t0) * 1000
        impl.reduced = r.canonical
        impl.is_valid = r.is_valid
    except Exception as exc:  # noqa: BLE001
        impl.error = str(exc)
    return impl


def run_engine_partition(expression: str, n_minimum: int = 50) -> ImplResult:
    impl = ImplResult("partition", f"boole_engine (partition n>={n_minimum})")
    try:
        t0 = time.perf_counter()
        r = be.BooleEngine(default_n_minimum=n_minimum).reduce_full(
            expression, method="partition", n_minimum=n_minimum
        )
        impl.elapsed_ms = (time.perf_counter() - t0) * 1000
        impl.reduced = r.canonical
        impl.is_valid = r.is_valid
    except Exception as exc:  # noqa: BLE001
        impl.error = str(exc)
    return impl


def reduce_expression(
    expression: str,
    case_id: str = "custom",
    label: str = "Custom expression",
) -> CaseResult:
    """Run fastest GF(2) reduction only — returns full canonical form."""
    case = CaseResult(
        case_id=case_id,
        label=label,
        expression=expression,
        mode="reduce",
    )
    try:
        t0 = time.perf_counter()
        r = be.BooleEngine().reduce_full(expression, method="gf2")
        elapsed = (time.perf_counter() - t0) * 1000
        case.boole_string = r.boole_string
        case.results.append(
            ImplResult(
                id="gf2",
                name="boole_engine (GF(2))",
                reduced=r.canonical,
                is_valid=r.is_valid,
                elapsed_ms=elapsed,
            )
        )
    except Exception as exc:  # noqa: BLE001
        case.results.append(
            ImplResult(id="gf2", name="boole_engine (GF(2))", error=str(exc))
        )
    return case


def compare_expression(
    expression: str,
    case_id: str = "custom",
    label: str = "Custom expression",
    n_minimum: int = 50,
    include_slow: bool = True,
) -> CaseResult:
    """Run all implementations on one expression."""
    case = CaseResult(case_id=case_id, label=label, expression=expression, mode="compare")

    gf2 = run_engine_gf2(expression)
    case.results.append(gf2)
    if gf2.ok:
        case.boole_string = be.logic_to_boole_string(be.parse_logic(expression))

    if include_slow:
        case.results.append(run_brute(expression))
        case.results.append(run_updated(expression, n_minimum))
        case.results.append(run_engine_partition(expression, n_minimum))

    return case


# Built-in benchmark cases
BUILTIN_CASES: List[Dict[str, str]] = [
    {
        "case_id": "chain_only",
        "label": "Chain only (reduce, not a proof)",
        "expression": "(a-->b)&(b-->c)&(c-->d)",
    },
    {
        "case_id": "syllogism",
        "label": "Syllogism (transitivity)",
        "expression": "((a-->b) & (b-->c)) --> (a-->c)",
    },
    {
        "case_id": "tautology",
        "label": "Tautology: a OR NOT a",
        "expression": "a | ~a",
    },
    {
        "case_id": "modus_ponens",
        "label": "Modus ponens",
        "expression": "(a & (a --> b)) --> b",
    },
    {
        "case_id": "contradiction",
        "label": "Contradiction (invalid)",
        "expression": "a & ~a",
    },
    {
        "case_id": "blog_example",
        "label": "Blog / paper multi-premise example",
        "expression": "((i-->p) & (m-->a) & (y-->s) & (a-->(~p)) & ((~m)-->(~s))) --> (y-->(~i))",
    },
]

for _n in (3, 4, 5, 6, 7, 8, 10, 12):
    BUILTIN_CASES.append(
        {
            "case_id": f"makesample_{_n}",
            "label": f"Chain proof makesample({_n})",
            "expression": be.makesample(_n),
        }
    )


def list_cases() -> List[Dict[str, str]]:
    return [
        {"case_id": c["case_id"], "label": c["label"], "expression": c["expression"]}
        for c in BUILTIN_CASES
    ]


def run_cases(
    case_ids: Optional[List[str]] = None,
    n_minimum: int = 50,
    include_slow: bool = True,
) -> List[CaseResult]:
    selected = BUILTIN_CASES
    if case_ids:
        ids = set(case_ids)
        selected = [c for c in BUILTIN_CASES if c["case_id"] in ids]

    return [
        compare_expression(
            c["expression"],
            case_id=c["case_id"],
            label=c["label"],
            n_minimum=n_minimum,
            include_slow=include_slow,
        )
        for c in selected
    ]


def _display_reduced(reduced: Optional[str]) -> str:
    if reduced is None or reduced == "":
        return "(empty)"
    if reduced == "0":
        return "0"
    return reduced


def format_reduce_output(case: CaseResult) -> str:
    """Reduce-only mode: print full reduced form (not just tautology)."""
    lines = [
        "",
        f"=== {case.label} ===",
        f"Expression:   {case.expression}",
    ]
    if case.boole_string:
        lines.append(f"Boole form:    {case.boole_string}")
    lines.append("")

    r = case.results[0] if case.results else None
    if not r or r.error:
        lines.append(f"ERROR: {r.error if r else 'no result'}")
        return "\n".join(lines)

    lines.extend(
        [
            "Reduced form:",
            _display_reduced(r.reduced),
            "",
            f"Time:          {r.elapsed_ms:.3f} ms",
            f"Tautology:     {r.is_valid}  (True iff reduced form is exactly 1)",
        ]
    )
    return "\n".join(lines)


def format_case_table(case: CaseResult) -> str:
    lines = [
        "",
        f"=== {case.label} ===",
        f"Expression: {case.expression}",
        "",
    ]
    for r in case.results:
        if r.error:
            lines.extend(
                [
                    f"[{r.name}] ERROR ({r.elapsed_ms:.2f} ms)",
                    f"  {r.error}",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    f"[{r.name}]  {r.elapsed_ms:.2f} ms  |  tautology={r.is_valid}",
                    "Reduced form:",
                    f"  {_display_reduced(r.reduced)}",
                    "",
                ]
            )
    return "\n".join(lines)


def format_summary_table(cases: List[CaseResult]) -> str:
    if not cases:
        return "No cases run."

    impl_names = [r.name for r in cases[0].results]
    header = f"{'Case':<28}" + "".join(f"{n[:18]:>20}" for n in impl_names)
    lines = ["", "=== Timing summary (ms) ===", "", header, "-" * (28 + 20 * len(impl_names))]

    for case in cases:
        row = f"{case.case_id:<28}"
        for r in case.results:
            if r.error:
                cell = "ERR"
            else:
                cell = f"{r.elapsed_ms:.2f}"
            row += f"{cell:>20}"
        lines.append(row)

    return "\n".join(lines)
