"""Check local links, original bytes, release metadata, schema and file bounds."""

import json
import re
import subprocess
import tomllib
from pathlib import Path
from urllib.parse import unquote

from etl import __version__
from etl.export import FIELDS

ROOT = Path(__file__).resolve().parents[1]
tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
paths = {ROOT / p for p in tracked if p}
paths.update(p for p in (ROOT / "docs").rglob("*") if p.is_file())
paths.update(ROOT / p for p in ["README.md", "docs/EVIDENCE.md", "docs/RELEASE.md"])
problems = []
for path in sorted(paths):
    if not path.is_file():
        problems.append(f"Missing source file: {path.relative_to(ROOT)}")
        continue
    if path.stat().st_size > 5_000_000:
        problems.append(f"File exceeds 5 MB: {path.relative_to(ROOT)}")
    if path.suffix != ".md" or path.name == "README-original.md":
        continue
    for link in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
        target = link.split("#", 1)[0].split(" ", 1)[0]
        if not target or re.match(r"[a-z]+:", target):
            continue
        dest = (path.parent / unquote(target)).resolve()
        if not dest.is_relative_to(ROOT) or not dest.exists():
            problems.append(f"Broken local link in {path.relative_to(ROOT)}: {link}")
readme = (ROOT / "README.md").read_text()
required = [
    "Why this matters",
    "Quickstart",
    "Features",
    "Architecture",
    "Design decisions",
    "Results and limitations",
    "Repo map",
    "Development",
    "Roadmap",
    "License, data and citation",
]
actual = re.findall(r"^## (.+)$", readme, re.MULTILINE)
if actual != required:
    problems.append("README sections differ from fixed portfolio order")
if len(readme.splitlines()[2].split()) > 18:
    problems.append("README value proposition exceeds 18 words")
for badge in re.findall(r"https://img\.shields\.io/[^)]+", readme):
    if "style=flat-square" not in badge or "labelColor=0b1220" not in badge:
        problems.append("Badge misses portfolio style")
metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
if (
    metadata["version"] != __version__
    or f"## [{__version__}]" not in (ROOT / "CHANGELOG.md").read_text()
):
    problems.append("Package/changelog versions differ")
if f"version: {__version__}" not in (ROOT / "CITATION.cff").read_text():
    problems.append("Citation version differs")
dictionary = (ROOT / "docs/data-dictionary.md").read_text()
for field in FIELDS:
    if f"`{field}`" not in dictionary:
        problems.append(f"Dictionary misses {field}")
for name in [
    "reports/validation_report.json",
    "reports/model/catalog.json",
    "data/source-receipt.json",
]:
    json.loads((ROOT / name).read_text())
if problems:
    raise SystemExit("\n".join(problems))
print("README order, local links, schema/version metadata and tracked file bounds pass.")
