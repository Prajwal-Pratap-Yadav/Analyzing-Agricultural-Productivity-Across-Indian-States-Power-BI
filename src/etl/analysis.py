"""Descriptive insights safe to compute despite unverified crop-unit semantics."""

from collections import Counter
from decimal import Decimal

from etl.clean import CropRow


def insights(rows: list[CropRow]) -> dict[str, object]:
    """Use coverage and arithmetic, never cross-crop physical production totals."""
    mismatches = sum(not r.ratio_check_pass for r in rows)
    counts = Counter(r.crop for r in rows)
    return {
        "rows": len(rows),
        "crops": len(counts),
        "state_labels": len({r.state for r in rows}),
        "seasons": len({r.season for r in rows}),
        "minimum_year": min(r.year for r in rows),
        "maximum_year": max(r.year for r in rows),
        "ratio_mismatches": mismatches,
        "ratio_mismatch_percent": f"{Decimal(mismatches) * 100 / len(rows):.2f}",
        "ratio_check_pass": len(rows) - mismatches,
        "fractional_area_rows": sum(r.area % 1 != 0 for r in rows),
        "telangana_before_2014_rows": sum(r.state == "Telangana" and r.year < 2014 for r in rows),
        "boundary_review_rows": sum(r.boundary_review for r in rows),
        "top_crops_by_row_count": [
            {"crop": crop, "rows": n}
            for crop, n in sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:8]
        ],
        "row_weighted_rainfall_average": str(
            sum((r.rainfall for r in rows), Decimal(0)) / len(rows)
        ),
        "row_weighted_pesticide_average": str(
            sum((r.pesticide for r in rows), Decimal(0)) / len(rows)
        ),
        "csv_area_sum_diagnostic": str(sum((r.area for r in rows), Decimal(0))),
    }
