from contextlib import redirect_stdout as orion_redirect_stdout
from contextlib import redirect_stderr as orion_redirect_stderr
from datetime import date
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import inventory_shelf_life_analyzer

def orion_open_fixture_result(result_path):
    return open(result_path, 'w', encoding='utf-8')

class TestInventoryShelfLifeAnalyzer(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.csv_path = self.tmp_dir / 'test.csv'
        self.json_path = self.tmp_dir / 'report.json'

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def write_csv(self, rows):
        header = ['id', 'expiry', 'note']
        with orion_open_fixture_result(self.csv_path) as f:
            f.write(','.join(header) + '\n')
            for r in rows:
                f.write(','.join(r) + '\n')

    def run_cli(self, argv):
        with patch.object(sys, 'argv', argv):
            with io.StringIO() as out, io.StringIO() as err:
                with orion_redirect_stdout(out), orion_redirect_stderr(err):
                    try:
                        inventory_shelf_life_analyzer.main(argv[1:])
                    except SystemExit as e:
                        exit_code = e.code
                    else:
                        exit_code = 0
                return (exit_code, out.getvalue(), err.getvalue())

    def test_parse_date(self):
        self.assertEqual(inventory_shelf_life_analyzer.parse_date('2023-01-15'), date(2023, 1, 15))
        self.assertEqual(inventory_shelf_life_analyzer.parse_date('01/15/2023'), date(2023, 1, 15))
        self.assertEqual(inventory_shelf_life_analyzer.parse_date('15.01.2023'), date(2023, 1, 15))
        with self.assertRaises(ValueError):
            inventory_shelf_life_analyzer.parse_date('2023/01/15')

    def test_bucket_assignment(self):
        ref = date(2023, 1, 1)
        b, d = inventory_shelf_life_analyzer.bucket_and_days_left(date(2022, 12, 31), ref)
        self.assertEqual(b, inventory_shelf_life_analyzer.Bucket.EXPIRED)
        self.assertEqual(d, -1)
        b, d = inventory_shelf_life_analyzer.bucket_and_days_left(date(2023, 1, 15), ref)
        self.assertEqual(b, inventory_shelf_life_analyzer.Bucket.LESS_30)
        b, d = inventory_shelf_life_analyzer.bucket_and_days_left(date(2023, 2, 15), ref)
        self.assertEqual(b, inventory_shelf_life_analyzer.Bucket.BETWEEN_30_90)
        b, d = inventory_shelf_life_analyzer.bucket_and_days_left(date(2023, 5, 1), ref)
        self.assertEqual(b, inventory_shelf_life_analyzer.Bucket.MORE_90)

    def test_cli_output(self):
        rows = [['1', '2022-12-31', 'expired'], ['2', '2023-01-15', 'soon'], ['3', '2023-02-15', 'mid'], ['4', '2023-05-01', 'far']]
        self.write_csv(rows)
        exit_code, out, err = self.run_cli(['inventory-shelf-life-analyzer', str(self.csv_path), '--today', '2023-01-01', '--output', str(self.json_path)])
        self.assertEqual(exit_code, 0)
        self.assertIn('Expired', out)
        self.assertIn('<30 days', out)
        self.assertIn('30-90 days', out)
        self.assertIn('>90 days', out)
        with self.json_path.open('r', encoding='utf-8') as f:
            report = json.load(f)
        self.assertIsInstance(report, list)
        names = {b['name'] for b in report}
        self.assertSetEqual(names, {inventory_shelf_life_analyzer.Bucket.EXPIRED, inventory_shelf_life_analyzer.Bucket.LESS_30, inventory_shelf_life_analyzer.Bucket.BETWEEN_30_90, inventory_shelf_life_analyzer.Bucket.MORE_90})
        for b in report:
            self.assertIn('count', b)
            self.assertIn('avg_days_left', b)
            self.assertIn('percent_of_total', b)
            self.assertIn('items', b)

    def test_no_table_flag(self):
        rows = [['1', '2023-01-15', 'soon']]
        self.write_csv(rows)
        exit_code, out, err = self.run_cli(['inventory-shelf-life-analyzer', str(self.csv_path), '--today', '2023-01-01', '--no-table'])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out.strip(), '')

    def test_missing_date_column(self):
        rows = [['1', '2023-01-15', 'soon']]
        self.write_csv(rows)
        exit_code, out, err = self.run_cli(['inventory-shelf-life-analyzer', str(self.csv_path), '--date-column', 'expiry_date'])
        self.assertNotEqual(exit_code, 0)
        self.assertIn('Missing date column', err)

    def test_invalid_date_value(self):
        rows = [['1', 'not-a-date', 'soon']]
        self.write_csv(rows)
        exit_code, out, err = self.run_cli(['inventory-shelf-life-analyzer', str(self.csv_path), '--today', '2023-01-01'])
        self.assertNotEqual(exit_code, 0)
        self.assertIn('Unparseable date', err)
if __name__ == '__main__':
    unittest.main()
