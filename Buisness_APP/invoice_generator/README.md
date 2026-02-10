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