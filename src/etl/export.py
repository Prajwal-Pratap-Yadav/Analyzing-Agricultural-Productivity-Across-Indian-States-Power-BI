"""Deterministic CSV and JSON exports with dataset licence notes."""

import csv
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from etl.clean import CropRow

FIELDS = (
    "Crop", "Crop_Year", "Season", "State", "Raw_State", "Area", "Production",
    "Annual_Rainfall", "Fertilizer", "Pesticide", "Reported_Yield",
    "Calculated_Production_per_Area", "Ratio_Check_Pass", "Boundary_Review",
)


def write_json(path: Path, content: Any) -> None:
    """Atomically replace a stable sorted JSON result."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, encoding="utf-8", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(json.dumps(content, indent=2, sort_keys=True, allow_nan=False) + "\n")
    os.replace(temporary, path)


def write_rows(path: Path, rows: list[CropRow]) -> str:
    """Write original numerical decimals plus a twelve-place derived ratio."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, newline="", encoding="utf-8", delete=False) as handle:
        temporary = Path(handle.name)
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(FIELDS)
        for row in rows:
            writer.writerow((row.crop, row.year, row.season, row.state, row.raw_state,
                             row.area, row.production, row.rainfall, row.fertilizer,
                             row.pesticide, row.reported_yield,
                             format(row.production_per_area, ".12f"),
                             str(row.ratio_check_pass).lower(), str(row.boundary_review).lower()))
    os.replace(temporary, path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(rows: list[CropRow], output: Path, profile: dict[str, object]) -> dict[str, object]:
    """Publish the full audit table and clearly named arithmetic slices."""
    hashes = {
        "cleaned.csv": write_rows(output / "cleaned.csv", rows),
        "ratio_check_pass.csv": write_rows(output / "ratio_check_pass.csv", [r for r in rows if r.ratio_check_pass]),
        "ratio_mismatches.csv": write_rows(output / "ratio_mismatches.csv", [r for r in rows if not r.ratio_check_pass]),
    }
    report = {**profile, "csv_sha256": hashes, "data_license": "CC BY-SA 4.0",
              "data_creator": "Akshat Gupta (akshatgupta7)",
              "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
              "changes": "Trimmed labels; mapped aliases; retained reported yields; added ratio/flags; sorted rows."}
    write_json(output / "validation_report.json", report)
    return report
