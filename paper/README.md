# Research paper

The complete manuscript is `wifi-roaming-paper.tex`; the exported reading copy is `wifi-roaming-paper.pdf`. The author is Mouhamad Mamane, with the supplied email address. No university affiliation or publication venue is assumed.

The source is standalone: all six diagrams/plots and all 17 cited references are embedded in the LaTeX file. It can be opened in the Codex LaTeX editor or a normal LaTeX project. No external figure or bibliography file is needed to compile it. It uses a readable single-column article format because no target journal or conference was specified.

## Refresh the tables and graphs

From the repository root, after generating the saved analysis tables:

```sh
python3 scripts/update_paper_data.py
```

The script replaces only the marked generated regions. It preserves the prose. It reads the saved main, sensitivity, supplementary and trace files, and the two repository bibliographies. `data-generation-manifest.json` records those inputs and the generator hash. It does not rerun simulations or select a favorable example.

If results change in a future study, the surrounding prose must also be reviewed. Refreshing generated regions alone does not update every number or interpretation in the text.

## Export a PDF

The source compiles with the built-in LaTeX editor. For a local PDF export, the version used here is Tectonic 0.17.0:

```sh
tectonic --outdir paper --keep-logs paper/wifi-roaming-paper.tex
```

The first run may download standard LaTeX packages. A standard XeLaTeX installation can also compile the source; run it again as needed to resolve references. The scientific plots use TikZ/PGFPlots, not raster screenshots. Separate PNG and PDF versions are available under `results/packet/figures` for reuse in slides or reports.

The manuscript is ready for the researcher's review, not a claim of journal acceptance or completed human verification. Its central result is negative for the proposed complex rule. The complete source and original data preserve that result and its limitations.
