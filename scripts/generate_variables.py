"""Write the values cited in the manuscript to results/variables.yml.

Quarto loads the file through `metadata-files` in `_quarto.yml`; documents
cite a value with the `meta` shortcode. See docs/workflow.qmd.
"""

import json
from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "results" / "variables.yml"


def collect() -> dict[str, object]:
    """Return manuscript values, computed from results/derived/ via research."""
    return {}


def main() -> None:
    # JSON is valid YAML, so no YAML library is needed.
    OUTPUT.write_text(json.dumps(collect(), indent=2) + "\n")


if __name__ == "__main__":
    main()
