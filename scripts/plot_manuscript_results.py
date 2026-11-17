#!/usr/bin/env python3
"""Generate the manuscript's aggregate sensitivity figure from retained CSVs."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results" / "summary.csv"
OUTPUT = ROOT / "overleaf" / "figures" / "sensitivity.png"


def load_rows():
    with SUMMARY.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main():
    rows = load_rows()
    policies = ["advertisement", "on_demand", "artifact_only", "slot_only", "joint_reservation"]
    labels = ["Advert.", "On-demand", "Artifact", "Slot", "Joint"]
    colors = ["#8c8c8c", "#4c78a8", "#72b7b2", "#f2cf5b", "#1b4f72"]

    stress = [
        row for row in rows
        if row["dispatch_delay_ms"] == "30.0"
        and row["eviction_rate_per_s"] == "8.0"
        and row["competing_load"] == "0.75"
        and row["reservation_ttl_ms"] == "50.0"
    ]
    by_policy = {row["policy"]: row for row in stress}

    ttl_rows = [
        row for row in rows
        if row["policy"] == "joint_reservation"
        and row["dispatch_delay_ms"] == "30.0"
        and row["eviction_rate_per_s"] == "8.0"
        and row["competing_load"] == "0.75"
    ]
    ttl_rows.sort(key=lambda row: float(row["reservation_ttl_ms"]))

    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.55))
    deadline = [100 * float(by_policy[p]["deadline_satisfaction_mean"]) for p in policies]
    ci = [100 * float(by_policy[p]["deadline_satisfaction_ci95"]) for p in policies]
    axes[0].bar(labels, deadline, yerr=ci, capsize=2, color=colors, edgecolor="black", linewidth=0.4)
    axes[0].set_ylabel("Deadline satisfaction (%)")
    axes[0].set_ylim(0, 100)
    axes[0].tick_params(axis="x", rotation=25)
    axes[0].grid(axis="y", alpha=0.25)

    ttl = [float(row["reservation_ttl_ms"]) for row in ttl_rows]
    refusal = [100 * float(row["refusal_rate_mean"]) for row in ttl_rows]
    deadline_ttl = [100 * float(row["deadline_satisfaction_mean"]) for row in ttl_rows]
    axes[1].plot(ttl, deadline_ttl, marker="o", linewidth=1.8, label="Deadline met")
    axes[1].plot(ttl, refusal, marker="s", linewidth=1.8, label="Refusal")
    axes[1].axvline(30, color="black", linestyle="--", linewidth=0.8, label="Dispatch delay")
    axes[1].set_xlabel("Reservation lifetime (ms)")
    axes[1].set_ylabel("Rate (%)")
    axes[1].set_xticks(ttl)
    axes[1].set_ylim(0, 100)
    axes[1].grid(alpha=0.25)
    axes[1].legend(fontsize=7, frameon=False)

    fig.tight_layout(pad=0.8)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
