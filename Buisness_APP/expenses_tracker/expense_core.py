import json
import os
import csv
import sys
from datetime import datetime, date

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "expenses.json")

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


# ----------------------------
# Storage
# ----------------------------
def load_expenses() -> list[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def save_expenses(expenses: list[dict]) -> None:
    # Atomic write: write to a temp file then replace to avoid corruption
    tmp_path = DATA_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(expenses, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    try:
        os.replace(tmp_path, DATA_FILE)
    except Exception:
        # best-effort cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def next_id(expenses: list[dict]) -> int:
    if not expenses:
        return 1
    return max(e.get("id", 0) for e in expenses) + 1


# ----------------------------
# Helpers
# ----------------------------
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
    """
    Returns YYYY-MM-DD. Empty input uses today's date.
    """
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
    # YYYY-MM
    return date_str[:7]


def sanitize_csv_cell(value) -> str:
    """
    Sanitize a cell value for CSV export to avoid CSV/formula injection in
    spreadsheets. If the cell begins with one of =, +, -, @ prepend a single
    quote so spreadsheet apps treat it as text.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        if value != "" and value[0] in ("=", "+", "-", "@"):
            return "'" + value
        return value
    # non-strings -> convert to str
    return str(value)


def find_by_id(expenses: list[dict], expense_id: int) -> dict | None:
    for e in expenses:
        if e.get("id") == expense_id:
            return e
    return None


def prompt_receipt_path() -> str:
    """
    Receipt file path. Empty means 'no receipt'.
    Tip: drag-and-drop a file into Command Prompt to paste the full path.
    """
    return input("Receipt file path (optional, Enter to skip): ").strip().strip('"')

def open_receipt(path: str) -> None:
    if not path:
        print("No receipt attached.")
        return
    if not os.path.exists(path):
        print("Receipt file not found at that path.")
        return
    try:
        # Cross-platform open: Windows, macOS, Linux
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


# ----------------------------
# Core actions
# ----------------------------
def add_expense(expenses: list[dict]) -> None:
    print("\n--- Add Expense ---")
    d = prompt_date("Date (YYYY-MM-DD) [Enter=today]: ")
    vendor = input("Vendor (example: Shell, AutoZone): ").strip() or "Unknown"
    category = pick_category()
    amount = prompt_float("Amount: ")
    notes = input("Notes (optional): ").strip()
    receipt_path = prompt_receipt_path()


    expense = {
        "id": next_id(expenses),
        "date": d,
        "vendor": vendor,
        "category": category,
        "amount": amount,
        "notes": notes,
        "receipt_path": receipt_path,
        "billable": False,
        "billed": False,
}


    expenses.append(expense)
    save_expenses(expenses)
    print(f"Saved expense #{expense['id']}.")

def toggle_billable(expenses: list[dict]) -> None:
    raw = input("Enter expense ID to toggle billable: ").strip()
    if not raw.isdigit():
        print("Enter a valid ID number.")
        return

    eid = int(raw)
    e = find_by_id(expenses, eid)
    if not e:
        print("Expense not found.")
        return

    e["billable"] = not bool(e.get("billable", False))
    if not e["billable"]:
        # if it’s not billable, it can’t be billed
        e["billed"] = False

    save_expenses(expenses)
    print(f"Expense #{eid} billable set to {e['billable']}.")


def toggle_billed(expenses: list[dict]) -> None:
    raw = input("Enter expense ID to toggle billed: ").strip()
    if not raw.isdigit():
        print("Enter a valid ID number.")
        return

    eid = int(raw)
    e = find_by_id(expenses, eid)
    if not e:
        print("Expense not found.")
        return

    # Only allow setting billed=True if expense is billable
    if not bool(e.get("billable", False)) and not bool(e.get("billed", False)):
        print("Expense is not billable. Mark it billable first.")
        return

    e["billed"] = not bool(e.get("billed", False))
    if e["billed"]:
        # ensure billable is true when billing
        e["billable"] = True

    save_expenses(expenses)
    print(f"Expense #{eid} billed set to {e['billed']}.")


def list_expenses(expenses: list[dict], month: str | None = None) -> None:
    items = expenses
    if month:
        items = [e for e in expenses if month_key(e.get("date", "")) == month]

    if not items:
        print("No expenses found." if not month else f"No expenses found for {month}.")
        return

    items_sorted = sorted(items, key=lambda e: (e.get("date", ""), e.get("id", 0)))

    print("\nID  DATE        CATEGORY         VENDOR                AMOUNT     R  B")
    print("--  ----------  ---------------  --------------------  --------  -  -")
    for e in items_sorted:
        eid = str(e.get("id", "")).rjust(2)
        d = (e.get("date", "") or "")[:10].ljust(10)
        cat = (e.get("category", "") or "")[:15].ljust(15)
        vendor = (e.get("vendor", "") or "")[:20].ljust(20)
        amt = money(float(e.get("amount", 0.0))).rjust(8)
        r = "R" if e.get("receipt_path") else "-"
        b = "B" if e.get("billed", False) else "-"
        print(f"{eid}  {d}  {cat}  {vendor}  {amt}  {r}  {b}")

    total = sum(float(e.get("amount", 0.0)) for e in items_sorted)
    print(f"\nTotal: {money(total)}")
    if month:
        print(f"Month: {month}")


def monthly_summary(expenses: list[dict]) -> None:
    month = input("Month (YYYY-MM) or Enter=current month: ").strip()
    if month == "":
        month = date.today().isoformat()[:7]

    items = [e for e in expenses if month_key(e.get("date", "")) == month]
    if not items:
        print(f"No expenses found for {month}.")
        return

    total = sum(float(e.get("amount", 0.0)) for e in items)
    by_cat: dict[str, float] = {}
    for e in items:
        cat = e.get("category", "Other")
        by_cat[cat] = by_cat.get(cat, 0.0) + float(e.get("amount", 0.0))

    print(f"\n--- Summary for {month} ---")
    print(f"Total: {money(total)}\n")

    print("By Category:")
    for cat, amt in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
        print(f"- {cat}: {money(amt)}")


def export_csv(expenses: list[dict]) -> None:
    month = input("Export which month? (YYYY-MM) or Enter=ALL: ").strip()
    if month:
        items = [e for e in expenses if month_key(e.get("date", "")) == month]
        filename = f"expenses_{month}.csv"
    else:
        items = expenses[:]
        filename = "expenses_all.csv"

    if not items:
        print("Nothing to export.")
        return

    items_sorted = sorted(items, key=lambda e: (e.get("date", ""), e.get("id", 0)))

    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # include billable and billed; use Y/N for compatibility
        w.writerow(["id", "date", "vendor", "category", "amount", "notes", "receipt_path", "billable", "billed"])

        for e in items_sorted:
            # sanitize textual cells to prevent CSV formula injection
            date_cell = sanitize_csv_cell(e.get("date", ""))
            vendor_cell = sanitize_csv_cell(e.get("vendor", ""))
            category_cell = sanitize_csv_cell(e.get("category", ""))
            notes_cell = sanitize_csv_cell(e.get("notes", ""))
            receipt_cell = sanitize_csv_cell(e.get("receipt_path", ""))

            billable = "Y" if e.get("billable", False) else "N"
            billed = "Y" if e.get("billed", False) else "N"
            w.writerow([
                e.get("id", ""),
                date_cell,
                vendor_cell,
                category_cell,
                f"{float(e.get('amount', 0.0)):.2f}",
                notes_cell,
                receipt_cell,
                billable,
                billed,
            ])

    print(f"Exported: {filename}")

def edit_expense(expenses: list[dict]) -> None:
    raw = input("Enter expense ID to edit: ").strip()
    if not raw.isdigit():
        print("Enter a valid ID number.")
        return

    eid = int(raw)
    e = find_by_id(expenses, eid)
    if not e:
        print("Expense not found.")
        return

    print("\n--- Edit Expense ---")
    print("Press Enter to keep the current value.\n")

    # Date
    current_date = e.get("date", "")
    new_date = input(f"Date [{current_date}] (YYYY-MM-DD): ").strip()
    if new_date:
        try:
            datetime.strptime(new_date, "%Y-%m-%d")
            e["date"] = new_date
        except ValueError:
            print("Invalid date format. Keeping existing date.")

    # Vendor
    current_vendor = e.get("vendor", "")
    new_vendor = input(f"Vendor [{current_vendor}]: ").strip()
    if new_vendor:
        e["vendor"] = new_vendor

    # Category
    current_cat = e.get("category", "")
    change_cat = input(f"Category [{current_cat}] - change? (y/N): ").strip().lower()
    if change_cat == "y":
        e["category"] = pick_category()

    # Amount
    current_amount = float(e.get("amount", 0.0))
    new_amount = input(f"Amount [{current_amount}]: ").strip().replace("$", "").replace(",", "")
    if new_amount:
        try:
            val = float(new_amount)
            if val >= 0:
                e["amount"] = val
            else:
                print("Amount must be non-negative. Keeping existing amount.")
        except ValueError:
            print("Invalid number. Keeping existing amount.")
# Notes 
    current_notes = e.get("notes", "")
    new_notes = input(f"Notes [{current_notes}] (Enter=keep, '-'=clear): ").strip()
    if new_notes == "-":
        e["notes"] = ""
    elif new_notes != "":
        e["notes"] = new_notes

    # Receipt
    current_receipt = e.get("receipt_path", "")
    print(f"\nReceipt currently: {current_receipt if current_receipt else '(none)'}")
    receipt_choice = input("Receipt: (k)eep, (u)pdate, (r)emove? [k]: ").strip().lower()
    if receipt_choice in ("", "k"):
        pass
    elif receipt_choice == "r":
        e["receipt_path"] = ""
    elif receipt_choice == "u":
        e["receipt_path"] = prompt_receipt_path()
    else:
        print("Unknown choice. Keeping receipt.")

    save_expenses(expenses)
    print("Expense updated.")


def delete_expense(expenses: list[dict]) -> None:
    raw = input("Enter expense ID to delete: ").strip()
    if not raw.isdigit():
        print("Enter a valid ID number.")
        return
    eid = int(raw)
    e = find_by_id(expenses, eid)
    if not e:
        print("Expense not found.")
        return

    confirm = input(f"Delete expense #{eid} ({e.get('vendor')} {money(float(e.get('amount', 0.0)))})? (y/N): ").strip().lower()
    if confirm != "y":
        print("Canceled.")
        return

    expenses.remove(e)
    save_expenses(expenses)
    print("Deleted.")
def attach_or_update_receipt(expenses: list[dict]) -> None:
    raw = input("Enter expense ID to attach/update receipt: ").strip()
    if not raw.isdigit():
        print("Enter a valid ID number.")
        return
    eid = int(raw)
    e = find_by_id(expenses, eid)
    if not e:
        print("Expense not found.")
        return

    current = e.get("receipt_path", "")
    if current:
        print(f"Current receipt: {current}")
        action = input("Enter new path to replace, or Enter to remove: ").strip().strip('"')
        if action == "":
            e["receipt_path"] = ""
            save_expenses(expenses)
            print("Receipt removed.")
            return
        e["receipt_path"] = action
        save_expenses(expenses)
        print("Receipt updated.")
    else:
        new_path = prompt_receipt_path()
        e["receipt_path"] = new_path
        save_expenses(expenses)
        print("Receipt attached." if new_path else "No receipt attached.")


def open_expense_receipt(expenses: list[dict]) -> None:
    raw = input("Enter expense ID to open receipt: ").strip()
    if not raw.isdigit():
        print("Enter a valid ID number.")
        return
    eid = int(raw)
    e = find_by_id(expenses, eid)
    if not e:
        print("Expense not found.")
        return

    open_receipt(e.get("receipt_path", ""))

def list_billable_unbilled(expenses: list[dict]) -> None:
    items = [
        e for e in expenses
        if bool(e.get("billable", False)) and not bool(e.get("billed", False))
    ]

    if not items:
        print("No billable unbilled expenses found.")
        return

    items_sorted = sorted(items, key=lambda e: (e.get("date", ""), e.get("id", 0)))

    print("\nBillable (NOT billed yet)")
    print("ID  DATE        CATEGORY         VENDOR                AMOUNT   R")
    print("--  ----------  ---------------  --------------------  --------  -")
    for e in items_sorted:
        eid = str(e.get("id", "")).rjust(2)
        d = (e.get("date", "") or "")[:10].ljust(10)
        cat = (e.get("category", "") or "")[:15].ljust(15)
        vendor = (e.get("vendor", "") or "")[:20].ljust(20)
        amt = money(float(e.get("amount", 0.0))).rjust(8)
        r = "📎" if e.get("receipt_path") else "-"
        print(f"{eid}  {d}  {cat}  {vendor}  {amt}  {r}")

    total = sum(float(e.get("amount", 0.0)) for e in items_sorted)
    print(f"\nCount: {len(items_sorted)}")
    print(f"Total billable unbilled: {money(total)}")

def search_expenses(expenses: list[dict]) -> None:
    term = input("Search term (vendor/category/notes): ").strip().lower()
    if not term:
        print("Search term can't be empty.")
        return

    matches = []
    for e in expenses:
        vendor = str(e.get("vendor", "")).lower()
        category = str(e.get("category", "")).lower()
        notes = str(e.get("notes", "")).lower()
        if term in vendor or term in category or term in notes:
            matches.append(e)

    if not matches:
        print("No matches found.")
        return

    list_expenses(matches)

# ----------------------------
# Main loop
# ----------------------------
def main():
    expenses = load_expenses()

    while True:
        print("\nExpense Tracker")
        print("1) Add expense")
        print("2) List expenses (all)")
        print("3) List expenses (by month)")
        print("4) Monthly summary")
        print("5) List billable (not billed)")
        print("6) Search expenses")
        print("7) Export CSV")
        print("8) Attach / Update receipt")
        print("9) Open receipt")
        print("10) Toggle billable")
        print("11) Toggle billed")
        print("12) Edit expense")
        print("13) Delete expense")
        print("14) Quit")

        try:
            choice = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break

        if choice == "1":
            add_expense(expenses)
            expenses = load_expenses()

        elif choice == "2":
            list_expenses(expenses)

        elif choice == "3":
            m = input("Month (YYYY-MM): ").strip()
            if len(m) != 7 or m[4] != "-":
                print("Use YYYY-MM (example: 2026-01).")
            else:
                list_expenses(expenses, month=m)

        elif choice == "4":
            monthly_summary(expenses)

        elif choice == "5":
            list_billable_unbilled(expenses)

        elif choice == "6":
            search_expenses(expenses)

        elif choice == "7":
            export_csv(expenses)

        elif choice == "8":
            attach_or_update_receipt(expenses)
            expenses = load_expenses()

        elif choice == "9":
            open_expense_receipt(expenses)

        elif choice == "10":
            toggle_billable(expenses)
            expenses = load_expenses()

        elif choice == "11":
            toggle_billed(expenses)
            expenses = load_expenses()

        elif choice == "12":
            edit_expense(expenses)
            expenses = load_expenses()

        elif choice == "13":
            delete_expense(expenses)
            expenses = load_expenses()

        elif choice == "14":
            print("Goodbye.")
            break

        else:
            print("Choose 1–14.")


if __name__ == "__main__":
    main()
