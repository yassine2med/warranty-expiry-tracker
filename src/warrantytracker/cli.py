"""Command line entry: python -m warrantytracker warranties.csv --as-of 2026-11-19"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date

from .tracker import classify, load_warranties


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    parser = argparse.ArgumentParser(prog="warrantytracker", description="Warranty expiry report")
    parser.add_argument("csv", help="warranties CSV")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today(), help="report date, YYYY-MM-DD")
    parser.add_argument("--within", type=int, default=90, help="days ahead that count as expiring (default 90)")
    parser.add_argument("--out", help="write the expiring and expired rows to this CSV")
    args = parser.parse_args(argv)
    if args.within < 0:
        print("error: --within cannot be negative", file=sys.stderr)
        return 1
    try:
        groups = classify(load_warranties(args.csv), args.as_of, args.within)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Warranty report as of {args.as_of} (expiring = ends within {args.within} days)")
    for label in ("expiring", "expired", "active"):
        items = groups[label]
        print(f"\n{label.upper()} ({len(items)})")
        for w in items:
            days = (w.end - args.as_of).days
            n = abs(days)
            unit = "day" if n == 1 else "days"
            when = f"{n} {unit} left" if days >= 0 else f"{n} {unit} ago"
            print(f"  {w.end}  {w.asset:<26} {w.vendor:<18} {when}")
    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["asset", "vendor", "end_date", "status"])
            for label in ("expiring", "expired"):
                writer.writerows([w.asset, w.vendor, w.end, label] for w in groups[label])
        print(f"\nwrote {args.out}")
    return 0
