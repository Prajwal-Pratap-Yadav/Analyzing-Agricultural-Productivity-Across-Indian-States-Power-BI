"""Grain, arithmetic and coverage assertions with a reproducible quality profile."""

from collections import Counter
from decimal import Decimal

from etl.clean import CropRow, ratio_matches
from etl.policy import DataError, Policy


def validate(rows: list[CropRow], policy: Policy) -> dict[str, object]:
    """Count mismatches rather than silently dropping or correcting reported yields."""
    if not rows:
        raise DataError("No observations to validate")
    keys = [row.grain for row in rows]
    if len(set(keys)) != len(keys):
        raise DataError("Duplicate canonical state/crop/year/season grain")
    for row in rows:
        if row.production_per_area != row.production / row.area:
            raise DataError("Calculated ratio no longer equals production/area")
        if row.ratio_check_pass != ratio_matches(
            row.reported_yield, row.production_per_area, policy
        ):
            raise DataError("Ratio-check flag is inconsistent with the policy")
    failed = [row for row in rows if not row.ratio_check_pass]
    accepted = [row for row in rows if row.ratio_check_pass]
    assert all(
        ratio_matches(row.reported_yield, row.production / row.area, policy) for row in accepted
    )
    years = sorted({row.year for row in rows})
    by_crop = Counter(row.crop for row in rows)
    failed_crop = Counter(row.crop for row in failed)
    coverage: dict[str, object] = {}
    for state in sorted({row.state for row in rows}):
        observed = sorted({row.year for row in rows if row.state == state})
        coverage[state] = {
            "years": observed,
            "missing_dataset_years": sorted(set(years) - set(observed)),
        }
    return {
        "input_rows": len(rows),
        "cleaned_rows": len(rows),
        "dropped_rows": 0,
        "ratio_check_pass_rows": len(accepted),
        "ratio_mismatch_rows": len(failed),
        "ratio_mismatch_percent": float(Decimal(len(failed)) * 100 / len(rows)),
        "distinct_crops": len(by_crop),
        "distinct_state_labels": len(coverage),
        "distinct_seasons": len({row.season for row in rows}),
        "years": years,
        "boundary_review_rows": sum(row.boundary_review for row in rows),
        "state_alias_rows": sum(row.state != row.raw_state for row in rows),
        "relative_tolerance": str(policy.relative_tolerance),
        "absolute_tolerance": str(policy.absolute_tolerance),
        "ratio_policy": "abs(reported-calculated) <= max(abs_tol, rel_tol*max(abs(reported),abs(calculated)))",
        "crop_counts": {
            crop: {"rows": count, "mismatch_rows": failed_crop[crop]}
            for crop, count in sorted(by_crop.items())
        },
        "coverage": coverage,
        "interpretation": "Arithmetic flags do not establish measurement accuracy or per-crop physical units.",
    }
