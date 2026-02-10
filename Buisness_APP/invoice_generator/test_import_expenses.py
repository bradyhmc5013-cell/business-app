import json
import os
import sys
from unittest.mock import patch

# Ensure project root is on sys.path so package imports work when running this script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from invoice_generator.invoice_GUI.invoice_gui import InvoiceGUI, load_expenses_file

# Prepare sample expenses file next to this script
path = os.path.join(os.path.dirname(__file__), "test_expenses.json")
expenses = [
    {"vendor": "Vendor A", "category": "Services", "amount": 100.0, "billable": True, "billed": False},
    {"vendor": "Vendor B", "category": "Goods", "amount": 50.5, "billable": True, "billed": False},
    {"vendor": "Vendor C", "category": "Misc", "amount": 25.0, "billable": False, "billed": False},
]
with open(path, "w", encoding="utf-8") as f:
    json.dump(expenses, f, indent=2)

# Patch the file dialog to return our test file path
with patch('invoice_generator.invoice_GUI.invoice_gui.filedialog.askopenfilename', return_value=path):
    app = InvoiceGUI()
    app.new_invoice()
    app.import_expenses()
    print("Items on invoice:", len(app.current.get("items", [])))
    exp_after = load_expenses_file(path)
    billed_count = sum(1 for e in exp_after if e.get('billed'))
    print("Expenses billed:", billed_count)

# Note: keep the test file for inspection
