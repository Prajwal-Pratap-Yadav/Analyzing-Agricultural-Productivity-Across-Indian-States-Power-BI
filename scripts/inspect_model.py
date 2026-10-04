"""Read-only original model inspection with sanitized source paths."""

import argparse
import csv
import hashlib
import json
import re
import zipfile
from decimal import Decimal
from pathlib import Path

from pbixray import PBIXRay

ROOT = Path(__file__).resolve().parents[1]


def inspect(output):
    path = ROOT / "powerbi/original/agricultural-productivity.pbix"
    model = PBIXRay(str(path))
    cached = model.get_table("crop_yield")
    schema = model.schema.to_dict("records")
    measures = model.dax_measures.to_dict("records")
    columns = model.dax_columns.to_dict("records")
    relations = model.relationships.to_dict("records")
    query = model.power_query.to_dict("records")
    for record in query:
        record["Expression"] = re.sub(
            r'File\.Contents\("(?:[^\"]|\"\")*"\)',
            'File.Contents("<LOCAL_SOURCE_PATH_REDACTED>")',
            record["Expression"],
        )
        if "C:\\" in record["Expression"] or "Users\\" in record["Expression"]:
            raise ValueError("Source path sanitizer did not cover the import expression")
    with zipfile.ZipFile(path) as archive:
        layout = json.loads(archive.read("Report/Layout").decode("utf-16-le"))
    pages = []
    for section in layout["sections"]:
        visuals = []
        for v in section["visualContainers"]:
            config = json.loads(v["config"])
            commands = json.loads(v.get("query", "{}")).get("Commands", [])
            selections = (
                commands[0]
                .get("SemanticQueryDataShapeCommand", {})
                .get("Query", {})
                .get("Select", [])
                if commands
                else []
            )
            visuals.append(
                {
                    "visual_id": config["name"],
                    "type": config.get("singleVisual", {}).get("visualType"),
                    "select": selections,
                }
            )
        pages.append(
            {"name": section["displayName"], "page_id": section["name"], "visuals": visuals}
        )
    with (ROOT / "data/raw/crop_yield.csv").open(newline="", encoding="utf-8") as handle:
        source = list(csv.DictReader(handle))

    def grain(record):
        return (
            str(record["Crop"]).strip(),
            int(record["Crop_Year"]),
            str(record["Season"]).strip(),
            str(record["State"]).strip(),
        )

    lookup = {grain(r): r for r in source}
    cached_records = cached.to_dict("records")
    if set(lookup) != {grain(r) for r in cached_records} or len(cached) != len(source):
        raise ValueError("Cached model/source grains differ; investigate before regeneration")
    area_changes = sum(
        Decimal(lookup[grain(r)]["Area"]) != Decimal(str(r["Area (In hectares)"]))
        for r in cached_records
    )
    average_rain = sum((Decimal(r["Annual_Rainfall"]) for r in source), Decimal(0)) / len(source)
    average_pesticide = sum((Decimal(r["Pesticide"]) for r in source), Decimal(0)) / len(source)
    comparison = {
        "scope": "Python arithmetic on unfiltered CSV and decoded cached table; not validated against Power BI output.",
        "csv_rows": len(source),
        "cached_rows": len(cached),
        "identical_label_grains": True,
        "fractional_area_values_changed_in_cache": area_changes,
        "csv_area_sum_diagnostic": str(sum((Decimal(r["Area"]) for r in source), Decimal(0))),
        "cached_area_sum_diagnostic": int(cached["Area (In hectares)"].sum()),
        "row_weighted_rainfall_average_csv": str(average_rain),
        "row_weighted_rainfall_average_cached": float(cached["Annual_Rainfall (In mm)"].mean()),
        "row_weighted_pesticide_average_csv": str(average_pesticide),
        "row_weighted_pesticide_average_cached": float(cached["Pesticide (In kg)"].mean()),
        "count_nonblank_rows": len(source),
        "distinct_crop_labels_trimmed": len({r["Crop"].strip() for r in source}),
        "distinct_state_labels_trimmed": len({r["State"].strip() for r in source}),
        "distinct_years": len({r["Crop_Year"] for r in source}),
        "distinct_seasons_trimmed": len({r["Season"].strip() for r in source}),
        "limitations": "No DAX engine, report interaction, visual result or rendering was executed. Inline aliases may differ from display labels. Means are weighted by source rows, not a national weather/pesticide estimate. No cross-crop production or yield totals are interpreted.",
    }
    catalog = {
        "pbix_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "inspection_tool": "pbixray==0.15.5",
        "tables": list(model.tables),
        "schema": schema,
        "explicit_dax_measures": measures,
        "calculated_columns": columns,
        "relationships": relations,
        "power_query_sanitized": query,
        "pages": pages,
    }
    output.mkdir(parents=True, exist_ok=True)
    for filename, payload in [
        ("catalog.json", catalog),
        ("arithmetic-crosschecks.json", comparison),
    ]:
        (output / filename).write_text(
            json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
        )
    print(
        f"Read-only extraction: {len(model.tables)} table; {len(measures)} explicit measures; {len(pages)} pages; {area_changes} cached area changes."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/model")
    inspect(parser.parse_args().output)
