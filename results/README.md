# results/

| Path       | Contract                                                            |
| ---------- | ------------------------------------------------------------------- |
| `raw/`     | Unmodified outputs from stochastic or external experiments. Immutable. |
| `derived/` | Deterministic analysis outputs. Regenerable.                        |
| `tables/`  | Publication tables. Generated from code.                            |
| `figures/` | Publication figures. Generated from code.                           |
| `exploratory/` | Exploratory outputs. Never canonical.                        |
| `variables.yml` | Values cited in the manuscript. Generated from code.       |

## Rules

- `raw/`: store outputs exactly as the experiment produced them. Never
  modify, overwrite or delete them in place. They cannot be regenerated, so
  once accepted for analysis they must be preserved.
- The template does not enforce this. Unlike `data/external/`, nothing
  blocks writes to `raw/` or records checksums for its files, and re-running
  an analysis can overwrite them. A project that relies on raw outputs adds
  its own provenance records and integrity checks for them, for example
  checksums verified by `just verify`.
- `derived/`: compute only from `raw/` and `data/processed/`, using code in
  `src/research/` or `scripts/`.
- `tables/`, `figures/`: write only from code. Every table and figure the
  paper uses must come from here.
- Never edit a generated file by hand. Change the code and regenerate.
- `variables.yml`: write only from the analysis (`just analyse`). Rendering
  and verification read it; they never regenerate it.
- `exploratory/`: outputs of notebooks and exploratory scripts. Nothing in
  `paper/` or the canonical analysis reads from here.
- Small publication-facing artifacts (`variables.yml`, tables, figures) may
  be committed so changes show in review. They stay regenerable.
- Deleting `derived/`, `tables/`, `figures/`, `exploratory/` and
  `variables.yml` must lose nothing that `just analyse` cannot regenerate.
