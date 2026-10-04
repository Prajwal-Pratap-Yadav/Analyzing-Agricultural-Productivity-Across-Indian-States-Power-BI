# DAX and inline aggregation catalog

Read-only extraction found **zero explicit model DAX measures**, **zero calculated columns** and **zero relationships**. There are therefore no explicit measure names, formulas, descriptions or format strings to list; none were invented or installed in the preserved binary. The report uses inline field selections/aggregations. The [complete catalog](../reports/model/catalog.json) records every visual ID, type, raw `Select` structure, function code, internal alias and native reference label for all six pages.

Microsoft distinguishes [automatic field summarization and authored measures](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-measures). Internal aliases such as `Sum(...)` are sometimes retained while the native label says `Average`; names alone cannot prove the executed aggregation. Numeric function codes are retained without reverse-engineering undocumented execution/filter behavior. No Power BI output was available for validation.

| Observed native reference | Location | Recomputed diagnostic / meaning | Format and limitation |
|---|---|---|---|
| Count of Crop / Season / Crop_Year / State | Page 1 cards | Both nonblank rows and distinct trimmed labels/years recorded | Card formatting is visual configuration, not an explicit DAX format string; the exact count semantics need Desktop confirmation. |
| Average of Annual_Rainfall / Pesticide | Page 1 cards and other selections | Decimal CSV mean; pandas decoded-cache mean | Source-row weighted arithmetic; not validated against Power BI output or a national estimate. |
| Sum of Area | Page 6 table | CSV decimal sum and cache integer sum | Difference reflects 235 rounded source values; overlapping areas across crops/years are not a unique land footprint. |
| Sum / Average of Production | Pages 1–3 | Selections retained; no physical cross-crop aggregate interpreted | Per-crop units unverified, filters unexecuted. |
| Average / Sum of Yield | Pages 2 / 6 | Selections retained; no cross-crop productivity statistic interpreted | Reported yield weighting and units unverified; mean ratio and ratio of sums are different quantities. |
| Sum of rainfall / fertilizer / pesticide | Pages 4 / 6 | Selections retained; no national total interpreted | Repeated observations, unknown input estimation and category overlap can invalidate totals. |

[Arithmetic cross-checks](../reports/model/arithmetic-crosschecks.json) use the same label grains in CSV and decoded cache. Rainfall mean is 1437.755176615968307176596069 in decimal CSV arithmetic versus 1437.7551766159681 in pandas cached arithmetic; pesticide mean is 48848.35339200924374015947991 versus 48848.353392009245. These are rounding-close Python calculations, **not validated against Power BI output**. The source-decimal area sum is 3542574242.797 versus cached integer 3542574244; these are diagnostics, not unique agricultural land totals. The executed notebook's `inline-arithmetic` cell prints the exact comparisons.

To reproduce the extraction, use Python 3.12, `make setup-dev setup-inspect inspect`. `make inspect` compares fresh JSON with the published catalog and fails on drift. Confirm actual measures, display formats and filter contexts using the [refresh guide](refresh.md); retain that manual evidence separately if supplied.
