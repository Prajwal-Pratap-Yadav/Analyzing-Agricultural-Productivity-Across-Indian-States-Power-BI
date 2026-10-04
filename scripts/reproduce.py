"""Generate deterministic profiles, dictionary, insight notes and a real Python chart."""

import hashlib
import importlib.metadata
import json
import platform
import subprocess
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from etl.__main__ import audit
from etl.analysis import insights
from etl.clean import normalize
from etl.export import FIELDS, write_json
from etl.extract import read_csv
from etl.policy import Policy

ROOT = Path(__file__).resolve().parents[1]


def chart(profile):
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "text.color": "#e2e8f0",
            "axes.labelcolor": "#e2e8f0",
            "xtick.color": "#cbd5e1",
            "ytick.color": "#cbd5e1",
            "axes.edgecolor": "#334155",
            "font.size": 10,
        }
    )
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(12, 5.8), gridspec_kw={"width_ratios": [1, 1.3]}, facecolor="#0b1220"
    )
    for ax in (left, right):
        ax.set_facecolor("#0b1220")
        ax.spines[["top", "right"]].set_visible(False)
    counts = [profile["ratio_check_pass_rows"], profile["ratio_mismatch_rows"]]
    bars = left.bar(
        ["Pass arithmetic check", "Flagged mismatch"],
        counts,
        color=["#38bdf8", "#a78bfa"],
        width=0.58,
    )
    left.set_ylim(0, 12000)
    left.set_ylabel("Source records")
    left.set_title("Every row retained", loc="left", color="#e2e8f0", pad=18)
    for bar, count in zip(bars, counts, strict=True):
        left.text(
            bar.get_x() + bar.get_width() / 2,
            count + 250,
            f"{count:,}",
            ha="center",
            fontweight="bold",
            fontsize=14,
        )
    crops = sorted(profile["crop_counts"].items(), key=lambda x: (-x[1]["rows"], x[0]))[:8][::-1]
    labels = [name for name, _ in crops]
    failed = [values["mismatch_rows"] for _, values in crops]
    passed = [values["rows"] - values["mismatch_rows"] for _, values in crops]
    right.barh(labels, passed, color="#38bdf8", label="Pass arithmetic check")
    right.barh(labels, failed, left=passed, color="#a78bfa", label="Flagged mismatch")
    right.set_xlabel("Records (eight most represented crop labels)")
    right.set_title("Coverage and flags by crop", loc="left", color="#e2e8f0", pad=18)
    right.legend(
        loc="lower right",
        facecolor="#111827",
        edgecolor="#334155",
        labelcolor="#e2e8f0",
        fontsize=8,
    )
    fig.suptitle(
        "Crop data audit  |  19,689 records · 1997–2020",
        x=0.05,
        ha="left",
        fontsize=19,
        fontweight="bold",
    )
    fig.text(
        0.05,
        0.88,
        "Reported yield vs production / area — descriptive arithmetic, not a productivity ranking",
        fontsize=10,
        color="#cbd5e1",
    )
    fig.text(
        0.05,
        0.07,
        "Tolerance: 5% relative OR 0.01 absolute  ·  Physical crop units unverified  ·  0 rows dropped",
        fontsize=9,
    )
    fig.text(
        0.05,
        0.035,
        "Python re-creation, not a Power BI export  |  Data: Akshat Gupta, Kaggle v1 (CC BY-SA 4.0)",
        fontsize=8,
        color="#94a3b8",
    )
    fig.subplots_adjust(left=0.08, right=0.98, top=0.80, bottom=0.22, wspace=0.5)
    fig.savefig(
        ROOT / "docs/assets/data-quality.png",
        dpi=160,
        metadata={
            "Software": "matplotlib; reproducible crop audit",
            "Title": "Python crop data quality audit",
        },
    )
    plt.close(fig)


def dictionary():
    definitions = {
        "Crop": (
            "string",
            "label",
            "Trimmed source crop label; totals/categories are not disjoint species.",
        ),
        "Crop_Year": (
            "integer",
            "year label",
            "Source crop-year label; not a timestamp or uniformly documented harvest interval.",
        ),
        "Season": ("string", "label", "Trimmed source season; limited to six configured labels."),
        "State": (
            "string",
            "historical label",
            "Trimmed, alias-mapped state/UT label; boundaries are not redistributed.",
        ),
        "Raw_State": (
            "string",
            "historical label",
            "Trimmed state label before the documented alias map.",
        ),
        "Area": (
            "decimal",
            "hectares (uploader declaration)",
            "Source area with fractional values preserved; no integer cast.",
        ),
        "Production": (
            "decimal",
            "unverified per crop",
            "Uploader says metric tons; extreme values and missing crop-unit lineage prevent a universal tonne assumption.",
        ),
        "Annual_Rainfall": (
            "decimal",
            "mm (uploader declaration)",
            "Source annual rainfall; repeated across crop/season rows, not additive.",
        ),
        "Fertilizer": (
            "decimal",
            "kg (uploader declaration)",
            "Source total; methodology and independence across records are unverified.",
        ),
        "Pesticide": (
            "decimal",
            "kg (uploader declaration)",
            "Source total; methodology and independence across records are unverified.",
        ),
        "Reported_Yield": (
            "decimal",
            "unverified per crop",
            "Original Yield retained without overwrite; derivation/weighting is not documented.",
        ),
        "Calculated_Production_per_Area": (
            "decimal, 12 places on export",
            "unverified production unit / declared hectare",
            "Production divided by source decimal Area; a diagnostic, not a corrected agronomic yield.",
        ),
        "Ratio_Check_Pass": (
            "boolean",
            "none",
            "Reported and calculated ratio satisfy the symmetric tolerance rule; not an accuracy certification.",
        ),
        "Boundary_Review": (
            "boolean",
            "none",
            "Telangana before 2014 or 2000-or-earlier split-state label requires boundary review; row retained.",
        ),
    }
    text = "# Processed data dictionary\n\nGenerated by `scripts/reproduce.py` in schema order. No nulls are allowed; invalid fields reject the input. Numeric fields must be finite and nonnegative, with strictly positive Area. Source: [data receipt](../data/source-receipt.json); definitions and limits: [DATA.md](DATA.md).\n\n| Column | Type | Unit / scope | Meaning | Source | Null policy |\n|---|---|---|---|---|---|\n"
    for field in FIELDS:
        dtype, unit, meaning = definitions[field]
        source = (
            "derived audit"
            if field
            in {
                "Raw_State",
                "Calculated_Production_per_Area",
                "Ratio_Check_Pass",
                "Boundary_Review",
            }
            else "CSV; label normalization only" if field in {"Crop", "State", "Season"} else "CSV"
        )
        text += f"| `{field}` | {dtype} | {unit} | {meaning} | {source} | reject null |\n"
    (ROOT / "docs/data-dictionary.md").write_text(text, encoding="utf-8")


def insight_notes(metrics):
    text = f"""# Descriptive insights

Generated by `scripts/reproduce.py` from the same functions used in the executed [notebook](../notebooks/01_etl.ipynb). Cell IDs below identify the exact code/output. These are measured source diagnostics, not causal or policy claims.

| Notebook cell | Exact result | Method | Caveat |
|---|---|---|---|
| `coverage` | {metrics['rows']:,} rows; {metrics['crops']} crop labels; {metrics['state_labels']} state/UT labels; {metrics['seasons']} seasons; {metrics['minimum_year']}–{metrics['maximum_year']} | Cardinality of trimmed labels and crop-year range | An observed range does not mean every state/crop has every year; see validation coverage. |
| `ratio-check` | {metrics['ratio_mismatches']:,} mismatches ({metrics['ratio_mismatch_percent']}%); {metrics['ratio_check_pass']:,} pass | Decimal production / area, symmetric 5% relative OR 0.01 absolute tolerance | Reported yield may have a different weighting definition; passing does not verify units or accuracy. No rows dropped. |
| `area-and-boundaries` | {metrics['fractional_area_rows']} fractional-area rows; {metrics['telangana_before_2014_rows']} Telangana rows before 2014; {metrics['boundary_review_rows']} total boundary-review flags | Source decimals, year/label tests | Original cached model rounds fractional area to integers. No geographical redistribution inferred. |
| `inline-arithmetic` | Row-weighted rainfall mean {Decimal(metrics['row_weighted_rainfall_average']):.6f}; pesticide mean {Decimal(metrics['row_weighted_pesticide_average']):.6f} | Decimal column sums / row count | Arithmetic cross-check only; repeated fields and changing coverage prevent national-average interpretation. Not validated against Power BI output. |

The figure selects the eight most represented crop labels by row count, with lexical tie-breaking; it does not select crops by high mismatch rates. No state productivity ranking, cross-crop yield average, rainfall total, fertilizer-effect estimate or future prediction is presented. The source includes `Oilseeds total` alongside individual crop categories, so summing those categories could double count.

Two baseline binary-float decisions differed at exact **relative** tolerance boundaries: Nagaland Sunflower 2009 (0.57 vs 0.6) and Odisha Horse-gram Summer 2018 (0.35 vs 7/19). The declared Decimal policy gives 9,717 mismatches; the initial float reconnaissance gave 9,719. The committed [boundary record](../reports/tolerance-boundaries.json) and tests retain this explanation.
"""
    (ROOT / "docs/insights.md").write_text(text, encoding="utf-8")


def main():
    policy_path = ROOT / "configs/policy.json"
    source = ROOT / "data/raw/crop_yield.csv"
    report = audit(source, policy_path, ROOT / "data/processed")
    rows = normalize(
        read_csv(source, Policy.load(policy_path).data_sha256), Policy.load(policy_path)
    )
    metrics = insights(rows)
    write_json(ROOT / "reports/validation_report.json", report)
    write_json(ROOT / "reports/insights.json", metrics)
    chart(report)
    dictionary()
    insight_notes(metrics)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    versions = {p: importlib.metadata.version(p) for p in ["matplotlib", "nbformat"]}
    generated = [
        "reports/validation_report.json",
        "reports/insights.json",
        "docs/assets/data-quality.png",
        "docs/data-dictionary.md",
        "docs/insights.md",
    ]
    manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_git_sha": sha,
        "dirty_source_tree": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        ),
        "data_sha256": Policy.load(policy_path).data_sha256,
        "policy_sha256": report["policy_sha256"],
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "versions": versions,
        "seed": "none; deterministic arithmetic",
        "generated_sha256": {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in generated
        },
        "limitations": "Read-only model metadata and Python diagnostics; no Power BI refresh, output validation or rendering.",
    }
    write_json(ROOT / "reports/run_manifest.json", manifest)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
