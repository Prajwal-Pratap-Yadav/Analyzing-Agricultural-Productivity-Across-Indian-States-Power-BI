# Data provenance and interpretation

The [source receipt](../data/source-receipt.json) identifies **Agricultural Crop Yield in Indian States Dataset**, Akshat Gupta (`akshatgupta7`), Kaggle dataset 3525502, version 1, published July 17, 2023. On October 4, 2026, the public [metadata endpoint](https://www.kaggle.com/api/v1/datasets/view/akshatgupta7/crop-yield-in-indian-states-dataset) declared **CC BY-SA 4.0**. The public download contained one 1,620,945-byte CSV whose SHA256 exactly matched this repository's original file: `ab9bc356b1f8107d490376cec24450a0e2906322ad25788ab22fb32537ab1f8f`. It is included under that grant, with [attribution, changes and ShareAlike notice](../data/LICENSE.md). Existing code remains MIT.

The uploader's listing is the verified distribution source. It does not establish a government publisher, original collection method, district aggregation rule, primary units by crop or historical boundary harmonization. Those facts are **unverified**. No official-government-data claim is made.

The ten-column original has 19,689 rows, 55 trimmed crop labels, 30 observed historical state/UT labels, six season labels and years 1997–2020. It is not a balanced panel. No null, negative numeric, zero-area or duplicate normalized grain was found. The [validation report](../reports/validation_report.json) records each state's observed/missing dataset years. `Crop_Year` is an integer label; its precise crop/harvest interval is not documented.

## Units and aggregation

| Field | Uploader declaration | Audit treatment |
|---|---|---|
| Area | hectares | Preserve source decimals; the original PBIX cache changes 235 fractional values through its integer cast. |
| Production | metric tons | Per-crop unit **unverified**; no cross-crop sum or conversion. Coconut extremes and fibre crops warrant primary-source confirmation, not inferred corrections. |
| Annual_Rainfall | mm | Preserve; repeated annual values across crop/season rows are not additive. Row-weighted means are arithmetic diagnostics, not national rainfall estimates. |
| Fertilizer / Pesticide | kilograms | Preserve; estimation method and row independence unknown. No causal input/productivity claim. |
| Yield | production per area | Preserve as `Reported_Yield`; aggregation/weighting formula and per-crop unit unknown. Calculate a separately named diagnostic ratio. |

`Oilseeds total` coexists with individual crop labels. These categories can overlap; crop-level sums may double count. A mean of yields from different crop units is not interpretable as a physical productivity measure.

## Arithmetic policy

Numeric text is limited to 64 characters and 28 significant digits; nonzero values must have a decimal adjusted exponent from -18 through 18. These transparent parser bounds prevent extreme finite values from overflowing ratio arithmetic. Every original numeric field falls within them (at most ten significant digits).

The [policy](../configs/policy.json) declares decimal arithmetic at Python's default 28-digit precision and a symmetric tolerance:

`abs(reported - production/area) <= max(0.01, 0.05 * max(abs(reported), abs(production/area)))`

5% relative **OR** 0.01 absolute tolerance is a transparent diagnostic choice, not a sourced agronomic accuracy standard. All valid records appear in `data/processed/cleaned.csv`; mismatches in `ratio_mismatches.csv`; the internally consistent slice in `ratio_check_pass.csv`. The slice asserts this arithmetic rule. It does not establish measurement validity, compatible crop units or an error in the original reported yield. Ratio decimals are rounded to 12 places only when exported. Reported yield is never overwritten.

There are 9,717 decimal-policy mismatches and 9,972 passes. The initial binary-float reconnaissance produced two additional failures at exact relative boundaries; [the retained examples](../reports/tolerance-boundaries.json) explain the difference. There is no hidden tolerance change or row dropping.

## State aliases and historical boundaries

| Input alias | Canonical historical label | Scope |
|---|---|---|
| Orissa | Odisha | Name only |
| Uttaranchal | Uttarakhand | Name only |
| Pondicherry | Puducherry | Name only |

The original file already uses these canonical names; **zero rows** are changed by this map. Unknown states/seasons are rejected, not guessed. No borders are redistributed. `Jammu and Kashmir` remains the source's historical label; it is not split into today's units. Sixty Telangana records precede 2014. Eighty-one Chhattisgarh/Uttarakhand split-year records add up to **141 boundary-review flags**. Flags retain records and identify review needs; they do not automatically correct dates or geography.

## Privacy, lineage and refresh

The full original Git history scan found no credential leaks. Read-only inspection covered the archive/layout, import query, security/connection metadata and 19,689 cached aggregate agricultural rows; no credentials or person-level records were found. The binary retains its original owner-machine file path. The published [catalog](../reports/model/catalog.json) redacts that path. Full-history and manual review are scoped checks, not a guarantee against every possible secret format.

See [lineage](lineage.md), [dictionary](data-dictionary.md), [measure catalog](dax-measures.md), [insights](insights.md) and [refresh guide](refresh.md). Power BI Desktop was unavailable: the report was neither edited, refreshed nor rendered. Optional `make inspect` reproduces metadata in Python 3.12; it does not evaluate DAX or validate report output.
