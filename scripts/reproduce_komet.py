#!/usr/bin/env python3
"""Recalculate Komet §8.1 metrics from the authors' released CSV files."""

from __future__ import annotations

import csv
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "baseline" / "komet" / "scheduling" / "results"

PAPER = {
    "minmax": (4.98, 16),
    "one2one-0.1": (4.99, 12),
    "one2one-0.25": (5.22, 9),
    "one2one-abs-500": (5.04, 12),
}
FILES = {
    "minmax": "simple-minmax-False.csv",
    "one2one-0.1": "simple-one2one-0.1.csv",
    "one2one-0.25": "simple-one2one-0.25.csv",
    "one2one-abs-500": "simple-one2one-abs-500.csv",
}


def calculate(path: Path) -> tuple[float, int]:
    with path.open() as f:
        rows = list(csv.DictReader(f))
    rtts_ms = [float(r["distance"]) * 2 / 1000 for r in rows]
    migrations = sum(
        rows[i]["satellite"] != rows[i - 1]["satellite"]
        for i in range(1, len(rows))
    )
    return statistics.mean(rtts_ms), migrations


def main() -> None:
    out = ROOT / "results" / "komet_reproduction.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, filename in FILES.items():
        reproduced_rtt, reproduced_migrations = calculate(RESULTS / filename)
        paper_rtt, paper_migrations = PAPER[name]
        rows.append({
            "strategy": name,
            "paper_mean_rtt_ms": paper_rtt,
            "reproduced_mean_rtt_ms": reproduced_rtt,
            "rtt_difference_ms": reproduced_rtt - paper_rtt,
            "paper_migrations": paper_migrations,
            "reproduced_migrations": reproduced_migrations,
            "migration_difference": reproduced_migrations - paper_migrations,
        })
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(row)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
