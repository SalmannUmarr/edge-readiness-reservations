#!/usr/bin/env python3
"""Run the frozen experiment matrix and write raw plus summarized CSVs."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from readiness_reservations.simulator import Config, run_many  # noqa: E402


def ci95(values: list[float]) -> float:
    return 1.96 * statistics.stdev(values) / math.sqrt(len(values))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=int, default=1000)
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    configs = [
        Config(tasks=args.tasks, dispatch_delay_ms=delay, eviction_rate_per_s=churn,
               competing_load=load, reservation_ttl_ms=ttl)
        for delay in (10.0, 30.0)
        for churn in (2.0, 8.0)
        for load in (0.35, 0.75)
        for ttl in (20.0, 50.0, 100.0)
    ]
    rows = run_many(configs, range(1, args.seeds + 1))
    args.output.mkdir(parents=True, exist_ok=True)
    raw = args.output / "raw_results.csv"
    with raw.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    metrics = ("deadline_satisfaction", "refusal_rate", "fallback_rate",
               "mean_latency_ms", "p95_latency_ms", "control_messages",
               "pinned_mb_seconds", "unused_reserved_slot_seconds")
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        key = (row["policy"], row["dispatch_delay_ms"], row["eviction_rate_per_s"],
               row["competing_load"], row["reservation_ttl_ms"])
        groups.setdefault(key, []).append(row)
    summary_rows = []
    for key, group in sorted(groups.items()):
        out = dict(zip(("policy", "dispatch_delay_ms", "eviction_rate_per_s",
                        "competing_load", "reservation_ttl_ms"), key))
        for metric in metrics:
            vals = [float(r[metric]) for r in group]
            out[f"{metric}_mean"] = statistics.mean(vals)
            out[f"{metric}_ci95"] = ci95(vals)
        summary_rows.append(out)
    summary = args.output / "summary.csv"
    with summary.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"wrote {len(rows)} raw runs to {raw}")
    print(f"wrote {len(summary_rows)} aggregate rows to {summary}")


if __name__ == "__main__":
    main()
