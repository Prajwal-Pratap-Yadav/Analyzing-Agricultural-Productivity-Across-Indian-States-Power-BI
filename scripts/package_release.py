"""Package real attributed source/report/audit evidence beside tested code artifacts."""

import hashlib
import json
import os
import subprocess
import tomllib
import zipfile
from pathlib import Path

version = tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"]
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
if os.environ.get("GITHUB_SHA", sha) != sha:
    raise SystemExit("Release source differs from checked-out source")
output = Path("reports/local/release")
output.mkdir(parents=True, exist_ok=True)
wheel = Path(f"dist/crop_quality_audit-{version}-py3-none-any.whl")
sdist = Path(f"dist/crop_quality_audit-{version}.tar.gz")
if not wheel.is_file() or not sdist.is_file():
    raise SystemExit("Build the package before release")
for p in [wheel, sdist]:
    (output / p.name).write_bytes(p.read_bytes())
evidence = output / f"crop-quality-audit-{version}-evidence.zip"
files = []
for folder in ["data/raw", "powerbi/original", "docs", "notebooks"]:
    files.extend(p for p in Path(folder).rglob("*") if p.is_file())
files.extend(p for p in Path("data/processed").glob("*") if p.is_file())
files.extend(p for p in Path("reports").rglob("*") if p.is_file() and "local" not in p.parts)
files.extend(
    Path(p)
    for p in [
        "data/LICENSE.md",
        "data/source-receipt.json",
        "configs/policy.json",
        "LICENSE",
        "README.md",
        "CITATION.cff",
    ]
)
with zipfile.ZipFile(evidence, "w", zipfile.ZIP_DEFLATED) as archive:
    for p in sorted(set(files)):
        archive.write(p, p.as_posix())
    archive.writestr(
        "release-source.json",
        json.dumps(
            {
                "version": version,
                "source_git_sha": sha,
                "code_license": "MIT",
                "real_data_and_adaptations_license": "CC BY-SA 4.0",
                "real_data_creator": "Akshat Gupta (akshatgupta7)",
                "power_bi_refresh_render_output_validated": False,
            },
            indent=2,
        )
        + "\n",
    )
artifacts = sorted(p for p in output.iterdir() if p.is_file() and p.name != "SHA256SUMS")
(output / "SHA256SUMS").write_text(
    "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in artifacts)
)
print(f"Packaged {len(artifacts)} verified-source artifacts for {version} at {sha}")
