#!/usr/bin/env python3
"""Change true capacity while retaining the original candidate estimator.

This is a secondary synthetic sensitivity analysis, not external validation.
Current-serving service remains ideally observed by every policy.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from roaming import POLICIES, Parameters, link_service, make_trace, prepare, run
from run_study import quantile, write_csv


def alter_truth(prepared, config, factors):
    """The estimator and RSSI observations are unchanged; only truth changes."""
    new_truth = []
    for step in range(prepared.trace.steps):
        index = prepared.trace.start + step
        links = []
        for ap, factor in enumerate(factors):
            radio = dict(config["radio_parameters"])
            radio["maximum_rate_mbps"] *= factor
            links.append(link_service(prepared.signal[step][ap], prepared.trace.load[index][ap],
                                      prepared.profile, radio))
        new_truth.append(tuple(links))
    return replace(prepared, truth=tuple(new_truth))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-results", type=Path, default=ROOT / "results")
    parser.add_argument("--output", type=Path, default=ROOT / "results/model_mismatch")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    config_path = ROOT / "configs/study.json"
    diagnostic_path = ROOT / "configs/model-mismatch.json"
    config = json.loads(config_path.read_text())
    diagnostic = json.loads(diagnostic_path.read_text())
    params_path = (args.main_results / "selected_parameters.json").resolve()
    params = Parameters(**json.loads(params_path.read_text())["parameters"])
    rows, factors_record = [], []
    for scenario, seed in itertools.product(diagnostic["scenarios"], diagnostic["evaluation_seeds"]):
        trace = make_trace(config, scenario, seed)
        rng = random.Random(seed * 131 + 8849)
        factors_by_variant = {
            "matched": [1.0] * len(config["ap_positions_m"]),
            "half_capacity": [0.5] * len(config["ap_positions_m"]),
            "uneven_capacity": [rng.uniform(*diagnostic["uneven_capacity_range"])
                                for _ in config["ap_positions_m"]],
        }
        for name, factors in factors_by_variant.items():
            factors_record.append(dict(scenario=scenario, seed=seed, variant=name, factors=factors))
        for profile, age in itertools.product(diagnostic["profiles"], diagnostic["telemetry_delays_seconds"]):
            original = prepare(config, trace, profile, age)
            for variant in diagnostic["truth_variants"]:
                prepared = alter_truth(original, config, factors_by_variant[variant])
                for cost, policy in itertools.product(diagnostic["blackout_seconds"], POLICIES):
                    rows.append(dict(variant=variant, scenario=scenario, profile=profile,
                                     telemetry_delay_seconds=age, blackout_seconds=cost, seed=seed,
                                     policy=policy, **run(prepared, config, policy, params, cost)))
        print(f"Completed {scenario}, seed {seed}", flush=True)
    write_csv(args.output / "seed_metrics.csv", rows)
    grouped = defaultdict(list)
    paired = defaultdict(dict)
    for row in rows:
        grouped[row["variant"], row["policy"]].append(row)
        key = tuple(row[k] for k in ("variant", "scenario", "profile", "telemetry_delay_seconds", "blackout_seconds", "seed"))
        paired[key][row["policy"]] = row
    summary = []
    for (variant, policy), samples in sorted(grouped.items()):
        summary.append(dict(variant=variant, policy=policy, runs=len(samples),
                            mean_service_deficit=statistics.fmean(r["service_deficit"] for r in samples),
                            mean_unserved_fraction=statistics.fmean(r["unserved_fraction"] for r in samples),
                            mean_handoffs=statistics.fmean(r["handoffs"] for r in samples)))
    write_csv(args.output / "overall_descriptive.csv", summary)
    # First average differences across cells within each seed. Then resample
    # seeds as blocks, retaining dependence between settings sharing a seed.
    blocks = defaultdict(list)
    for key, policies in paired.items():
        variant, *_, seed = key
        for comparator in (p for p in POLICIES if p != "proposed"):
            blocks[variant, comparator, seed].append(
                policies["proposed"]["service_deficit"] - policies[comparator]["service_deficit"])
    contrast_rows = []
    rng = random.Random(diagnostic["bootstrap_seed"])
    for variant, comparator in itertools.product(diagnostic["truth_variants"], (p for p in POLICIES if p != "proposed")):
        means = [statistics.fmean(blocks[variant, comparator, seed]) for seed in diagnostic["evaluation_seeds"]]
        samples = sorted(statistics.fmean(rng.choices(means, k=len(means)))
                         for _ in range(diagnostic["bootstrap_replicates"]))
        contrast_rows.append(dict(variant=variant, contrast="proposed_minus_" + comparator,
                                  seed_blocks=len(means), mean_difference=statistics.fmean(means),
                                  ci95_low=quantile(samples, .025), ci95_high=quantile(samples, .975)))
    write_csv(args.output / "paired_block_comparisons.csv", contrast_rows)
    manifest = {"completed_at_utc": datetime.now(timezone.utc).isoformat(), "diagnostic": diagnostic,
                "selected_parameters": params.__dict__, "rows": len(rows),
                "true_capacity_factors": factors_record,
                "status": "Exploratory review-added sensitivity; evaluation seeds reused, no retuning.",
                "source_sha256": {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in (Path(__file__), ROOT / "src/roaming.py", config_path, diagnostic_path, params_path)}}
    (args.output / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Saved {len(rows)} runs to {args.output}")


if __name__ == "__main__":
    main()
