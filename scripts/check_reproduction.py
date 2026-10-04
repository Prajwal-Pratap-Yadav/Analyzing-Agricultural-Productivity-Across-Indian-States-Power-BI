"""Independent pass over exported rows and agreement with notebook evidence."""

import csv
import hashlib
import json
import tempfile
from decimal import Decimal
from pathlib import Path

from etl.__main__ import audit

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as name:
    output = Path(name)
    audit(ROOT / "data/raw/crop_yield.csv", ROOT / "configs/policy.json", output)
    expected = json.loads((ROOT / "reports/validation_report.json").read_text())
    actual = json.loads((output / "validation_report.json").read_text())
    if actual != expected:
        raise SystemExit("Published validation report differs from fresh audit")
    for filename, digest in expected["csv_sha256"].items():
        if hashlib.sha256((output / filename).read_bytes()).hexdigest() != digest:
            raise SystemExit(f"Export checksum mismatch: {filename}")
    with (output / "cleaned.csv").open(newline="", encoding="utf-8") as handle:
        all_rows = list(csv.DictReader(handle))
    with (output / "ratio_check_pass.csv").open(newline="", encoding="utf-8") as handle:
        passed = list(csv.DictReader(handle))
    with (output / "ratio_mismatches.csv").open(newline="", encoding="utf-8") as handle:
        failed = list(csv.DictReader(handle))

    def grain(row):
        return tuple(row[k] for k in ["State", "Crop", "Crop_Year", "Season"])

    all_keys, pass_keys, fail_keys = (set(map(grain, rows)) for rows in [all_rows, passed, failed])
    if pass_keys & fail_keys or pass_keys | fail_keys != all_keys:
        raise SystemExit("Arithmetic slices are not a disjoint, complete partition")
    for row in passed:
        reported = Decimal(row["Reported_Yield"])
        ratio = Decimal(row["Production"]) / Decimal(row["Area"])
        if abs(reported - ratio) > max(
            Decimal(".01"), Decimal(".05") * max(abs(reported), abs(ratio))
        ):
            raise SystemExit("A pass-slice row violates its arithmetic guarantee")
        if abs(Decimal(row["Calculated_Production_per_Area"]) - ratio) > Decimal("0.000000000001"):
            raise SystemExit("Exported ratio precision is inconsistent")
notebook = json.loads((ROOT / "notebooks/01_etl.ipynb").read_text())
outputs = {
    c["id"]: "".join("".join(o.get("text", [])) for o in c.get("outputs", []))
    for c in notebook["cells"]
    if c["cell_type"] == "code"
}
for cell in ["coverage", "ratio-check", "area-and-boundaries", "inline-arithmetic"]:
    if cell not in outputs or not outputs[cell].strip():
        raise SystemExit(f"Unexecuted insight evidence cell: {cell}")
    if any(
        o.get("output_type") == "error" for c in notebook["cells"] for o in c.get("outputs", [])
    ):
        raise SystemExit("Notebook includes an error output")
if "9717" not in outputs["ratio-check"] or "235" not in outputs["area-and-boundaries"]:
    raise SystemExit("Notebook arithmetic/area evidence differs from published metrics")
print(
    "Fresh deterministic exports, independent slice arithmetic and executed evidence cells agree."
)
