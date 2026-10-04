# Contributing

Use Python 3.11 or 3.12 on Linux. Clone the repository and run `make setup-dev`; run `make lint typecheck test docs` before a pull request. `make reproduce` regenerates data-quality evidence and executes the notebook's plain-Python cells. For the separate read-only model catalog, use Python 3.12 and `make setup-inspect inspect`.

Keep a small conventional commit for each reviewed change. Never alter the original CSV/PBIX bytes or rewrite Git history. Input-policy changes require source/license evidence and an explicit before/after record. Retain dataset attribution and ShareAlike for derived data/figures. Do not infer crop units, replace reported yield silently or present fixture/metadata arithmetic as validated Power BI output.

Tests should explain a real failure mode: duplicate grain after alias mapping, zero/nonfinite/negative values, fractional area, exact tolerance boundaries, checksum/schema drift or complete slice membership. New notebook cells must use ordinary Python and explicit printed output; the maintained runner does not support magics/display machinery.

Use [bug reports](https://github.com/Prajwal-Pratap-Yadav/Analyzing-Agricultural-Productivity-Across-Indian-States-Power-BI/issues/new?template=bug.yml) for reproducibility defects and the existing roadmap for Desktop/provenance work. See [security policy](SECURITY.md) for sensitive findings. Scoped tests and measured evidence are preferred to unverified dashboard or agronomic claims.
