# scripts/

Thin entry points that run one stage of the workflow (for example, building
a processed dataset or producing a figure). Run them with `uv run`.

Keep reusable logic in `src/research/`, where it is type-checked and tested.
A script should mostly parse arguments, call into `research`, and write
outputs to `data/` or `results/`.
