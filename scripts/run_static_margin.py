#!/usr/bin/env python3
"""Added review diagnostic: can a tuned fixed margin explain the result?

This was added after the main run started, before inspecting its evaluation
results. It uses the original pilot seeds for tuning and never retunes on the
evaluation seeds. It is a diagnostic, not an independently preregistered test.
"""
import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import itertools
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from roaming import Parameters, run
from run_study import contexts, quantile, write_csv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/study.json")
    parser.add_argument("--main-results", type=Path, default=ROOT / "results")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    params_path = args.main_results / "selected_parameters.json"
    params = Parameters(**json.loads(params_path.read_text())["parameters"])
    margins = [0.03, 0.08, 0.15, 0.25]
    pilot_rows = []
    for scenario, seed, profile, age, prepared in contexts(config, config["pilot_seeds"]):
        for blackout, margin in itertools.product(config["blackout_seconds"], margins):
            local = dict(config, quality_margin=margin)
            result = run(prepared, local, "app_myopic", params, blackout)
            pilot_rows.append(dict(scenario=scenario, seed=seed, profile=profile,
                                   telemetry_delay_seconds=age, blackout_seconds=blackout,
                                   quality_margin=margin, **result))
    write_csv(out / "static_margin_pilot_seed_metrics.csv", pilot_rows)
    selection = [dict(quality_margin=margin, mean_service_deficit=statistics.fmean(
        row["service_deficit"] for row in pilot_rows if row["quality_margin"] == margin)) for margin in margins]
    write_csv(out / "static_margin_pilot_selection.csv", selection)
    chosen = min(selection, key=lambda row: (row["mean_service_deficit"], row["quality_margin"]))["quality_margin"]
    (out / "static_margin_selected.json").write_text(json.dumps({
        "quality_margin": chosen, "pilot_seeds": config["pilot_seeds"], "grid": margins,
        "rule": "Lowest equal-cell mean service deficit on original pilot seeds only.",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "Added exploratory diagnostic after independent code review, before main evaluation inspection."
    }, indent=2) + "\n")
    print(f"Static-margin pilot selected {chosen}.", flush=True)
    rows = []
    local = dict(config, quality_margin=chosen)
    for scenario, seed, profile, age, prepared in contexts(config, config["evaluation_seeds"]):
        for blackout in config["blackout_seconds"]:
            rows.append(dict(scenario=scenario, profile=profile, blackout_seconds=blackout,
                             telemetry_delay_seconds=age, seed=seed, policy="app_static",
                             quality_margin=chosen, **run(prepared, local, "app_myopic", params, blackout)))
    write_csv(out / "static_margin_seed_metrics.csv", rows)
    with (args.main_results / "seed_metrics.csv").open() as handle:
        main_rows = [row for row in csv.DictReader(handle) if row["policy"] == "proposed"]
    keys = ("scenario", "profile", "blackout_seconds", "telemetry_delay_seconds")
    def key(row):
        return row["scenario"], row["profile"], float(row["blackout_seconds"]), float(row["telemetry_delay_seconds"]), int(row["seed"])
    main = {key(row): row for row in main_rows}
    groups = {}
    for row in rows:
        sample_key = key(row)
        original = main[sample_key]
        groups.setdefault(sample_key[:-1], []).append({metric: float(original[metric]) - row[metric]
                                                     for metric in ("service_deficit", "handoffs")})
    rng = random.Random(config["bootstrap_seed"])
    comparisons = []
    for cell, differences in sorted(groups.items()):
        result = dict(zip(keys, cell), contrast="proposed_minus_app_static", n_seed_pairs=len(differences))
        draws = [[rng.randrange(len(differences)) for _ in differences] for _ in range(config["bootstrap_replicates"])]
        for metric in ("service_deficit", "handoffs"):
            samples = sorted(statistics.fmean(differences[index][metric] for index in draw) for draw in draws)
            result["mean_difference_" + metric] = statistics.fmean(row[metric] for row in differences)
            result["ci95_low_" + metric] = quantile(samples, 0.025)
            result["ci95_high_" + metric] = quantile(samples, 0.975)
        comparisons.append(result)
    write_csv(out / "static_margin_paired.csv", comparisons)
    manifest = {"completed_at_utc": datetime.now(timezone.utc).isoformat(),
                "evaluation_rows": len(rows), "pilot_rows": len(pilot_rows),
                "selected_quality_margin": chosen,
                "status": "Review-added diagnostic. Output-path interface added and experiment rerun; numerical method unchanged.",
                "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in (Path(__file__).resolve(), ROOT / "src/roaming.py", args.config.resolve())}}
    (out / "static_margin_run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Static-margin mean deficit={statistics.fmean(row['service_deficit'] for row in rows):.6f}; "
          f"mean handoffs={statistics.fmean(row['handoffs'] for row in rows):.3f}", flush=True)


if __name__ == "__main__":
    main()
