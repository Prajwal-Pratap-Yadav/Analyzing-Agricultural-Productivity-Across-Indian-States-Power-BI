# Refresh and confirm in Power BI Desktop

This has **not** been executed in this environment. The original PBIX is preserved byte-for-byte and contains its original local CSV path. Python figures are companion diagnostics, not report-page exports.

1. Open a copy of `powerbi/original/agricultural-productivity.pbix` in Power BI Desktop. Record the Desktop version and original report SHA256. Keep the original copy as evidence.
2. In Transform data, create a source-path parameter and point the import to your checked-out `data/raw/crop_yield.csv` (verify the source receipt checksum). Review encoding/delimiter settings and preserve **decimal Area** in this new working copy. Never cast area to integer just because most values are whole numbers.
3. Review the data dictionary, source licence and unit/boundary caveats before interpreting production or yield. If choosing processed data instead, update renamed-column references deliberately: its schema differs and retains both reported and derived ratios. Do not silently substitute the ratio for reported yield.
4. Refresh the working copy; compare its row count, distinct labels, source-area values and card aggregations with `reports/model/arithmetic-crosschecks.json`. Record every filter/slicer, measure formula and display format; attach actual values and differences. The Python comparisons are not yet validated against report output.
5. Export 2–3 real page images to `docs/assets/` with a manifest naming source/data hashes, refresh time, Desktop version and filters. Label them as the reviewed working copy. Do not relabel the Python figure as a dashboard export.
6. Optionally save that reviewed copy in PBIP format and audit credentials/machine paths before committing text metadata. Format migration and report-output confirmation are [roadmap work](https://github.com/Prajwal-Pratap-Yadav/Analyzing-Agricultural-Productivity-Across-Indian-States-Power-BI/issues/3).
