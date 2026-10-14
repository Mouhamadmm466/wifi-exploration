#!/usr/bin/env python3
"""Check the saved packet study without rerunning thousands of policy runs.

Run trace_packet_study.py first for its 18 deterministic replays. This validator
checks those saved replays, declared grids, counters, pairing, and provenance.
It does not validate a Wi-Fi implementation, codec, or physical measurement.
"""
import argparse
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import platform
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.packet_roaming import POLICIES, default_config


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def read_csv(path):
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    require(bool(rows), f"Empty result file: {path}")
    return rows


def number(row, key):
    value = float(row[key])
    require(math.isfinite(value), f"Non-finite {key}: {row.get('scenario')}/{row.get('seed')}/{row.get('policy')}")
    return value


def integer(row, key):
    value = number(row, key)
    require(value >= 0 and value.is_integer(), f"Invalid nonnegative count {key}: {value}")
    return int(value)


def config_for(protocol, overrides=None):
    config = default_config()
    config.update(protocol["config"])
    config.update(overrides or {})
    return config


def check_row(row, config, main=False):
    for key in row:
        if key.endswith("_fraction"):
            require(-1e-12 <= number(row, key) <= 1 + 1e-12, f"Fraction outside [0,1]: {key}")
    for key in ("packet_conservation_error", "background_conservation_error"):
        require(number(row, key) == 0, f"Conservation error: {key}")
    offered, delivered, timely = (integer(row, key) for key in ("offered_packets", "delivered_packets", "ontime_packets"))
    drops = sum(integer(row, key) for key in ("queue_drops", "expiry_drops", "handoff_drops"))
    pending = integer(row, "final_pending_packets")
    require(offered == delivered + drops + pending, "Foreground counts do not sum")
    require(0 <= timely <= delivered <= offered, "Foreground delivery ordering failed")
    require(integer(row, "late_packets") == delivered - timely, "Late-packet count inconsistent")
    if config["packet_expiry"]:
        require(pending == 0, "Expired traffic remains after deadline drain")
    bg_offered = integer(row, "background_offered_packets")
    bg_delivered = integer(row, "background_delivered_packets")
    bg_dropped = integer(row, "background_dropped_packets")
    bg_pending = integer(row, "background_pending_packets")
    require(bg_offered == bg_delivered + bg_dropped + bg_pending, "Background counts do not sum")
    require(0 <= bg_delivered <= bg_offered, "Background delivery ordering failed")
    expected_voice = math.ceil(config["duration_seconds"] / config["voice_interval_seconds"] - 1e-10)
    expected_frames = math.ceil(config["duration_seconds"] * config["video_fps"] - 1e-10)
    require(integer(row, "generated_voice_packets") == expected_voice, "Wrong generated voice denominator")
    require(integer(row, "generated_video_frames") == expected_frames, "Wrong generated frame denominator")
    if main:
        require((expected_voice, expected_frames) == (3000, 1800), "Declared main denominator changed")
    require(math.isclose(number(row, "ontime_packet_fraction"), timely / offered, abs_tol=1e-12), "On-time packet fraction inconsistent")
    voice = number(row, "voice_missed_fraction")
    video = 1 - number(row, "video_complete_fraction")
    objective = .5 * (voice + video)
    for key in ("call_miss_fraction", "objective_miss_fraction"):
        require(math.isclose(number(row, key), objective, abs_tol=1e-12), f"Primary score inconsistent: {key}")
    require(math.isclose(number(row, "video_missed_fraction"), video, abs_tol=1e-12), "Video miss fraction inconsistent")
    require(integer(row, "voice_missed_slots") == round(voice * expected_voice), "Missed voice slots inconsistent")
    require(number(row, "ontime_delivered_mbps") <= number(row, "delivered_mbps") + 1e-12, "Timely throughput exceeds total delivery")
    require(integer(row, "delivered_delay_sample_count") == delivered, "Conditional delay denominator inconsistent")
    attempts, failed, succeeded = (integer(row, key) for key in ("handoffs", "failed_handoffs", "successful_handoffs"))
    residual = attempts - failed - succeeded
    require(failed <= attempts and 0 <= residual <= 1, "Invalid attempted/failed/completed transition counts")
    if main:
        require(residual == 0, "Unfinished successful transition in main run despite sufficient drain")
    union = number(row, "radio_blackout_union_seconds")
    scan, handoff = number(row, "scan_blackout_seconds"), number(row, "handoff_blackout_seconds")
    require(max(scan, handoff) - 1e-8 <= union <= scan + handoff + 1e-8, "Blackout union inconsistent")
    return residual


def check_table(path, protocol, scenarios, seeds, choices, condition, overrides=None, main=False, supplied_rows=None):
    rows = read_csv(path) if supplied_rows is None else list(supplied_rows)
    scenario_map = {scenario["name"]: scenario for scenario in scenarios}
    expected = {(scenario, seed, variant) for scenario, seed, variant in
                itertools.product(scenario_map, seeds, choices)}
    actual = {(r["scenario"], int(r["seed"]), r["variant"]) for r in rows}
    require(len(actual) == len(rows), f"Duplicate result rows: {path}")
    require(actual == expected, f"Missing or unexpected declared grid entries: {path}")
    config = config_for(protocol, overrides)
    groups, unfinished = {}, 0
    for row in rows:
        require(row["condition"] == condition, f"Wrong condition in {path}")
        require(row["policy"] == choices[row["variant"]], f"Wrong variant-policy mapping: {path}")
        unfinished += check_row(row, config, main=main)
        key = row["scenario"], int(row["seed"])
        groups.setdefault(key, []).append(row)
    for (scenario_name, seed), group in groups.items():
        # Check world identifiers against inputs, not just equality with peers.
        identity = dict(config=config, scenario=scenario_map[scenario_name], seed=seed)
        input_hash = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        world_hash = hashlib.sha256(json.dumps(dict(identity, model="packet-roaming-v2"), sort_keys=True).encode()).hexdigest()
        for row in group:
            require(row["input_sha256"] == input_hash, f"Input fingerprint mismatch: {scenario_name}/{seed}")
            require(row["world_fingerprint"] == world_hash, f"World fingerprint mismatch: {scenario_name}/{seed}")
        for key in ("offered_packets", "generated_voice_packets", "generated_video_frames", "background_offered_packets"):
            require(len({row[key] for row in group}) == 1, f"Offered traffic is not paired: {key}/{scenario_name}/{seed}")
    return rows, {"file": str(path.relative_to(ROOT)), "condition": condition, "rows": len(rows), "paired_worlds": len(groups),
                  "sha256": digest(path), "inferred_unfinished_successful_attempts": unfinished}


def check_sources(record, protocol_path, archived=False, history=None):
    for source, expected in record["source_hashes"].items():
        if source == "protocol_content":
            path = protocol_path
        elif archived and source == "docs/packet-study-protocol.md":
            path = history / "initial_protocol.md"
        else:
            path = ROOT / source
        require(digest(path) == expected, f"Frozen source hash changed: {path}")


def check_manifests(directory, protocol_path, archived=False):
    paths = sorted(directory.glob("run_manifest_*.json"))
    require(bool(paths), f"No run manifest: {directory}")
    output = []
    for path in paths:
        manifest = read_json(path)
        check_sources(manifest, protocol_path, archived, directory)
        for name, expected in manifest["files"].items():
            require(digest(directory / name) == expected, f"Manifest data hash changed: {directory / name}")
        output.append({"file": str(path.relative_to(ROOT)), "stage": manifest["stage"],
            "elapsed_seconds": manifest["elapsed_seconds"], "python": manifest["python"],
            "workers": manifest["workers"], "csv_hashes_checked": len(manifest["files"])})
    return output


def check_selection(directory, protocol, rows, protocol_path, archived=False):
    frozen = read_json(directory / "frozen_parameters.json")
    check_sources(frozen, protocol_path, archived, directory)
    require(frozen["development_seeds"] == protocol["development_seeds"], "Frozen development seeds differ")
    grouped = {}
    for row in rows:
        grouped.setdefault(row["variant"], []).append(row)
    require(len(frozen["scores"]) == len(grouped), "Frozen score grid incomplete")
    for score in frozen["scores"]:
        group = grouped[score["variant"]]
        require(math.isclose(score["mean_miss_fraction"], statistics.mean(number(r, "call_miss_fraction") for r in group), abs_tol=1e-12), "Saved development objective differs from raw rows")
        require(math.isclose(score["mean_handoffs"], statistics.mean(number(r, "handoffs") for r in group), abs_tol=1e-12), "Saved development handoff score differs")
    for policy in protocol["parameter_grids"]:
        best = min((s for s in frozen["scores"] if s["policy"] == policy),
                   key=lambda s: (s["mean_miss_fraction"], s["mean_handoffs"], s["variant"]))
        require(frozen["selected"][policy] == best["params"], f"Selection rule mismatch: {policy}")
    for policy in ("no_dwell", "no_guard", "no_cost", "no_age"):
        require(frozen["selected"][policy] == frozen["selected"]["predictive"], "Ablation parameters changed")
    return frozen


def check_traces(path, rows, protocol):
    with gzip.open(path, "rt") as handle:
        document = json.load(handle)
    seed = protocol["heldout_seeds"][0]
    expected = {(s["name"], seed, p) for s in protocol["heldout_scenarios"]
                for p in ("rssi", "app_myopic", "predictive")}
    traces = document["traces"]
    actual = {(t["scenario"], t["seed"], t["policy"]) for t in traces}
    require(actual == expected and len(traces) == 18, "Trace set differs from the preselected 18 runs")
    main = {(r["scenario"], int(r["seed"]), r["policy"]): r for r in rows}
    for trace in traces:
        original = main[(trace["scenario"], trace["seed"], trace["policy"])]
        for key, value in trace.items():
            if key in original and isinstance(value, (int, float)):
                require(float(original[key]) == value, f"Replay scalar differs: {key}")
        require(trace["world_fingerprint"] == original["world_fingerprint"], "Replay world differs")
        voice, video = trace["voice_ontime"], trace["video_complete"]
        require(len(voice) == 3000 and len(video) == 1800, "Replay stream denominators differ")
        require(all(isinstance(v, bool) for v in voice + video), "Replay media outcomes are not booleans")
        require(math.isclose(1 - sum(voice)/len(voice), trace["voice_missed_fraction"], abs_tol=1e-12), "Voice trace and aggregate differ")
        require(math.isclose(sum(video)/len(video), trace["video_complete_fraction"], abs_tol=1e-12), "Frame trace and aggregate differ")
        for decision in trace["decisions"]:
            t = decision["time"]
            require(all(source <= t for source in decision["signal_sources"] + decision["load_sources"]), "Future observation in saved trace")
            require(decision["own_miss_source"] <= t, "Future own-miss observation in saved trace")
    return {"file": str(path.relative_to(ROOT)), "replays_checked": len(traces), "seed": seed,
            "scalar_equality": "exact", "voice_and_frame_arrays_match": True, "sha256": digest(path),
            "replayed_by": "scripts/trace_packet_study.py; validator checks its saved artifact"}


def check_analysis(directory, row_count, policy_count, world_count, input_path=None):
    manifest = read_json(directory / "analysis_manifest.json")
    require(manifest["analysis_sha256"] == digest(ROOT / "scripts/analyze_packet_study.py"), "Analysis source changed")
    require(manifest["rows"] == row_count and manifest["worlds"] == world_count, "Analysis uses wrong run/world count")
    require(len(manifest["policies"]) == policy_count, "Analysis uses wrong policy count")
    require(len(read_csv(directory / "policy_summary.csv")) == policy_count, "Analysis policy summary incomplete")
    require(manifest["bootstrap_repetitions"] == 5000 and manifest["bootstrap_seed"] == 81631,
            "Bootstrap settings differ from the declared analysis")
    if input_path is not None:
        require(manifest["input_sha256"] == digest(input_path), "Analysis input hash changed")
    return str(directory.relative_to(ROOT))


def check_supplement(directory, protocol, frozen, original_sensitivity, main_rows, original_dir):
    spec_path, raw_path = directory / "specification.json", directory / "runs.csv"
    specification = read_json(spec_path)
    manifest = read_json(directory / "run_manifest.json")
    require(manifest["status"] == "complete", "Supplement run is not complete")
    require(manifest["specification_sha256"] == digest(spec_path), "Supplement specification hash changed")
    require(manifest["raw_sha256"] == digest(raw_path), "Supplement raw hash changed")
    require(manifest["source_hashes"] == specification["source_hashes"], "Supplement source records differ")
    for path, expected in specification["source_hashes"].items():
        require(digest(ROOT / path) == expected, f"Supplement frozen source changed: {path}")
    require(specification["original_frozen_source_hashes"] == frozen["source_hashes"], "Supplement uses different original source freeze")
    require(specification["parameters"] == frozen["selected"]["load_aware"] == {"load_margin": 0.75}, "Supplement load margin was retuned")
    require(specification["retuning"] is False, "Supplement retuning flag is not false")
    require(specification["seeds"] == protocol["sensitivity_seeds"], "Supplement uses different sensitivity seeds")
    conditions = {c["name"]: c for c in specification["conditions"]}
    require(set(conditions) == {c["name"] for c in protocol["sensitivities"]}, "Supplement sensitivity names differ")
    rows, checks, analyses = read_csv(raw_path), [], []
    require(len(rows) == specification["expected_rows"] == manifest["rows"] == 320, "Expected 320 supplementary runs")
    for condition in protocol["sensitivities"]:
        name = condition["name"]
        declared = conditions[name]
        expected_scenarios = [s for s in protocol["heldout_scenarios"] if s["name"] in condition["scenarios"]]
        require(declared["config"] == config_for(protocol, condition["overrides"]), "Supplement config differs from original condition")
        require(declared["scenarios"] == expected_scenarios, "Supplement scenarios differ from original condition")
        selected = [r for r in rows if r["condition"] == name]
        samples, checked = check_table(raw_path, protocol, expected_scenarios, specification["seeds"],
            {"load_aware": "load_aware"}, name, condition["overrides"], supplied_rows=selected)
        originals = {(r["scenario"], int(r["seed"])): r for r in original_sensitivity[name]}
        for sample in samples:
            original = originals[(sample["scenario"], int(sample["seed"]))]
            for field in ("input_sha256", "world_fingerprint", "offered_packets", "generated_voice_packets",
                          "generated_video_frames", "background_offered_packets"):
                require(sample[field] == original[field], f"Supplement world does not pair with original: {field}")
        checks.append(checked)
        analysis = directory / f"analysis_{name}"
        combined = read_csv(analysis / "combined_runs.csv")
        row_key = lambda r: (r["scenario"], int(r["seed"]), r["policy"])
        expected_combined = original_sensitivity[name] + samples
        require(sorted(combined, key=row_key) == sorted(expected_combined, key=row_key),
                f"Supplement analysis changed or omitted original rows: {name}")
        analyses.append(check_analysis(analysis, 200, 5, 40))
    reference_dir = directory / "reference_analysis"
    reference = read_csv(reference_dir / "combined_runs.csv")
    scenario_names = set(protocol["sensitivities"][0]["scenarios"])
    policy_names = set(protocol["sensitivities"][0]["policies"]) | {"load_aware"}
    expected_reference = [r for r in main_rows if r["scenario"] in scenario_names
        and int(r["seed"]) in specification["seeds"] and r["policy"] in policy_names]
    require(len(reference) == 200 and sorted(reference, key=row_key) == sorted(expected_reference, key=row_key),
            "Supplement reference is not the declared unchanged main subset")
    analyses.append(check_analysis(reference_dir, 200, 5, 40))
    analysis_path = directory / "supplementary_analysis_manifest.json"
    analysis_manifest = read_json(analysis_path)
    required_hashes = {
        "analysis_script_sha256": ROOT / "scripts/analyze_packet_load_supplement.py",
        "paired_analysis_script_sha256": ROOT / "scripts/analyze_packet_study.py",
        "specification_sha256": spec_path,
        "supplement_raw_sha256": raw_path,
        "original_manifest_sha256": original_dir / "run_manifest_sensitivity.json",
        "summary_sha256": directory / "supplementary_contrasts.csv",
    }
    for field, path in required_hashes.items():
        require(analysis_manifest[field] == digest(path), f"Supplement analysis hash changed: {field}")
    for field, base in (("original_input_hashes", original_dir), ("combined_table_hashes", directory)):
        for path, expected in analysis_manifest[field].items():
            require(digest(base / path) == expected, f"Supplement analysis input changed: {path}")
    require(len(analysis_manifest["combined_table_hashes"]) == 9 and
            len(analysis_manifest["original_input_hashes"]) == 9, "Supplement analysis hash coverage incomplete")
    require(analysis_manifest["supplementary_runs"] == 320 and analysis_manifest["conditions"] == 8 and
            analysis_manifest["worlds_per_condition"] == 40 and analysis_manifest["seed_blocks_per_condition"] == 10,
            "Supplement analysis count differs")
    return {"checked": True, "designation": specification["designation"], "runs": 320,
            "retuning": False, "directory": str(directory.relative_to(ROOT)), "tables": checks,
            "analyses": analyses, "reused_main_reference_rows": 200,
            "analysis_manifest_sha256": digest(analysis_path),
            "elapsed_seconds": manifest["elapsed_seconds"], "workers": manifest["workers"],
            "specification_sha256": digest(spec_path), "raw_sha256": digest(raw_path)}


def validate(results, protocol_path, require_figures=False, supplement_path=None):
    protocol = read_json(protocol_path)
    require(len(protocol["heldout_scenarios"]) == 6 and len(protocol["heldout_seeds"]) == 40, "Main design changed")
    require(not set(protocol["development_seeds"]) & set(protocol["heldout_seeds"]), "Development/heldout seed overlap")
    history = results / "development_history"
    initial_path = history / "initial_protocol.json"
    initial = read_json(initial_path)
    tables, development = [], []
    for directory, declared, declared_path, expected_count, archived in (
        (history, initial, initial_path, 456, True), (results, protocol, protocol_path, 1032, False)):
        choices = {f"{policy}_{index}": policy for policy, options in declared["parameter_grids"].items()
                   for index, _ in enumerate(options)}
        rows, report = check_table(directory / "development_runs.csv", declared,
            declared["development_scenarios"], declared["development_seeds"], choices, "development")
        require(len(rows) == expected_count, "Unexpected development-round row count")
        frozen = check_selection(directory, declared, rows, declared_path, archived)
        tables.append(report)
        development.append({"runs": len(rows), "configurations": len(choices), "frozen_at_utc": frozen["frozen_at_utc"]})
    rows, report = check_table(results / "main_runs.csv", protocol, protocol["heldout_scenarios"],
        protocol["heldout_seeds"], {p: p for p in POLICIES}, "main", main=True)
    require(len(rows) == 2400, "Expected exactly 2400 main policy runs")
    tables.append(report)
    require(len(protocol["sensitivities"]) == 8, "Expected eight sensitivity conditions")
    analyses = [check_analysis(results, 2400, 10, 240, results / "main_runs.csv")]
    sensitivity_runs, sensitivity_rows = 0, {}
    for condition in protocol["sensitivities"]:
        scenarios = [s for s in protocol["heldout_scenarios"] if s["name"] in condition["scenarios"]]
        require(len(scenarios) == 4 and len(protocol["sensitivity_seeds"]) == 10 and len(condition["policies"]) == 4,
                "Sensitivity grid differs from four scenarios, ten seeds, four policies")
        samples, report = check_table(results / f"sensitivity_{condition['name']}.csv", protocol,
            scenarios, protocol["sensitivity_seeds"], {p:p for p in condition["policies"]},
            condition["name"], condition["overrides"])
        require(len(samples) == 160, "Sensitivity row count is not 160")
        sensitivity_runs += len(samples)
        sensitivity_rows[condition["name"]] = samples
        tables.append(report)
        candidates = [results / f"analysis_{condition['name']}", results / condition["name"],
                      results / "sensitivity" / condition["name"]]
        directory = next((p for p in candidates if (p / "analysis_manifest.json").exists()), None)
        require(directory is not None, f"Missing sensitivity analysis: {condition['name']}")
        analyses.append(check_analysis(directory, 160, 4, 40, results / f"sensitivity_{condition['name']}.csv"))
    require(sensitivity_runs == 1280, "Expected exactly 1280 sensitivity runs")
    # A matched slice of existing main rows is a reference, not a new run.
    reference_path = results / "reference_subset.csv"
    reference = read_csv(reference_path)
    names = set(protocol["sensitivities"][0]["scenarios"])
    policies = set(protocol["sensitivities"][0]["policies"])
    reference_seeds = set(protocol["sensitivity_seeds"])
    expected_reference = {(r["scenario"], int(r["seed"]), r["policy"]): r for r in rows
        if r["scenario"] in names and int(r["seed"]) in reference_seeds and r["policy"] in policies}
    actual_reference = {(r["scenario"], int(r["seed"]), r["policy"]): r for r in reference}
    require(len(reference) == 160 and set(actual_reference) == set(expected_reference), "Matched reference subset incomplete")
    for key, sample in actual_reference.items():
        original = expected_reference[key]
        for field in original:
            if field != "condition":
                require(sample[field] == original[field], f"Reference subset changed main value: {field}")
    analyses.append(check_analysis(results / "analysis_reference_subset", 160, 4, 40, reference_path))
    manifests = check_manifests(history, initial_path, archived=True) + check_manifests(results, protocol_path)
    # Completion manifests must cover the raw main and every sensitivity file.
    covered = set()
    for path in results.glob("run_manifest_*.json"):
        covered.update(read_json(path)["files"])
    require({"main_runs.csv"} | {f"sensitivity_{c['name']}.csv" for c in protocol["sensitivities"]} <= covered,
            "Completed run manifests do not cover every evaluation table")
    traces = check_traces(results / "selected_traces.json.gz", rows, protocol)
    figures = {"checked": False}
    figure_manifest = results / "figures/figure_manifest.json"
    if figure_manifest.exists():
        figure = read_json(figure_manifest)
        require(figure["plot_script_sha256"] == digest(ROOT / "scripts/plot_packet_results.py"), "Plot script changed")
        for name, expected in figure["inputs_sha256"].items():
            require(digest(results / name) == expected, f"Plot input changed: {name}")
        for name in figure["outputs"]:
            path = results / "figures" / name
            magic = path.read_bytes()[:8]
            require((path.suffix == ".png" and magic.startswith(b"\x89PNG\r\n\x1a\n")) or
                    (path.suffix == ".pdf" and magic.startswith(b"%PDF-")), f"Invalid plot artifact: {path}")
        figures = {"checked": True, "files": figure["outputs"],
                   "output_sha256": {name: digest(results / "figures" / name) for name in figure["outputs"]}}
    elif require_figures:
        raise ValueError("Final figures are missing")
    timeline_path = results / "figures/timeline_manifest.json"
    if timeline_path.exists():
        timeline = read_json(timeline_path)
        require(timeline["input_sha256"] == digest(results / "selected_traces.json.gz"), "Timeline trace input changed")
        require(timeline["scenario"] == "short_cells" and timeline["seed"] == 50001, "Timeline selection changed")
        timeline_hashes = {}
        for suffix, magic in (("png", b"\x89PNG\r\n\x1a\n"), ("pdf", b"%PDF-")):
            path = results / f"figures/preselected_timeline.{suffix}"
            require(path.read_bytes().startswith(magic), f"Invalid timeline artifact: {path}")
            timeline_hashes[path.name] = digest(path)
        figures["timeline"] = {"checked": True, "manifest_sha256": digest(timeline_path),
                               "output_sha256": timeline_hashes,
                               "current_plot_script_sha256": digest(ROOT / "scripts/plot_packet_timeline.py")}
    elif require_figures:
        raise ValueError("Preselected timeline figure is missing")
    supplementary_directory = supplement_path or results / "additional_load"
    supplement = {"checked": False, "runs": 0}
    if (supplementary_directory / "specification.json").exists():
        supplement = check_supplement(supplementary_directory, protocol,
                                     read_json(results / "frozen_parameters.json"), sensitivity_rows, rows, results)
    elif supplement_path:
        raise ValueError("Requested supplementary specification is missing")
    optimization_path = results / "analysis_optimization_check.json"
    optimization = {"checked": False}
    if optimization_path.exists():
        recorded = read_json(optimization_path)
        require(recorded["byte_equality"] is True and
                recorded["before_sha256"] == recorded["after_sha256"] == digest(results / "paired_contrasts.csv"),
                "Recorded bootstrap optimization equivalence does not match current paired results")
        optimization = {"checked": True, "evidence_sha256": digest(optimization_path),
                        "paired_contrasts_sha256": recorded["after_sha256"],
                        "scope": "Checks recorded before/after equality; does not rerun the prior analyzer"}
    analysis_artifacts = {}
    for analysis_dir in analyses + supplement.get("analyses", []):
        directory = ROOT / analysis_dir
        for name in ("policy_summary.csv", "scenario_summary.csv", "paired_contrasts.csv", "analysis_manifest.json"):
            path = directory / name
            analysis_artifacts[str(path.relative_to(ROOT))] = digest(path)
    return {"passed": True, "model": "packet-roaming-v2", "main_runs": 2400, "main_paired_worlds": 240,
        "sensitivity_runs": sensitivity_runs, "development_runs_executed": 1488,
        "development_rounds": development, "tables": tables, "analyses": analyses,
        "matched_reference": {"rows": 160, "new_simulation_runs": 0, "sha256": digest(reference_path)},
        "supplementary_load_sensitivity": supplement,
        "total_executed_policy_runs_excluding_replays": 5168 + supplement["runs"],
        "run_manifests": manifests, "selected_replays": traces, "figures": figures,
        "analysis_artifact_hashes": analysis_artifacts, "analysis_optimization_record": optimization,
        "checks": ["Exact declared grids and no duplicate rows", "Paired input/world fingerprints and offered traffic",
                   "Foreground and background packet conservation", "Generated denominators, score identities and fraction bounds",
                   "Transition counters and blackout union", "Frozen selection/source hashes and completed CSV hashes",
                   "All main and sensitivity analyses present", "18 preselected replays agree exactly with main scalars"],
        "interpretation": "Internal software/data verification of a synthetic packet-queue study. No codec, IEEE 802.11 implementation, hardware, or human-quality validation."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results/packet")
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/packet-study.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-figures", action="store_true")
    parser.add_argument("--supplement", type=Path, help="Optional supplementary directory; default is results/additional_load when present")
    args = parser.parse_args()
    started, timer = datetime.now(timezone.utc).isoformat(), time.monotonic()
    try:
        report = validate(args.results.resolve(), args.protocol.resolve(), args.require_figures,
                          args.supplement.resolve() if args.supplement else None)
    except (AssertionError, ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        report = {"passed": False, "error": f"{type(exc).__name__}: {exc}"}
    report.update(started_at_utc=started, completed_at_utc=datetime.now(timezone.utc).isoformat(),
        validation_seconds=time.monotonic()-timer, python=platform.python_version(),
        validator_sha256=digest(Path(__file__)), command=sys.argv)
    output = args.output or args.results / "validation.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": report["passed"], "seconds": report["validation_seconds"],
                      "output": str(output), "error": report.get("error")}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
