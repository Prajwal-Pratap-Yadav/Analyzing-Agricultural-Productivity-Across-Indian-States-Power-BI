"""Explicit validation tolerances and label policy."""

import json
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


class DataError(ValueError):
    """Input or configuration violates the stated data contract."""


def number(value: str, label: str) -> Decimal:
    """Read a finite nonnegative decimal, without a binary-float round trip."""
    if len(value) > 64:
        raise DataError(f"{label}: numeric text exceeds 64 characters")
    try:
        result = Decimal(value)
    except ArithmeticError as exc:
        raise DataError(f"{label}: expected a number") from exc
    if not result.is_finite() or result < 0:
        raise DataError(f"{label}: expected a finite nonnegative number")
    if len(result.as_tuple().digits) > 28 or (result and not -18 <= result.adjusted() <= 18):
        raise DataError(f"{label}: number exceeds the declared 28-digit / magnitude bounds")
    if result == 0:
        return Decimal(0)
    return result


@dataclass(frozen=True)
class Policy:
    relative_tolerance: Decimal
    absolute_tolerance: Decimal
    minimum_year: int
    maximum_year: int
    allowed_seasons: tuple[str, ...]
    allowed_states: tuple[str, ...]
    state_aliases: dict[str, str]
    data_sha256: str
    data_creator: str
    data_license: str
    license_url: str
    data_source_url: str

    @classmethod
    def load(cls, path: Path) -> "Policy":
        """Reject malformed configuration before reading data."""
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
            expected = set(cls.__dataclass_fields__)
            if not isinstance(config, dict) or set(config) != expected:
                raise DataError("Policy keys differ from the documented contract")
            relative = number(str(config["relative_tolerance"]), "relative_tolerance")
            absolute = number(str(config["absolute_tolerance"]), "absolute_tolerance")
            low, high = config["minimum_year"], config["maximum_year"]
            if type(low) is not int or type(high) is not int or not 1000 <= low <= high <= 9999:
                raise DataError("Policy year range is invalid")
            if relative > 1:
                raise DataError("Relative tolerance must not exceed one")
            for field in ("allowed_seasons", "allowed_states"):
                labels = config[field]
                if (
                    not isinstance(labels, list)
                    or not labels
                    or any(not isinstance(x, str) or not x or x != x.strip() for x in labels)
                    or len(labels) != len(set(labels))
                ):
                    raise DataError(f"Policy {field}: use distinct nonempty trimmed labels")
            aliases = config["state_aliases"]
            if not isinstance(aliases, dict) or any(
                not isinstance(k, str)
                or not k
                or k != k.strip()
                or v not in config["allowed_states"]
                for k, v in aliases.items()
            ):
                raise DataError("State aliases must map labels to the allowed historical labels")
            digest = config["data_sha256"]
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise DataError("Policy requires the exact input SHA256")
            for field in ("data_creator", "data_license", "license_url", "data_source_url"):
                value = config[field]
                if not isinstance(value, str) or not value.strip():
                    raise DataError(f"Policy {field} requires an explicit attribution value")
            return cls(
                relative,
                absolute,
                low,
                high,
                tuple(config["allowed_seasons"]),
                tuple(config["allowed_states"]),
                aliases,
                digest,
                config["data_creator"],
                config["data_license"],
                config["license_url"],
                config["data_source_url"],
            )
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise DataError("Malformed policy JSON") from exc
