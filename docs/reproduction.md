# Reproduce and inspect the research package

The main experiment uses Python's standard library. It was executed with Python 3.14.5; Python 3.10 or later is expected to work, but other versions have not all been tested. The manifests record source hashes, configuration, random seeds, and the actual execution environment.

All commands below run from the repository root. Use new directories under `work/` to preserve the shipped results. That directory is ignored by Git.

## Run the numerical work

```sh
python3 -m unittest discover -s tests -v
python3 scripts/run_study.py --output work/reproduction
python3 scripts/run_static_margin.py --main-results work/reproduction --output work/static-reproduction
python3 scripts/run_model_mismatch.py --main-results work/reproduction --output work/mismatch-reproduction
```

The main command repeats pilot selection, the full evaluation, the paired bootstrap, and the horizon sensitivity. It took about three minutes in the recorded environment. Other computers may differ. The supplemental commands use the saved pilot-selected parameters. They do not retune the candidate on evaluation results.

The static-margin diagnostic chooses its own constant margin using the original pilot seeds. The mismatch diagnostic uses the same main configuration and changes the true capacity only in its named stress cases. If you change `configs/study.json`, regenerate the main results before running either diagnostic.

Tests cover past-only information, unchanged decisions when future trace values change, repeatable paired traces, exact partial-step blackout accounting, score bounds, component removal, emergency-rule semantics, and separation of the mismatch truth from candidate predictions. Passing tests supports implementation consistency, not realism.

## Understand the files

| File or group | What it contains |
| --- | --- |
| `configs/study.json` | Main world, application profiles, policies' shared settings, tuning grids, and seeds |
| `results/pilot_seed_metrics.csv` | Every pilot variant's deficit and handoffs |
| `results/selected_parameters.json` | The parameters frozen before main evaluation |
| `results/seed_metrics.csv` | Main seed-level outcomes for all six policies |
| `results/cell_summary.csv` | Means and standard deviations for each setting and policy |
| `results/paired_comparisons.csv` | Candidate-minus-comparator differences and pointwise bootstrap intervals |
| `results/overall_descriptive.csv` | Equal-setting descriptive averages, without a pooled independence claim |
| `results/horizon_sensitivity.csv` | A secondary check of the holding-horizon assumption |
| `results/static_margin_*.csv` | The additional fixed-margin baseline's tuning, outcomes, and comparisons |
| `results/model_mismatch/` | Separate capacity-error configuration record, outcomes, and seed-block intervals |
| `results/*manifest.json` | Main or supplemental provenance records |
| `references/*sources.json` | Bibliographic records and reading depth; mechanism records also include search details |

There are 240 main evaluation world traces. They are generated deterministically from the source and seeds rather than stored as large duplicate files. Repeated policy runs and application/delay settings share these worlds. The raw outcome tables retain the scenario, settings, seed, and policy needed to pair comparisons.

The current data contains no real device identities, human activity records, or downloaded paper text. Literature links and original notes are provided instead of redistributing the papers.

## Recreate the figures

Figures are optional. Install their dependencies in a local virtual environment:

```sh
python3 -m venv work/figure-env
work/figure-env/bin/python -m pip install -r requirements-figures.txt
MPLCONFIGDIR=work/matplotlib-cache work/figure-env/bin/python scripts/plot_results.py
```

The plotting script reads the shipped `results/` data and writes PNG and SVG files to `results/figures/`. It does not rerun or alter the experiments. The pinned figure package versions reflect this execution; if a platform cannot install them, the CSV results remain usable without plotting dependencies.

The heatmap shows all 72 main settings against the application-myopic rule. The second figure shows the aggregate mismatch contrast with seed-block intervals. The figures were visually checked for clipped text and readable labels.

## Change the experiment honestly

Save a new configuration and output directory for a substantive change. Keep assumptions, selected parameters, and test environments together. Do not use the present evaluation results repeatedly for tuning and continue calling them an independent final test.

When comparing reruns, numeric CSV data should match in the recorded environment. Runtime and timestamp fields will differ. A source hash records which code produced a result; a clean test run alone does not establish that an old result came from new code.

The final integration check includes a sample numerical regeneration from the main experiment, full supplemental reruns using the documented output options, and a check that the main source hashes still match. Numerical changes require regenerating all affected results.
