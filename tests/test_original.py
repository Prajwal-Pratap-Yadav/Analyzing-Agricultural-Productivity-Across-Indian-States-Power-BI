"""Characterize original inputs before restructuring or deriving analytics."""
import csv
import hashlib
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OriginalInputs(unittest.TestCase):
    def test_original_bytes_are_preserved(self):
        for original, moved, digest in [
            ('crop_yield.csv', 'data/raw/crop_yield.csv', 'ab9bc356b1f8107d490376cec24450a0e2906322ad25788ab22fb32537ab1f8f'),
            ('Analysing Agricultural Productivity.pbix', 'powerbi/original/agricultural-productivity.pbix', '84c142e6dd8905e9b7e81c29af21878669594fb9b90537162638ca0f8b34a7ba'),
            ('LICENSE', 'LICENSE', '4aae2fc6f9d5f27cf556519461713d508e8d3f91bc2df951ebcbeb18670f0726'),
        ]:
            path = ROOT / (original if (ROOT / original).exists() else moved)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_baseline_grain_and_coverage(self):
        path = ROOT / 'crop_yield.csv'
        if not path.exists():
            path = ROOT / 'data/raw/crop_yield.csv'
        with path.open(newline='', encoding='utf-8') as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 19689)
        self.assertEqual(len({r['Crop'].strip() for r in rows}), 55)
        self.assertEqual(len({r['State'].strip() for r in rows}), 30)
        self.assertEqual({int(r['Crop_Year']) for r in rows}, set(range(1997, 2021)))
        grain = {(r['State'].strip(), r['Crop'].strip(), r['Crop_Year'], r['Season'].strip()) for r in rows}
        self.assertEqual(len(grain), len(rows))

    def test_report_is_self_contained_import_archive(self):
        path = ROOT / 'Analysing Agricultural Productivity.pbix'
        if not path.exists():
            path = ROOT / 'powerbi/original/agricultural-productivity.pbix'
        with zipfile.ZipFile(path) as archive:
            self.assertIsNone(archive.testzip())
            self.assertIn('DataModel', archive.namelist())
            self.assertIn('Report/Layout', archive.namelist())
            self.assertNotIn('Connections', archive.namelist())


if __name__ == '__main__':
    unittest.main()
