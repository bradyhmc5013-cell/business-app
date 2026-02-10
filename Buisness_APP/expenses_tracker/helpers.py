import os
import sys
from datetime import datetime, date

CATEGORIES = [
    "Fuel",
    "Parts",
    "Tools",
    "Repairs",
    "Supplies",
    "Insurance",
    "Registration",
    "Meals",
    "Phone/Internet",
    "Software",
    "Other",
]


def money(x: float) -> str:
    return f"${x:,.2f}"


def prompt_float(prompt: str) -> float:
    while True:
        raw = input(prompt).strip().replace("$", "").replace(",", "")
        try:
            val = float(raw)
            if val < 0:
                print("Enter a non-negative amount.")
                continue
            return val
        except ValueError:
            print("Enter a valid number (example: 12.50).")


def prompt_date(prompt: str) -> str:
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return date.today().isoformat()
        try:
            datetime.strptime(raw, "%Y-%m-%d")
            return raw
        except ValueError:
            print("Use YYYY-MM-DD (example: 2026-02-15) or press Enter for today.")


def pick_category() -> str:
    print("\nChoose a category:")
    for i, c in enumerate(CATEGORIES, start=1):
        print(f"{i}) {c}")
    while True:
        raw = input("> ").strip()
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(CATEGORIES):
                return CATEGORIES[idx - 1]
        print(f"Choose 1–{len(CATEGORIES)}.")


def month_key(date_str: str) -> str:
    return date_str[:7]


def sanitize_csv_cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        if value != "" and value[0] in ("=", "+", "-", "@"):
            return "'" + value
        return value
    return str(value)


def find_by_id(expenses: list[dict], expense_id: int) -> dict | None:
    for e in expenses:
        if e.get("id") == expense_id:
            return e
    return None


def prompt_receipt_path() -> str:
    return input("Receipt file path (optional, Enter to skip): ").strip().strip('"')


def open_receipt(path: str) -> None:
    if not path:
        print("No receipt attached.")
        return
    if not os.path.exists(path):
        print("Receipt file not found at that path.")
        return
    try:
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            import subprocess
            if sys.platform == "darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        print("Opened receipt.")
    except Exception as e:
        print(f"Could not open receipt: {e}")
