"""Checksum and schema gate for the original CSV."""

import csv
import hashlib
import io
from pathlib import Path

from etl.policy import DataError

HEADERS = (
    "Crop",
    "Crop_Year",
    "Season",
    "State",
    "Area",
    "Production",
    "Annual_Rainfall",
    "Fertilizer",
    "Pesticide",
    "Yield",
)


def read_csv(path: Path, expected_sha256: str) -> list[dict[str, str]]:
    """Only accept the declared bounded UTF-8 source, without silent row repair."""
    if path.stat().st_size > 5_000_000:
        raise DataError("CSV exceeds the 5 MB input bound")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise DataError("Source checksum differs from the policy; investigate before updating it")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
        if reader.fieldnames != list(HEADERS):
            raise DataError("CSV headers or their order differ from the ten-column schema")
        rows: list[dict[str, str]] = []
        for index, values in enumerate(reader, start=2):
            if None in values or any(
                v is None or not isinstance(v, str) or not v.strip() for v in values.values()
            ):
                raise DataError(f"CSV line {index}: missing, blank or surplus fields")
            rows.append({k: str(v) for k, v in values.items()})
        if not rows:
            raise DataError("CSV has no observations")
        return rows
    except (UnicodeError, csv.Error) as exc:
        raise DataError("CSV is not valid bounded UTF-8 tabular data") from exc
