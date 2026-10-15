# results/

| Directory  | Contract                                                            |
| ---------- | ------------------------------------------------------------------- |
| `raw/`     | Unmodified outputs from stochastic or external experiments. Immutable. |
| `derived/` | Deterministic analysis outputs. Regenerable.                        |
| `tables/`  | Publication tables. Generated from code.                            |
| `figures/` | Publication figures. Generated from code.                           |

## Rules

- `raw/`: store outputs exactly as the experiment produced them. Never
  modify, overwrite or delete them in place. They cannot be regenerated, so
  they must be preserved.
- `derived/`: compute only from `raw/` and `data/processed/`, using code in
  `src/research/` or `scripts/`.
- `tables/`, `figures/`: write only from code. Every file the paper uses
  must come from here.
- Never edit a generated file by hand. Change the code and regenerate.
- Deleting `derived/`, `tables/` and `figures/` must lose nothing.
