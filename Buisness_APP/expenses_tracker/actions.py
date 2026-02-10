import csv
from datetime import datetime, date

from storage import save_expenses, next_id
from helpers import (
    money, prompt_float, prompt_date, pick_category, month_key,
    sanitize_csv_cell, find_by_id, prompt_receipt_path, open_receipt
)


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

    if not bool(e.get("billable", False)) and not bool(e.get("billed", False)):
        print("Expense is not billable. Mark it billable first.")
        return

    e["billed"] = not bool(e.get("billed", False))
    if e["billed"]:
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
        w.writerow(["id", "date", "vendor", "category", "amount", "notes", "receipt_path", "billable", "billed"])

        for e in items_sorted:
            w.writerow([
                e.get("id", ""),
                sanitize_csv_cell(e.get("date", "")),
                sanitize_csv_cell(e.get("vendor", "")),
                sanitize_csv_cell(e.get("category", "")),
                f"{float(e.get('amount', 0.0)):.2f}",
                sanitize_csv_cell(e.get("notes", "")),
                sanitize_csv_cell(e.get("receipt_path", "")),
                "Y" if e.get("billable", False) else "N",
                "Y" if e.get("billed", False) else "N",
            ])

    print(f"Exported: {filename}")


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

    current_date = e.get("date", "")
    new_date = input(f"Date [{current_date}] (YYYY-MM-DD): ").strip()
    if new_date:
        try:
            datetime.strptime(new_date, "%Y-%m-%d")
            e["date"] = new_date
        except ValueError:
            print("Invalid date format. Keeping existing date.")

    current_vendor = e.get("vendor", "")
    new_vendor = input(f"Vendor [{current_vendor}]: ").strip()
    if new_vendor:
        e["vendor"] = new_vendor

    current_cat = e.get("category", "")
    change_cat = input(f"Category [{current_cat}] - change? (y/N): ").strip().lower()
    if change_cat == "y":
        e["category"] = pick_category()

    current_amount = float(e.get("amount", 0.0))
    new_amount = input(f"Amount [{current_amount}]: ").strip().replace("$", "").replace(",", "")
    if new_amount:
        try:
            val = float(new_amount)
            if val >= 0:
                e["amount"] = val
        except ValueError:
            print("Invalid number. Keeping existing amount.")

    current_notes = e.get("notes", "")
    new_notes = input(f"Notes [{current_notes}] (Enter=keep, '-'=clear): ").strip()
    if new_notes == "-":
        e["notes"] = ""
    elif new_notes != "":
        e["notes"] = new_notes

    current_receipt = e.get("receipt_path", "")
    print(f"\nReceipt currently: {current_receipt if current_receipt else '(none)'}")
    receipt_choice = input("Receipt: (k)eep, (u)pdate, (r)emove? [k]: ").strip().lower()
    if receipt_choice == "r":
        e["receipt_path"] = ""
    elif receipt_choice == "u":
        e["receipt_path"] = prompt_receipt_path()

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


def list_billable_unbilled(expenses: list[dict]) -> None:
    items = [e for e in expenses if bool(e.get("billable", False)) and not bool(e.get("billed", False))]
    if not items:
        print("No billable unbilled expenses found.")
        return

    items_sorted = sorted(items, key=lambda e: (e.get("date", ""), e.get("id", 0)))

    print("\nBillable (NOT billed yet)")
    print("ID  DATE        CATEGORY         VENDOR                AMOUNT     R")
    print("--  ----------  ---------------  --------------------  --------  -")
    for e in items_sorted:
        eid = str(e.get("id", "")).rjust(2)
        d = (e.get("date", "") or "")[:10].ljust(10)
        cat = (e.get("category", "") or "")[:15].ljust(15)
        vendor = (e.get("vendor", "") or "")[:20].ljust(20)
        amt = money(float(e.get("amount", 0.0))).rjust(8)
        r = "R" if e.get("receipt_path") else "-"
        print(f"{eid}  {d}  {cat}  {vendor}  {amt}  {r}")

    total = sum(float(e.get("amount", 0.0)) for e in items_sorted)
    print(f"\nCount: {len(items_sorted)}")
    print(f"Total billable unbilled: {money(total)}")
