---
name: scientific-figures
description: Rules for creating or changing empirical figures and their captions — figure scripts, files in results/figures/, figure captions in paper/. Use when plotting results for the manuscript or docs, not for exploratory plots in notebooks.
---

# Scientific figures

## Rules

**Generated from code.** Every empirical figure is produced by a script, so
that rerunning it reproduces the file. Exploratory plots in `notebooks/` do
not count until moved into code.

**No manual alteration.** Never edit plotted data, points or bars by hand or
in a graphics editor. Fix the data or the code and regenerate. Layout
annotations added in code are fine.

**Traceable source data.** A figure script reads only from
`results/derived/` or `data/processed/`. Record each figure, its script and
its inputs under `outputs` in `provenance.yml`.

**Explicit axes and units.** Label every axis with the quantity and its unit.
State transformations (log scale, normalisation, truncated or broken axes) on
the figure or in the caption.

**Uncertainty where relevant.** Show intervals or error bars wherever the
figure shows estimates, and say in the caption what they represent (95% CI,
standard error, interquartile range) and the sample size.

**Vector output.** Prefer PDF or SVG. Use raster (PNG at 300 dpi or more)
only for images or plots too dense for vector output.

**Descriptive captions.** The caption says what is plotted: variables,
groups, n, what the marks and intervals mean. It does not argue for an
interpretation; that belongs in the text.

**No imposed style.** Choose style for the paper at hand. Do not add a global
plotting theme or helper module unless several figures need the same code.

## Convention

- One script per figure, `scripts/figure_<name>.py`, calling plotting code
  in `src/research/` when it is shared.
- Output to `results/figures/<name>.<ext>`.
- Write numbers cited from the figure into `results/variables.yml` from the
  analysis code, not by reading values off the plot.

## Before finishing

Check the figure against these rules and report any you could not satisfy.
For an independent check, use the `figure-reviewer` agent.
