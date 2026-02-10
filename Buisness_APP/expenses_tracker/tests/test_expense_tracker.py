import os
import io
import json
import unittest
import tempfile
from unittest import mock

import expense_core

class TestExpenseTracker(unittest.TestCase):
    def setUp(self):
        # prevent writes to real data file during tests
        expense_core.save_expenses = lambda expenses: None

    def test_toggle_billable_toggles_and_clears_billed(self):
        expenses = [{
            "id": 1,
            "billable": True,
            "billed": True,
        }]
        with mock.patch("builtins.input", return_value="1"):
            expense_core.toggle_billable(expenses)
        self.assertFalse(expenses[0]["billable"])
        self.assertFalse(expenses[0]["billed"])  # cleared when un-billable

    def test_toggle_billed_requires_billable(self):
        expenses = [{
            "id": 1,
            "billable": False,
            "billed": False,
        }]
        with mock.patch("builtins.input", return_value="1"), mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
            expense_core.toggle_billed(expenses)
            out = fake_out.getvalue()
        self.assertIn("not billable", out)
        self.assertFalse(expenses[0]["billed"])

    def test_toggle_billed_sets_billed_when_billable(self):
        expenses = [{
            "id": 1,
            "billable": True,
            "billed": False,
        }]
        with mock.patch("builtins.input", return_value="1"):
            expense_core.toggle_billed(expenses)
        self.assertTrue(expenses[0]["billed"]) 

    def test_export_csv_includes_billable_billed(self):
        sample = [
            {"id": 1, "date": "2026-01-10", "vendor": "Shell", "category": "Fuel", "amount": 45.6, "notes": "", "receipt_path": "", "billable": False, "billed": False},
            {"id": 2, "date": "2026-01-11", "vendor": "AutoZone", "category": "Parts", "amount": 123.45, "notes": "", "receipt_path": "C:/tmp/r.png", "billable": True, "billed": True},
        ]
        # run in a temp directory to avoid polluting the repo
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as td:
            os.chdir(td)
            with mock.patch("builtins.input", return_value=""):
                expense_core.export_csv(sample)
            # verify file created
            fn = os.path.join(td, "expenses_all.csv")
            self.assertTrue(os.path.exists(fn))
            with open(fn, "r", encoding="utf-8") as f:
                content = f.read()
            # header contains billable,billed and rows contain Y/N
            self.assertIn("billable,billed", content)
            self.assertIn(",Y,Y", content)
            self.assertIn(",N,N", content)
            os.chdir(cwd)

    def test_export_csv_sanitizes_formula_cells(self):
        sample = [
            {"id": 1, "date": "2026-01-10", "vendor": "=1+1", "category": "Fuel", "amount": 10.0, "notes": "", "receipt_path": "", "billable": False, "billed": False},
        ]
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as td:
            os.chdir(td)
            with mock.patch("builtins.input", return_value=""):
                expense_core.export_csv(sample)
            fn = os.path.join(td, "expenses_all.csv")
            with open(fn, "r", encoding="utf-8") as f:
                content = f.read()
            # the dangerous vendor cell should be prefixed with a single quote
            self.assertIn("'==1+1".replace("==","="), content) or self.assertIn("'=1+1", content)
            os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
