# docs/amendments/

Changes to the study plan made after the protocol was frozen. The frozen
files listed in `protocol/manifest.toml` never change; each departure from
them is recorded here instead.

- One file per amendment, named `YYYY-MM-DD-short-title.qmd`. Copy
  `_template.qmd` to start one. Quarto skips files whose names begin with `_`.
- Write the amendment before running the analysis it changes, where possible,
  and say whether it was made before or after seeing any results.
- Do not edit an amendment once committed. To revise one, add a new amendment
  that refers back to it.
- A canonical analysis that departs from the protocol names the amendment
  that authorises the departure.

Decisions made before the freeze, or that do not depart from the protocol,
belong in `docs/decisions.qmd`.
