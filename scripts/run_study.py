#!/usr/bin/env python3
"""Run the bounded exploratory study with Python's standard library only."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import platform
import random
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from roaming import POLICIES, Parameters, make_trace, prepare, run


def write_csv(path, rows):
    rows = list(rows)
    if not rows:
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def contexts(config, seeds):
    for scenario, seed in itertools.product(config["scenarios"], seeds):
        trace = make_trace(config, scenario, seed)
        for profile, age in itertools.product(config["profiles"], config["telemetry_delays_seconds"]):
            yield scenario, seed, profile, age, prepare(config, trace, profile, age)


def pilot(config, out):
    variants = []
    for value in config["rssi_hysteresis_grid_db"]:
        variants.append((f"rssi_hysteresis_{value}", "rssi", Parameters(rssi_hysteresis_db=value)))
    for value in config["load_relative_margin_grid"]:
        variants.append((f"load_margin_{value}", "load_aware", Parameters(load_relative_margin=value)))
    for horizon, penalty in itertools.product(config["planning_horizon_grid_seconds"], config["age_penalty_grid"]):
        variants.append((f"candidate_horizon_{horizon}_penalty_{penalty}", "proposed",
                         Parameters(horizon_seconds=horizon, age_penalty=penalty)))
    sums = {name: [0.0, 0] for name, _, _ in variants}
    rows = []
    for scenario, seed, profile, age, prepared in contexts(config, config["pilot_seeds"]):
        for blackout in config["blackout_seconds"]:
            for name, policy, params in variants:
                metrics = run(prepared, config, policy, params, blackout)
                sums[name][0] += metrics["service_deficit"]
                sums[name][1] += 1
                rows.append(dict(scenario=scenario, profile=profile, telemetry_delay_seconds=age,
                                 blackout_seconds=blackout, seed=seed, variant=name,
                                 service_deficit=metrics["service_deficit"], handoffs=metrics["handoffs"]))
    write_csv(out / "pilot_seed_metrics.csv", rows)
    summary = [dict(variant=name, policy=policy, mean_service_deficit=sums[name][0] / sums[name][1],
                    runs=sums[name][1], **asdict(params)) for name, policy, params in variants]
    write_csv(out / "pilot_selection.csv", summary)
    best = {policy: min((row for row in summary if row["policy"] == policy),
                        key=lambda row: (row["mean_service_deficit"], row["variant"]))
            for policy in ("rssi", "load_aware", "proposed")}
    chosen = Parameters(rssi_hysteresis_db=best["rssi"]["rssi_hysteresis_db"],
                        load_relative_margin=best["load_aware"]["load_relative_margin"],
                        horizon_seconds=best["proposed"]["horizon_seconds"],
                        age_penalty=best["proposed"]["age_penalty"])
    # This record is written before any evaluation seed is run.
    selection = {"parameters": asdict(chosen), "pilot_seeds": config["pilot_seeds"],
                 "rule": "Lowest equal-cell mean service deficit on pilot seeds only; lexicographic tie break.",
                 "caution": "Synthetic within-model tuning. Application-myopic margin is fixed, not tuned.",
                 "frozen_at_utc": datetime.now(timezone.utc).isoformat()}
    (out / "selected_parameters.json").write_text(json.dumps(selection, indent=2) + "\n")
    return chosen


def evaluate(config, params, out):
    rows = []
    for scenario, seed, profile, age, prepared in contexts(config, config["evaluation_seeds"]):
        for blackout, policy in itertools.product(config["blackout_seconds"], POLICIES):
            rows.append(dict(scenario=scenario, profile=profile, blackout_seconds=blackout,
                             telemetry_delay_seconds=age, seed=seed, policy=policy,
                             **run(prepared, config, policy, params, blackout)))
    write_csv(out / "seed_metrics.csv", rows)
    return rows


def quantile(sorted_values, p):
    index = (len(sorted_values) - 1) * p
    low = int(index)
    high = min(low + 1, len(sorted_values) - 1)
    return sorted_values[low] * (high - index) + sorted_values[high] * (index - low) if low != high else sorted_values[low]


def summarize(config, rows, out):
    keys = ("scenario", "profile", "blackout_seconds", "telemetry_delay_seconds")
    metrics = ("service_deficit", "unserved_fraction", "delivered_mbps", "handoffs", "pingpong",
               "blackout_seconds_total", "blackout_fraction", "delivered_weighted_rtt_ms")
    groups = {}
    for row in rows:
        cell = tuple(row[key] for key in keys)
        groups.setdefault(cell, {}).setdefault(row["policy"], {})[row["seed"]] = row
    aggregate, comparisons = [], []
    rng = random.Random(config["bootstrap_seed"])
    for cell, policies in sorted(groups.items()):
        for policy, by_seed in policies.items():
            row = dict(zip(keys, cell), policy=policy, n_seeds=len(by_seed))
            for metric in metrics:
                values = [sample[metric] for sample in by_seed.values()]
                row["mean_" + metric] = statistics.fmean(values)
                row["sd_" + metric] = statistics.stdev(values)
            aggregate.append(row)
        seeds = sorted(policies["proposed"])
        # Resample whole paired seed runs, never individual time steps.
        draws = [[rng.randrange(len(seeds)) for _ in seeds] for _ in range(config["bootstrap_replicates"])]
        for comparator in POLICIES:
            if comparator == "proposed":
                continue
            result = dict(zip(keys, cell), contrast="proposed_minus_" + comparator,
                          n_seed_pairs=len(seeds))
            for metric in ("service_deficit", "handoffs"):
                differences = [policies["proposed"][seed][metric] - policies[comparator][seed][metric] for seed in seeds]
                samples = sorted(sum(differences[index] for index in draw) / len(seeds) for draw in draws)
                result["mean_difference_" + metric] = statistics.fmean(differences)
                result["ci95_low_" + metric] = quantile(samples, 0.025)
                result["ci95_high_" + metric] = quantile(samples, 0.975)
            comparisons.append(result)
    write_csv(out / "cell_summary.csv", aggregate)
    write_csv(out / "paired_comparisons.csv", comparisons)
    overview = []
    for policy in POLICIES:
        selected = [row for row in rows if row["policy"] == policy]
        overview.append(dict(policy=policy, runs=len(selected),
                             **{"mean_" + metric: statistics.fmean(row[metric] for row in selected) for metric in metrics}))
    write_csv(out / "overall_descriptive.csv", overview)
    by_scenario = []
    for scenario, policy in itertools.product(config["scenarios"], POLICIES):
        selected = [row for row in rows if row["scenario"] == scenario and row["policy"] == policy]
        by_scenario.append(dict(scenario=scenario, policy=policy, runs=len(selected),
                                **{"mean_" + metric: statistics.fmean(row[metric] for row in selected) for metric in metrics}))
    write_csv(out / "scenario_descriptive.csv", by_scenario)
    return overview


def sensitivity(config, params, out):
    # A declared secondary check, not an opportunity to choose new parameters.
    rows = []
    age, blackout = max(config["telemetry_delays_seconds"]), max(config["blackout_seconds"])
    for scenario, seed in itertools.product(config["scenarios"], config["evaluation_seeds"]):
        trace = make_trace(config, scenario, seed)
        for profile in config["profiles"]:
            prepared = prepare(config, trace, profile, age)
            for horizon in config["planning_horizon_grid_seconds"]:
                variant = Parameters(params.rssi_hysteresis_db, params.load_relative_margin, horizon, params.age_penalty)
                rows.append(dict(scenario=scenario, profile=profile, seed=seed, horizon_seconds=horizon,
                                 telemetry_delay_seconds=age, blackout_seconds=blackout,
                                 **run(prepared, config, "proposed", variant, blackout)))
    write_csv(out / "horizon_sensitivity.csv", rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/study.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if set(config["pilot_seeds"]) & set(config["evaluation_seeds"]):
        raise ValueError("Pilot and evaluation seeds overlap")
    args.output.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    started = datetime.now(timezone.utc).isoformat()
    print("Running pilot selection on separate synthetic seeds...", flush=True)
    params = pilot(config, args.output)
    print("Frozen parameters:", asdict(params), flush=True)
    print("Running evaluation traces...", flush=True)
    rows = evaluate(config, params, args.output)
    print("Computing paired seed-bootstrap intervals...", flush=True)
    overview = summarize(config, rows, args.output)
    print("Checking fixed planning-horizon sensitivity...", flush=True)
    sensitivity(config, params, args.output)
    manifest = {"model_version": config["model_version"], "python": platform.python_version(),
                "platform": platform.platform(), "started_at_utc": started,
                "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                "runtime_seconds": time.monotonic() - start,
                "evaluation_rows": len(rows), "evaluation_cells": len(rows) // (len(POLICIES) * len(config["evaluation_seeds"])),
                "config": config, "selected_parameters": asdict(params),
                "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in (ROOT / "src/roaming.py", Path(__file__).resolve(), args.config.resolve())}}
    (args.output / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for row in overview:
        print(f"{row['policy']:18s} mean deficit={row['mean_service_deficit']:.6f} mean handoffs={row['mean_handoffs']:.3f}")
    print(f"Completed {len(rows):,} evaluation runs in {manifest['runtime_seconds']:.1f} seconds.", flush=True)


if __name__ == "__main__":
    main()
