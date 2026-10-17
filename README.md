# empirical-research-template

A repository template for empirical research: a pre-registered protocol that
can be frozen, immutable inputs, generated results and a Quarto manuscript,
with checks and agent guardrails that keep them consistent.

## Starting a project

1. Create a repository from this template.
2. In `pyproject.toml`, rename the project and add a description and
   authors. Run `uv lock`.
3. Fill in `project` and `template` in `provenance.yml`.
4. Replace this README, keep `LICENSING.md`, and decide the licences for
   your code, manuscript and data.
5. Run `just setup`, then `just check` and `just verify`.

`docs/workflow.qmd` describes the workflow and the commands. `AGENTS.md`
holds the rules that agents and people follow.

## Requirements

uv, just and Quarto. Vale is optional, for `just prose`; a TeX installation
is optional, for `just pdf`. CI pins the versions it uses in
`.github/workflows/check.yml`.

## License

Copyright (C) 2026 Eoin O'Brien

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the [GNU General Public License](LICENSE) for
more details.

[`LICENSING.md`](LICENSING.md) sets out what the licence covers in a project
created from this template.
