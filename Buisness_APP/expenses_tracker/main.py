from storage import load_expenses
from actions import (
    add_expense, list_expenses, monthly_summary, export_csv,
    attach_or_update_receipt, open_expense_receipt,
    toggle_billable, toggle_billed, edit_expense, delete_expense,
    list_billable_unbilled
)

# Optional: If you don't have search yet, comment out choice 6.
def search_expenses(expenses: list[dict]) -> None:
    q = input("Search (vendor/category/notes): ").strip().lower()
    if not q:
        print("Nothing to search.")
        return
    hits = [
        e for e in expenses
        if q in str(e.get("vendor","")).lower()
        or q in str(e.get("category","")).lower()
        or q in str(e.get("notes","")).lower()
    ]
    if not hits:
        print("No matches.")
        return
    list_expenses(hits)


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
