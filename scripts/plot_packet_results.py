#!/usr/bin/env python3
"""Export four descriptive packet-study figures from saved, analyzed results.

Run from the repository root after analyze_packet_study.py. This script does
not select policies, remove outliers, or calculate new confidence intervals.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
POLICIES = ["rssi", "load_aware", "app_myopic", "cautious_v1", "session_stay",
            "predictive", "no_dwell", "no_guard", "no_cost", "no_age"]
LABELS = {
    "rssi": "Signal", "load_aware": "Capacity/load", "app_myopic": "App margin",
    "cautious_v1": "Earlier caution", "session_stay": "Session stay",
    "predictive": "Proposed", "no_dwell": "No dwell",
    "no_guard": "No guard", "no_cost": "No cost", "no_age": "No age",
}
SCENARIOS = ["wide_corridor", "short_cells", "reversals", "hidden_hotspot",
             "burst_load", "crowded"]
SCENARIO_LABELS = {
    "wide_corridor": "Wide corridor", "short_cells": "Short cells",
    "reversals": "Reversals", "hidden_hotspot": "Hidden hotspot",
    "burst_load": "Burst load", "crowded": "Crowded",
}
COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#777777",
          "#332288", "#882255", "#44AA99", "#AA7744", "#6699CC"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "<", ">", "h"]
MAIN_POLICIES = ["rssi", "load_aware", "app_myopic", "predictive"]


def read_csv(path):
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"Empty result file: {path}")
    return rows


def number(row, key):
    value = float(row[key])
    if not math.isfinite(value):
        raise ValueError(f"Non-finite {key} in {row}")
    return value


def save_figure(fig, directory, stem):
    paths = []
    for suffix in ("png", "pdf"):
        path = directory / f"{stem}.{suffix}"
        metadata = {"Creator": "plot_packet_results.py"}
        if suffix == "pdf":
            metadata.update({"CreationDate": None, "ModDate": None})
        fig.savefig(path, dpi=300, facecolor="white", metadata=metadata)
        paths.append(path.name)
    plt.close(fig)
    return paths


def check_inputs(policy_rows, scenario_rows, contrast_rows, run_rows):
    summary = {r["policy"]: r for r in policy_rows}
    if len(summary) != len(policy_rows) or set(summary) != set(POLICIES):
        raise ValueError("Policy summary must contain exactly the ten study policies")
    scenario_keys = {(r["scenario"], r["policy"]) for r in scenario_rows}
    expected = {(s, p) for s in SCENARIOS for p in POLICIES}
    if len(scenario_keys) != len(scenario_rows) or scenario_keys != expected:
        raise ValueError("Scenario summary must contain every scenario-policy cell")
    contrasts = [r for r in contrast_rows if r["comparator"] == "app_myopic"
                 and r["metric"] == "call_miss_fraction" and r["scope"] != "all"]
    if len(contrasts) != len(SCENARIOS) or {r["scope"] for r in contrasts} != set(SCENARIOS):
        raise ValueError("Missing or duplicate primary scenario contrast")
    for row in contrasts:
        if number(row, "ci_low") > number(row, "ci_high"):
            raise ValueError("Reversed confidence interval")
    if {r["policy"] for r in run_rows} != set(POLICIES):
        raise ValueError("Raw results must include all ten policies")
    if {r["scenario"] for r in run_rows} != set(SCENARIOS):
        raise ValueError("Raw results must include all six scenarios")
    keys = {(r["scenario"], r["seed"], r["policy"]) for r in run_rows}
    if len(keys) != len(run_rows):
        raise ValueError("Duplicate raw run")
    scenario_seeds = {s: {r["seed"] for r in run_rows if r["scenario"] == s}
                      for s in SCENARIOS}
    seeds = scenario_seeds[SCENARIOS[0]]
    if any(values != seeds for values in scenario_seeds.values()):
        raise ValueError("Unequal seed sets across scenarios")
    if keys != {(s, seed, p) for s in SCENARIOS for seed in seeds for p in POLICIES}:
        raise ValueError("Raw results are not a complete paired grid")
    by_scenario = {(r["scenario"], r["policy"]): r for r in scenario_rows}
    for row in contrasts:
        scenario = row["scope"]
        expected_difference = (number(by_scenario[(scenario, "predictive")], "call_miss_fraction")
                               - number(by_scenario[(scenario, "app_myopic")], "call_miss_fraction"))
        if not math.isclose(number(row, "difference"), expected_difference,
                            rel_tol=1e-8, abs_tol=1e-10):
            raise ValueError(f"Scenario means and contrast differ for {scenario}")
    for policy in POLICIES:
        group = [r for r in run_rows if r["policy"] == policy]
        if len(group) != int(summary[policy]["runs"]):
            raise ValueError(f"Raw and summarized run counts differ for {policy}")
        metrics = {
            "voice_missed_fraction": [number(r, "voice_missed_fraction") for r in group],
            "video_missed_fraction": [1 - number(r, "video_complete_fraction") for r in group],
            "handoffs": [number(r, "handoffs") for r in group],
        }
        metrics["call_miss_fraction"] = [0.5 * (v + f) for v, f in zip(
            metrics["voice_missed_fraction"], metrics["video_missed_fraction"])]
        for metric, values in metrics.items():
            if not math.isclose(sum(values) / len(values),
                                number(summary[policy], metric + "_mean"),
                                rel_tol=1e-8, abs_tol=1e-10):
                raise ValueError(f"Raw and summarized {metric} differ for {policy}")
    return summary, {r["scope"]: r for r in contrasts}


def miss_bars(summary, output):
    fig, ax = plt.subplots(figsize=(10.2, 4.9))
    fig.subplots_adjust(left=.09, right=.99, bottom=.24, top=.85)
    positions = np.arange(len(POLICIES))
    width = .36
    voice = [100 * number(summary[p], "voice_missed_fraction_mean") for p in POLICIES]
    video = [100 * number(summary[p], "video_missed_fraction_mean") for p in POLICIES]
    for shift, values, label, color, hatch in [
        (-width / 2, voice, "Voice packets", "#0072B2", ""),
        (width / 2, video, "Whole video frames", "#E69F00", "///"),
    ]:
        bars = ax.bar(positions + shift, values, width, label=label, color=color,
                      edgecolor="#333333", linewidth=.5, hatch=hatch)
        ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=7)
    ax.set_xticks(positions, [LABELS[p].replace(" ", "\n").replace("/", "/\n") for p in POLICIES])
    ax.set_ylim(0, max(1, max(voice + video) * 1.20))
    ax.set_ylabel("Deadline misses (%)")
    ax.set_title("Voice and video deadline misses across all policies", loc="left", pad=35)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.005), ncol=2,
              frameon=False, borderaxespad=0)
    ax.grid(axis="y", alpha=.2)
    fig.text(.09, .045, "Means across all held-out runs. Each scenario has equal weight.\n"
             "Voice uses packets; video requires a complete frame by its deadline. Synthetic results.",
             fontsize=8.5)
    return save_figure(fig, output, "voice_video_deadline_misses")


def scenario_intervals(contrasts, output):
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    fig.subplots_adjust(left=.19, right=.97, bottom=.24, top=.84)
    means = np.array([100 * number(contrasts[s], "difference") for s in SCENARIOS])
    lows = np.array([100 * number(contrasts[s], "ci_low") for s in SCENARIOS])
    highs = np.array([100 * number(contrasts[s], "ci_high") for s in SCENARIOS])
    y = np.arange(len(SCENARIOS))
    ax.hlines(y, lows, highs, color="#0072B2", linewidth=1.8)
    ax.vlines(lows, y-.07, y+.07, color="#0072B2", linewidth=1.2)
    ax.vlines(highs, y-.07, y+.07, color="#0072B2", linewidth=1.2)
    ax.plot(means, y, "o", color="#0072B2", markersize=6)
    ax.axvline(0, color="#555555", linestyle="--", linewidth=1)
    ax.set_yticks(y, [SCENARIO_LABELS[s] for s in SCENARIOS])
    ax.set_ylim(len(y)-.5, -.5)
    low, high = min(0, min(lows)), max(0, max(highs))
    pad = max(.1, (high-low)*.10)
    ax.set_xlim(low-pad, high+pad)
    ax.set_xlabel("Proposed minus app margin (percentage points)")
    ax.set_title("Primary deadline-miss difference by scenario\n"
                 "Negative favors proposed; positive favors app margin", loc="left", pad=15)
    ax.grid(axis="x", alpha=.2)
    counts = sorted({int(contrasts[s]["paired_worlds"]) for s in SCENARIOS})
    count_text = str(counts[0]) if len(counts) == 1 else "/".join(map(str, counts))
    fig.text(.19, .045, f"{count_text} paired seeds per scenario; saved 95% bootstrap intervals, unadjusted.\n"
             "Primary metric: equal-weight voice/video miss rate. Uncertainty is within the synthetic model.",
             fontsize=8.2)
    return save_figure(fig, output, "scenario_primary_difference")


def handoff_tradeoff(summary, output):
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    fig.subplots_adjust(left=.10, right=.69, bottom=.22, top=.85)
    points = {p: (number(summary[p], "handoffs_mean"),
                  100*number(summary[p], "call_miss_fraction_mean")) for p in POLICIES}
    frontier = []
    for policy, point in sorted(points.items(), key=lambda item: item[1]):
        if not any(q[0] <= point[0] and q[1] <= point[1] and q != point
                   for other, q in points.items() if other != policy):
            frontier.append(point)
    if len(frontier) > 1:
        xs, ys = zip(*sorted(set(frontier)))
        ax.plot(xs, ys, color="#555555", linestyle="--", linewidth=1,
                zorder=1)
    for i, policy in enumerate(POLICIES):
        ax.scatter(*points[policy], marker=MARKERS[i], color=COLORS[i],
                   edgecolors="#222222", linewidths=.45, s=68, zorder=3)
    # All names remain visible even when several policies have nearly equal means.
    order = sorted(POLICIES, key=lambda p: (-points[p][1], points[p][0]))
    for y, policy in zip(np.linspace(.96, .04, len(order)), order):
        i = POLICIES.index(policy)
        ax.annotate("", xy=points[policy], xytext=(1.02, y),
                    textcoords="axes fraction", annotation_clip=False,
                    arrowprops={"arrowstyle": "-", "color": COLORS[i],
                                "lw": .7, "alpha": .75})
        ax.text(1.035, y, LABELS[policy], transform=ax.transAxes,
                fontsize=9.1, va="center", color="#222222")
    max_x = max(x for x, _ in points.values())
    max_y = max(y for _, y in points.values())
    ax.set_xlim(-max(.1, .025*max_x), max(1, max_x*1.12))
    ax.set_ylim(0, max(1, max_y*1.12))
    ax.set_xlabel("Mean handoffs per run")
    ax.set_ylabel("Mean primary deadline-miss rate (%)")
    ax.set_title("Handoff count and deadline-miss tradeoff", loc="left", pad=15)
    ax.grid(alpha=.18)
    fig.text(.10, .045, "Every policy is shown; lower and left are preferable for these two metrics.\n"
             "Dashed line: non-dominated displayed means. This is a descriptive comparison within the model.",
             fontsize=8.5)
    return save_figure(fig, output, "handoff_deadline_tradeoff")


def voice_outage_cdf(run_rows, output):
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    fig.subplots_adjust(left=.11, right=.98, bottom=.24, top=.86)
    styles = ["-", "--", "-.", ":"]
    counts = []
    endpoint = max(number(r, "voice_longest_outage_seconds") for r in run_rows
                   if r["policy"] in MAIN_POLICIES)
    for j, policy in enumerate(MAIN_POLICIES):
        values = sorted(number(r, "voice_longest_outage_seconds")
                        for r in run_rows if r["policy"] == policy)
        if min(values) < 0:
            raise ValueError("Negative longest voice outage")
        counts.append(len(values))
        # Collapse tied durations so markers show the right-continuous CDF,
        # not intermediate ranks on a vertical jump; no observations are removed.
        unique, frequencies = np.unique(values, return_counts=True)
        x = np.concatenate(([0.], unique, [endpoint]))
        y = np.concatenate(([0.], np.cumsum(frequencies) / len(values), [1.]))
        i = POLICIES.index(policy)
        ax.step(x, y, where="post", color=COLORS[i], linestyle=styles[j],
                linewidth=1.8, label=LABELS[policy], marker=MARKERS[i],
                markevery=max(1, len(x)//12), markersize=4)
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Longest voice deadline-miss burst in a run (s)")
    ax.set_ylabel("Fraction of runs at or below this duration")
    ax.set_title("Longest voice deadline-miss bursts across runs", loc="left", pad=15)
    ax.legend(frameon=False, loc="lower right")
    ax.grid(alpha=.18)
    count_text = str(counts[0]) if len(set(counts)) == 1 else "/".join(map(str, counts))
    fig.text(.11, .045, f"Empirical CDF of all {count_text} held-out runs per policy; no runs excluded.\n"
             "Runs share paired seeds and scenarios. This is a descriptive distribution, not measured audio quality.",
             fontsize=8.4)
    return save_figure(fig, output, "longest_voice_outage_cdf")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=ROOT / "results/packet")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    output = args.output_dir or args.input_dir / "figures"
    filenames = ["policy_summary.csv", "scenario_summary.csv", "paired_contrasts.csv", "main_runs.csv"]
    missing = [name for name in filenames if not (args.input_dir / name).is_file()]
    if missing:
        parser.error("Run the packet study and analysis first. Missing: " + ", ".join(missing))
    loaded = [read_csv(args.input_dir / name) for name in filenames]
    summary, contrasts = check_inputs(*loaded)
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.titlesize": 12, "axes.titleweight": "bold",
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.axisbelow": True, "pdf.fonttype": 42,
                         "savefig.bbox": None})
    exported = []
    exported += miss_bars(summary, output)
    exported += scenario_intervals(contrasts, output)
    exported += handoff_tradeoff(summary, output)
    exported += voice_outage_cdf(loaded[3], output)
    manifest = {
        "plot_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "inputs_sha256": {name: hashlib.sha256((args.input_dir/name).read_bytes()).hexdigest()
                          for name in filenames},
        "outputs": exported,
        "primary_metric": "Equal-weight mean of voice packet and whole-video-frame deadline miss fractions",
        "intervals": "Read from paired_contrasts.csv; per-scenario 95% paired bootstrap, unadjusted",
        "selection": "All ten policies and all six scenarios retained; CDF uses four named main methods",
        "interpretation": "Descriptive results and uncertainty within synthetic conditions; no hardware or QoE claim",
    }
    (output / "figure_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Saved {len(exported)} plot files and figure_manifest.json to {output}")


if __name__ == "__main__":
    main()
