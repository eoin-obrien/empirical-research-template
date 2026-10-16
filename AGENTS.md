# AGENTS.md

These rules are invariants. If a task would break one, stop and ask.

## Integrity

- Never fabricate data, results, references, quotations or metadata. If
  something is unknown, say so.
- Add entries to `paper/references.bib` only through the reference workflow
  in `docs/workflow.qmd`. Never write BibTeX while drafting prose.
- Never change models, exclusions, metrics or hypotheses to obtain a desired
  result. Record every such change, with its reason, in `docs/decisions.qmd`.
- Keep exploratory and confirmatory analyses distinct. Never present an
  exploratory result as confirmatory.

## Data and results

- Never modify, overwrite or delete anything in `data/external/`.
- Never modify, overwrite or delete anything in `results/raw/`. Raw outputs
  from stochastic or external systems are preserved as produced.
- Change a generated artifact by changing its source and regenerating it.
  Never edit it directly.
- Generate numerical results in the manuscript from code where practicable.

## Code

- Canonical analyses live in `src/research/`.
- Scripts in `scripts/` orchestrate library code. They do not contain
  analysis logic.
- Notebooks in `notebooks/` are exploratory. Nothing canonical depends on
  them.
