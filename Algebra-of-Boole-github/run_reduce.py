#!/usr/bin/env python3
"""
Run GF(2) Boole reduction only (fastest) — prints full reduced form.

Examples:
    python run_reduce.py --expr "(a-->b)&(b-->c)&(c-->d)"
    python run_reduce.py --case syllogism
    python run_reduce.py --list
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
    BUILTIN_CASES,
    format_reduce_output,
    list_cases,
    reduce_expression,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GF(2) Boole reduction only — prints full canonical form."
    )
    parser.add_argument("--case", dest="case_id", help="Built-in case id")
    parser.add_argument("--expr", type=str, help="Custom logic expression")
    parser.add_argument("--list", action="store_true", help="List built-in cases")
    args = parser.parse_args()

    if args.list:
        for c in list_cases():
            print(f"  {c['case_id']:<20} {c['label']}")
        return 0

    if args.expr:
        case = reduce_expression(args.expr.strip(), label="Custom expression")
    elif args.case_id:
        match = next((c for c in BUILTIN_CASES if c["case_id"] == args.case_id), None)
        if not match:
            print(f"Unknown case: {args.case_id}", file=sys.stderr)
            return 1
        case = reduce_expression(
            match["expression"],
            case_id=match["case_id"],
            label=match["label"],
        )
    else:
        parser.print_help()
        return 1

    print("Boole Reduction — GF(2) reduce-only mode")
    print(format_reduce_output(case))
    return 0 if case.results and case.results[0].ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
