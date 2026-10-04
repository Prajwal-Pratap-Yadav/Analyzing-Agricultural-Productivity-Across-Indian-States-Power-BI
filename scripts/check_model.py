"""Compare a fresh read-only model extraction with the published catalog."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
candidate = Path(sys.argv[1])
for name in ["catalog.json", "arithmetic-crosschecks.json"]:
    expected = json.loads((ROOT / "reports/model" / name).read_text())
    actual = json.loads((candidate / name).read_text())
    if actual != expected:
        raise SystemExit(f"Model extraction differs: {name}")
print("Original model catalog and arithmetic cross-checks reproduce exactly.")
