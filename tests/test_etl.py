"""Adversarial inputs and independent arithmetic expectations for the audit."""

import csv
import hashlib
import io
import json
import os
import subprocess
import sys
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from etl.__main__ import audit
from etl.clean import normalize, ratio_matches
from etl.export import export
from etl.extract import HEADERS, read_csv
from etl.policy import DataError, Policy
from etl.validate import validate

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def policy():
    return Policy.load(ROOT / "configs/policy.json")


def observation(**changes):
    row = dict(
        zip(
            HEADERS,
            [" Rice ", "2013", " Kharif ", "Odisha", "100", "200", "1500", "30", "1", "2"],
            strict=True,
        )
    )
    row.update(changes)
    return row


def as_csv(rows):
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=HEADERS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode()


def test_trims_aliases_and_preserves_reported_measure(policy):
    rows = normalize([observation(State=" Orissa ", Yield="3")], policy)
    row = rows[0]
    assert row.state == "Odisha" and row.raw_state == "Orissa"
    assert row.crop == "Rice" and row.season == "Kharif"
    assert row.reported_yield == 3 and row.production_per_area == 2
    assert not row.ratio_check_pass
    assert validate(rows, policy)["dropped_rows"] == 0


@pytest.mark.parametrize(
    "column,value",
    [
        ("Area", "0"),
        ("Area", "-1"),
        ("Production", "NaN"),
        ("Yield", "Infinity"),
        ("Fertilizer", "bad"),
        ("Pesticide", "-0.01"),
        ("Annual_Rainfall", "-3"),
    ],
)
def test_rejects_invalid_numeric_values(policy, column, value):
    with pytest.raises(DataError):
        normalize([observation(**{column: value})], policy)


@pytest.mark.parametrize(
    "column,value",
    [
        ("Crop_Year", "1997.5"),
        ("Crop_Year", "1996"),
        ("Crop_Year", "2021"),
        ("State", "Atlantis"),
        ("Season", "Monsoon"),
        ("Crop", " "),
    ],
)
def test_rejects_unknown_labels_and_outside_years(policy, column, value):
    with pytest.raises(DataError):
        normalize([observation(**{column: value})], policy)


def test_duplicate_after_state_alias_mapping_is_rejected(policy):
    with pytest.raises(DataError, match="Duplicate canonical"):
        validate(normalize([observation(State="Orissa"), observation()], policy), policy)


def test_boundary_flags_retain_ambiguous_rows(policy):
    rows = normalize(
        [
            observation(State="Telangana"),
            observation(State="Chhattisgarh", Crop_Year="2000"),
            observation(State="Telangana", Crop_Year="2014"),
        ],
        policy,
    )
    assert validate(rows, policy)["boundary_review_rows"] == 2
    assert len(rows) == 3


def test_decimal_tolerance_boundary_and_symmetry(policy):
    assert ratio_matches(Decimal("0.03"), Decimal("0.04"), policy)
    assert not ratio_matches(Decimal("0.03"), Decimal("0.040000000001"), policy)
    assert ratio_matches(Decimal("19"), Decimal("20"), policy)
    assert ratio_matches(Decimal("20"), Decimal("19"), policy)
    assert not ratio_matches(Decimal("18.999"), Decimal("20"), policy)
    assert ratio_matches(Decimal("0"), Decimal("0"), policy)
    assert ratio_matches(Decimal("0.57"), Decimal("0.6"), policy)
    assert ratio_matches(Decimal("0.35"), Decimal(7) / Decimal(19), policy)


def test_inconsistent_internal_ratio_or_flag_is_rejected(policy):
    row = normalize([observation()], policy)[0]
    for broken in [
        replace(row, production_per_area=Decimal("9")),
        replace(row, ratio_check_pass=False),
    ]:
        with pytest.raises(DataError):
            validate([broken], policy)
    with pytest.raises(DataError):
        validate([], policy)


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"Crop,Year\nRice,2000\n",
        as_csv([]),
        as_csv([observation(Yield="")]),
        as_csv([observation()]) + b"extra,fields\n",
        b"\xff\xff",
    ],
)
def test_schema_blank_and_encoding_fail_closed(tmp_path, raw):
    source = tmp_path / "input.csv"
    source.write_bytes(raw)
    with pytest.raises(DataError):
        read_csv(source, hashlib.sha256(raw).hexdigest())


def test_source_checksum_and_size_bound(tmp_path):
    source = tmp_path / "input.csv"
    source.write_bytes(as_csv([observation()]))
    with pytest.raises(DataError, match="checksum"):
        read_csv(source, "0" * 64)
    with source.open("wb") as handle:
        handle.truncate(5_000_001)
    with pytest.raises(DataError, match="5 MB"):
        read_csv(source, "0" * 64)


@pytest.mark.parametrize(
    "change",
    [
        {"relative_tolerance": "1.1"},
        {"absolute_tolerance": "-1"},
        {"minimum_year": True},
        {"minimum_year": 2021},
        {"data_sha256": "bad"},
        {"allowed_states": ["Odisha", "Odisha"]},
        {"allowed_seasons": [" "]},
        {"state_aliases": {"Orissa": "Atlantis"}},
        {"data_creator": ""},
        {"extra": 1},
    ],
)
def test_malformed_policy_is_rejected(tmp_path, change):
    content = json.loads((ROOT / "configs/policy.json").read_text())
    content.update(change)
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(content))
    with pytest.raises(DataError):
        Policy.load(path)


def test_all_rows_and_slice_membership_are_deterministic(tmp_path, policy):
    raw = [
        observation(),
        observation(State="Assam", Yield="3"),
        observation(Crop_Year="2014", Yield="0"),
    ]
    rows = normalize(raw, policy)
    report = validate(rows, policy)
    assert report["ratio_check_pass_rows"] == 1 and report["ratio_mismatch_rows"] == 2
    first = export(rows, tmp_path / "first", report)
    second = export(normalize(list(reversed(raw)), policy), tmp_path / "second", report)
    assert first == second
    for name in (
        "cleaned.csv",
        "ratio_check_pass.csv",
        "ratio_mismatches.csv",
        "validation_report.json",
    ):
        assert (tmp_path / "first" / name).read_bytes() == (tmp_path / "second" / name).read_bytes()
    with (tmp_path / "first/ratio_check_pass.csv").open() as handle:
        accepted = list(csv.DictReader(handle))
    assert len(accepted) == 1 and accepted[0]["Reported_Yield"] == "2"
    assert accepted[0]["Calculated_Production_per_Area"] == "2.000000000000"


def test_real_source_end_to_end_without_row_loss(tmp_path):
    report = audit(ROOT / "data/raw/crop_yield.csv", ROOT / "configs/policy.json", tmp_path)
    assert report["input_rows"] == report["cleaned_rows"] == 19689
    assert report["ratio_mismatch_rows"] == 9717
    assert report["ratio_check_pass_rows"] == 9972
    assert report["boundary_review_rows"] == 141


def test_fractional_area_is_never_coerced_to_integer(policy):
    row = normalize([observation(Area="5.7", Production="6", Yield="1")], policy)[0]
    assert row.area == Decimal("5.7")
    assert row.production_per_area == Decimal(6) / Decimal("5.7")


def test_packaged_demo_attribution_and_main(tmp_path, monkeypatch, capsys):
    from etl.__main__ import main

    monkeypatch.setattr(sys, "argv", ["crop-audit", "--demo", "--output", str(tmp_path)])
    assert main() == 0
    report = json.loads((tmp_path / "validation_report.json").read_text())
    assert report["input_rows"] == 3 and report["ratio_mismatch_rows"] == 1
    assert report["data_license"] == "MIT" and "synthetic" in report["data_creator"]
    assert "3 rows retained" in capsys.readouterr().out


def test_main_handles_invalid_json_and_missing_input(tmp_path, monkeypatch, capsys):
    from etl.__main__ import main

    path = tmp_path / "policy.json"
    path.write_text("{invalid")
    monkeypatch.setattr(sys, "argv", ["crop-audit", "--policy", str(path)])
    assert main() == 2
    assert "Malformed policy" in capsys.readouterr().err


def test_analysis_coverage_is_descriptive_and_uses_source_decimals(policy):
    from etl.analysis import insights

    report = insights(
        normalize([observation(Area="10.5"), observation(State="Telangana", Yield="3")], policy)
    )
    assert report["rows"] == 2 and report["telangana_before_2014_rows"] == 1
    assert report["fractional_area_rows"] == 1
    assert report["csv_area_sum_diagnostic"] == "110.5"


def test_cli_failure_has_actionable_error_and_no_outputs(tmp_path):
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "etl",
            "--input",
            str(tmp_path / "missing.csv"),
            "--policy",
            str(ROOT / "configs/policy.json"),
            "--output",
            str(tmp_path / "outputs"),
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2 and "Audit rejected" in result.stderr
    assert "Traceback" not in result.stderr and not (tmp_path / "outputs").exists()
