Expense Tracker
===============

<!-- Replace OWNER/REPO in the badge URL with your repository path -->
![CI](https://github.com/OWNER/REPO/actions/workflows/python-tests.yml/badge.svg)

Small CLI expense tracker script.

Requirements
------------
- Python 3.10+ (uses modern type annotations)
- Windows recommended for receipt-opening (`os.startfile` is Windows-only)

Quick start
-----------
Run:

```bash
python expense_tracker.py
```

Notes
-----
- Data is stored in `expenses.json` in the same folder.
- Receipt opening uses the default OS handler; on non-Windows platforms this feature will not work.
- No external dependencies.

- CSV export now includes a `billed` column (boolean) indicating whether an expense
- CSV export now includes `billable` and `billed` columns indicating billing state.
  Values are `Y` or `N` in the exported CSV for better spreadsheet compatibility.

Other changes:
- Atomic saves: `save_expenses` now writes to a temp file and renames to avoid corruption.
- Cross-platform receipt opening: works on Windows/macOS/Linux where available.

Suggested improvements
----------------------
- Use atomic saves (temp file + rename) for robustness.
- Add cross-platform receipt opening.
- Validate receipt paths at entry time.
# Invoice Generator

Simple command-line invoice generator.

Quick start (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\.venv\Scripts\python.exe invoice_generator.py
```

Files to keep:
- `invoice_generator.py` — main program
- `business_info.json` — saved business info
- `invoices.json` — stored invoices

Dependencies:
- `reportlab` (for PDF export)

If you want, I can initialize a git repo and commit these files.
