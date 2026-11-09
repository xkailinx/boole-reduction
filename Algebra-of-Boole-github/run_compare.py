#!/usr/bin/env python3
"""
Compare Boole reduction implementations with timing.

Examples:
    python run_compare.py                          # run all built-in cases
    python run_compare.py --case syllogism         # one built-in case
    python run_compare.py --case makesample_8      # chain proof n=8
    python run_compare.py --expr "a | ~a"          # custom expression
    python run_compare.py --quick                  # GF(2) only (fast)
    python run_compare.py --list                   # list available cases
"""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from compare_runner import (  # noqa: E402
    compare_expression,
    format_case_table,
    format_summary_table,
    list_cases,
    run_cases,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare Boole reduction implementations with timing."
    )
    parser.add_argument(
        "--case",
        action="append",
        dest="cases",
        metavar="ID",
        help="Built-in case id (repeatable). Use --list to see ids.",
    )
    parser.add_argument(
        "--expr",
        type=str,
        help="Custom logic expression (&, |, ~, (), -->).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List built-in case ids and exit.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only boole_engine GF(2) (skip legacy SymPy implementations).",
    )
    parser.add_argument(
        "--n-minimum",
        type=int,
        default=50,
        help="Partition chunk size for LogicJudgeUpdated (default: 50).",
    )
    args = parser.parse_args()

    if args.list:
        print("Built-in cases:\n")
        for c in list_cases():
            print(f"  {c['case_id']:<20} {c['label']}")
            print(f"    {c['expression'][:70]}{'...' if len(c['expression']) > 70 else ''}")
        return 0

    include_slow = not args.quick
    results = []

    if args.expr:
        results.append(
            compare_expression(
                args.expr.strip(),
                case_id="custom",
                label="Custom expression",
                n_minimum=args.n_minimum,
                include_slow=include_slow,
            )
        )
    elif args.cases:
        results = run_cases(args.cases, n_minimum=args.n_minimum, include_slow=include_slow)
    else:
        # Default: a representative subset + optional full suite hint
        default_ids = [
            "syllogism",
            "tautology",
            "makesample_4",
            "makesample_6",
            "makesample_8",
            "blog_example",
        ]
        if include_slow:
            default_ids.extend(["makesample_10", "makesample_12"])
        results = run_cases(default_ids, n_minimum=args.n_minimum, include_slow=include_slow)

    print("Boole Reduction — Implementation Comparison")
    print("=" * 90)
    if args.quick:
        print("(Quick mode: GF(2) only)\n")
    else:
        print("(Full mode: GF(2) + LogicJudge brute + LogicJudgeUpdated + partition)\n")

    for case in results:
        print(format_case_table(case))

    if len(results) > 1:
        print(format_summary_table(results))

    print("\nFastest on each case is typically boole_engine (GF(2)).")
    print("Legacy LogicJudge / LogicJudgeUpdated use SymPy expand (slower on large inputs).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
