# ADR 0003: Keep fast runtime independent of optional inspection and graphics

Status: accepted, 2026-10-04.

The audit can run with Python's standard library. Keep runtime build/bootstrap, developer chart/test tooling and Python 3.12 PBIXRay inspection in separately hash-locked environments. The wheel includes only code and a synthetic MIT fixture. Alternatives: require pandas/model decoding/matplotlib before any CSV check; distribute the report and real dataset inside the MIT wheel. Trade-off: full reproduction and optional inspection require additional setup; the real source/evidence release has a separate CC BY-SA notice.

The maintained notebook uses ordinary Python and printed diagnostics. Execute its cells sequentially and capture actual stdout with a small nbformat-validated runner; it does not support general notebook magics or a Jupyter UI. The initial local Jupyter-kernel attempt failed on restricted socket operations. The plain-Python mode executes the same cells without a kernel dependency and is explicitly identified in notebook metadata.
