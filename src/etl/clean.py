"""Normalize labels; retain source yield and calculate a separate ratio."""

from dataclasses import dataclass
from decimal import Decimal

from etl.policy import DataError, Policy, number


@dataclass(frozen=True)
class CropRow:
    crop: str
    year: int
    season: str
    state: str
    raw_state: str
    area: Decimal
    production: Decimal
    rainfall: Decimal
    fertilizer: Decimal
    pesticide: Decimal
    reported_yield: Decimal
    production_per_area: Decimal
    ratio_check_pass: bool
    boundary_review: bool

    @property
    def grain(self) -> tuple[str, str, int, str]:
        return (self.state, self.crop, self.year, self.season)


def ratio_matches(reported: Decimal, calculated: Decimal, policy: Policy) -> bool:
    """Symmetric math.isclose rule: absolute OR relative tolerance, not their sum."""
    return abs(reported - calculated) <= max(
        policy.absolute_tolerance,
        policy.relative_tolerance * max(abs(reported), abs(calculated)),
    )


def normalize(records: list[dict[str, str]], policy: Policy) -> list[CropRow]:
    """Preserve all valid records, with explicit mismatch and boundary flags."""
    result = []
    for line, row in enumerate(records, start=2):
        crop, season, raw_state = (row[k].strip() for k in ("Crop", "Season", "State"))
        state = policy.state_aliases.get(raw_state, raw_state)
        if not crop or season not in policy.allowed_seasons or state not in policy.allowed_states:
            raise DataError(f"CSV line {line}: crop, season or historical state label is invalid")
        try:
            year = int(row["Crop_Year"])
        except ValueError as exc:
            raise DataError(f"CSV line {line}: crop year must be an integer") from exc
        if not policy.minimum_year <= year <= policy.maximum_year:
            raise DataError(f"CSV line {line}: crop year outside the configured coverage")
        values = {k: number(row[k], f"CSV line {line}, {k}") for k in (
            "Area", "Production", "Annual_Rainfall", "Fertilizer", "Pesticide", "Yield"
        )}
        if values["Area"] == 0:
            raise DataError(f"CSV line {line}: area must be positive")
        ratio = values["Production"] / values["Area"]
        boundary = (state == "Telangana" and year < 2014) or (
            state in {"Jharkhand", "Chhattisgarh", "Uttarakhand"} and year <= 2000
        )
        result.append(CropRow(crop, year, season, state, raw_state, values["Area"],
                              values["Production"], values["Annual_Rainfall"],
                              values["Fertilizer"], values["Pesticide"], values["Yield"],
                              ratio, ratio_matches(values["Yield"], ratio, policy), boundary))
    return sorted(result, key=lambda row: row.grain)
