# data/

| Directory    | Contract                                                         |
| ------------ | ---------------------------------------------------------------- |
| `external/`  | Upstream or original inputs. Immutable.                          |
| `interim/`   | Intermediate transformations. Regenerable.                       |
| `processed/` | Analysis-ready datasets. Regenerable.                            |

## Rules

- `external/`: add files only. Never modify, overwrite or delete them in place.
  Record each file in `docs/provenance.qmd`.
- `interim/`, `processed/`: write only from code in `src/research/` or
  `scripts/`. Every file must be regenerable from `external/`.
- Never edit a generated file by hand. Change the code and regenerate.
- Deleting `interim/` and `processed/` must lose nothing.
