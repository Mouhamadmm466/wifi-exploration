#!/usr/bin/env python3
"""Make static research figures from saved CSV results (optional Matplotlib)."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/figures"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "svg.fonttype": "none"})


def read(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    rows = [r for r in read(ROOT / "results/paired_comparisons.csv")
            if r["contrast"] == "proposed_minus_app_myopic"]
    scenarios = ["balanced", "hotspots", "overloaded", "abrupt", "reversal", "short_dwell"]
    names = ["Balanced", "Hotspots", "Overloaded", "Abrupt changes", "Reversals", "Short dwell"]
    ages = [0.0, 2.0, 8.0]
    cmap = LinearSegmentedColormap.from_list("benefit", ["#245c8c", "#f8f8f6", "#ba5425"])
    maxabs = max(abs(float(r["mean_difference_service_deficit"]) * 100) for r in rows)
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8), layout="constrained")
    for row_id, profile in enumerate(["realtime", "bulk"]):
        for col_id, cost in enumerate([0.02, 0.2]):
            ax = axes[row_id, col_id]
            matrix = np.array([[next(float(r["mean_difference_service_deficit"]) * 100
                                    for r in rows if r["scenario"] == s and r["profile"] == profile
                                    and float(r["blackout_seconds"]) == cost
                                    and float(r["telemetry_delay_seconds"]) == age)
                                for age in ages] for s in scenarios])
            picture = ax.imshow(matrix, cmap=cmap, norm=TwoSlopeNorm(vmin=-maxabs, vcenter=0, vmax=maxabs), aspect="auto")
            ax.set_yticks(range(6), names)
            ax.set_xticks(range(3), ["0 s", "2 s", "8 s"])
            ax.set_xlabel("Load-report delivery delay")
            title_profile = "Interactive profile" if profile == "realtime" else "Bulk profile"
            ax.set_title(f"{title_profile}  |  {int(cost * 1000)} ms interruption", weight="bold", pad=11)
            for i in range(6):
                for j in range(3):
                    ax.text(j, i, f"{matrix[i,j]:+.2f}", ha="center", va="center",
                            color="white" if abs(matrix[i,j]) > maxabs * .65 else "#182b3a", fontsize=11)
            for spine in ax.spines.values():
                spine.set_visible(False)
    fig.suptitle("Extra caution helps in some conditions and harms in others\n"
                 "Candidate minus application-aware myopic rule • service deficit, percentage points",
                 fontsize=15, weight="bold")
    colorbar = fig.colorbar(picture, ax=axes, shrink=.83, pad=.03)
    colorbar.set_label("Negative: candidate better   |   Positive: candidate worse")
    fig.supxlabel("40 paired seeds per cell. Synthetic decision model; not measured call quality.\n"
                  "Actual report age also includes up to 0.75 s of reporting-period wait.", fontsize=10)
    for suffix in ("png", "svg"):
        fig.savefig(OUT / f"all_conditions.{suffix}", dpi=180, facecolor="white")
    plt.close(fig)

    comparisons = [r for r in read(ROOT / "results/model_mismatch/paired_block_comparisons.csv")
                   if r["contrast"] == "proposed_minus_app_myopic"]
    order = ["matched", "half_capacity", "uneven_capacity"]
    labels = ["Original capacity model", "True capacity halved", "True capacity differs by AP"]
    means, lows, highs = [], [], []
    for key in order:
        row = next(r for r in comparisons if r["variant"] == key)
        means.append(float(row["mean_difference"]) * 100)
        lows.append(float(row["ci95_low"]) * 100)
        highs.append(float(row["ci95_high"]) * 100)
    fig, ax = plt.subplots(figsize=(9.6, 4.3), layout="constrained")
    y = np.arange(3)
    ax.errorbar(means, y, xerr=[np.array(means) - lows, np.array(highs) - means],
                fmt="o", color="#245c8c", ecolor="#245c8c", capsize=5, markersize=8)
    ax.axvline(0, color="#666666", linestyle="--", linewidth=1)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_ylim(2.6, -.6)
    ax.grid(axis="x", alpha=.18)
    ax.set_xlabel("Candidate minus myopic service deficit (percentage points); lower is better")
    ax.set_title("A small benefit survives two capacity-error tests\n"
                 "Exploratory paired 95% intervals • fixed parameters", loc="left", weight="bold", pad=15)
    fig.supxlabel("20 seed blocks, each averaged across 16 settings. Review-added diagnostic.\n"
                  "Candidate estimates unchanged; serving quality remains ideally known.", fontsize=9)
    for suffix in ("png", "svg"):
        fig.savefig(OUT / f"model_mismatch.{suffix}", dpi=180, facecolor="white")
    plt.close(fig)
    print(f"Saved figures in {OUT}")


if __name__ == "__main__":
    main()
