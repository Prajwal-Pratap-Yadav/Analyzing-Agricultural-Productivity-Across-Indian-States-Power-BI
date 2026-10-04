"""Execute this plain-Python notebook's cells sequentially and capture real stdout."""

import contextlib
import io
import platform
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "notebooks/01_etl.ipynb"
notebook = nbformat.read(path, as_version=4)
namespace = {"__name__": "__main__"}
execution_count = 0
for cell in notebook.cells:
    if cell.cell_type != "code":
        continue
    execution_count += 1
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture):
        exec(compile(cell.source, f"01_etl.ipynb#{cell.id}", "exec"), namespace)
    cell.execution_count = execution_count
    cell.outputs = (
        [nbformat.v4.new_output("stream", name="stdout", text=capture.getvalue())]
        if capture.getvalue()
        else []
    )
notebook.metadata["execution"] = {
    "engine": "sequential plain Python cells; stdout captured; no Jupyter kernel",
    "python": platform.python_version(),
}
nbformat.validate(notebook)
nbformat.write(notebook, path)
print("Executed plain-Python notebook cells and captured their actual outputs.")
