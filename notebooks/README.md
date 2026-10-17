# notebooks/

Jupyter notebooks for exploration only. Their results are exploratory and
are never reported as confirmatory.

- Write notebook outputs to `results/exploratory/`, nowhere else in
  `results/`.
- Nothing canonical in `results/` or `paper/` may depend on a notebook.
- When an exploratory result matters, move the code into `src/research/`
  or `scripts/`, justify it from the protocol or an amendment, and
  regenerate the result from there.
- Clear outputs before committing. `just verify` fails on a committed code
  cell with an execution count or outputs.
