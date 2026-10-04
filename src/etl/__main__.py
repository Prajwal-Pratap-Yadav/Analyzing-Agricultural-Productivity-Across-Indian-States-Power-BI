"""Single local entry point: verify source, audit it, export deterministic results."""

import argparse
import hashlib
import sys
from importlib.resources import files
from pathlib import Path

from etl.clean import normalize
from etl.export import export
from etl.extract import read_csv
from etl.policy import DataError, Policy
from etl.validate import validate


def audit(source: Path, policy_path: Path, output: Path) -> dict[str, object]:
    """Run the complete pipeline without network, Power BI or optional plotting tools."""
    policy = Policy.load(policy_path)
    raw = read_csv(source, policy.data_sha256)
    rows = normalize(raw, policy)
    profile = validate(rows, policy)
    profile.update({"source_sha256": policy.data_sha256,
                    "data_creator": policy.data_creator, "data_license": policy.data_license,
                    "license_url": policy.license_url, "data_source_url": policy.data_source_url,
                    "policy_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
                    "trimmed_label_rows": sum(any(r[k] != r[k].strip() for k in ("Crop", "Season", "State")) for r in raw)})
    return export(rows, output, profile)


def main() -> int:
    """Return a concise actionable error for rejected data or configuration."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/raw/crop_yield.csv"))
    parser.add_argument("--policy", type=Path, default=Path("configs/policy.json"))
    parser.add_argument("--output", type=Path, default=Path("data/processed"))
    parser.add_argument("--demo", action="store_true", help="Use the bundled synthetic fixture; not agricultural evidence")
    options = parser.parse_args()
    if options.demo:
        options.input = Path(str(files("etl").joinpath("fixtures/crop_sample.csv")))
        options.policy = Path(str(files("etl").joinpath("fixtures/policy.json")))
    try:
        report = audit(options.input, options.policy, options.output)
    except (DataError, OSError) as exc:
        print(f"Audit rejected: {exc}", file=sys.stderr)
        return 2
    print(f"{report['cleaned_rows']} rows retained; {report['ratio_mismatch_rows']} ratio mismatches; "
          f"{report['ratio_check_pass_rows']} pass the arithmetic check.")
    print(f"Outputs: {options.output}; per-crop physical units remain unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
