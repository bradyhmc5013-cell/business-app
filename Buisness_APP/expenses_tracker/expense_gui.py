import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date

try:
    from . import expense_core as core
except Exception:
    import expense_core as core


def safe_float(s: str, default=0.0) -> float:
    s = (s or "").strip().replace("$", "").replace(",", "")
    if s == "":
        return default
    try:
        v = float(s)
        if v < 0:
            return default
        return v
    except ValueError:
        return default


def is_valid_date(s: str) -> bool:
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except ValueError:
        return False


class ExpenseForm(tk.Toplevel):
    def __init__(self, master, title: str, categories: list[str], initial: dict | None = None):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self.categories = categories

        init = initial or {}
        init_date = init.get("date") or date.today().isoformat()

        self.var_date = tk.StringVar(value=init_date)
        self.var_vendor = tk.StringVar(value=init.get("vendor", ""))
        self.var_category = tk.StringVar(value=init.get("category", categories[0] if categories else "Other"))
        self.var_amount = tk.StringVar(value=str(init.get("amount", "")))
        self.var_notes = tk.StringVar(value=init.get("notes", ""))
        self.var_receipt = tk.StringVar(value=init.get("receipt_path", ""))
        self.var_billable = tk.BooleanVar(value=bool(init.get("billable", False)))
        self.var_billed = tk.BooleanVar(value=bool(init.get("billed", False)))

        pad = {"padx": 8, "pady": 6}
        frm = ttk.Frame(self)
        frm.grid(row=0, column=0, sticky="nsew", **pad)

        r = 0
        ttk.Label(frm, text="Date (YYYY-MM-DD)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_date, width=28).grid(row=r, column=1, sticky="w")
        r += 1

        ttk.Label(frm, text="Vendor").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_vendor, width=28).grid(row=r, column=1, sticky="w")
        r += 1

        ttk.Label(frm, text="Category").grid(row=r, column=0, sticky="w")
        cat = ttk.Combobox(frm, textvariable=self.var_category, values=categories, state="readonly", width=26)
        cat.grid(row=r, column=1, sticky="w")
        r += 1

        ttk.Label(frm, text="Amount").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_amount, width=28).grid(row=r, column=1, sticky="w")
        r += 1

        ttk.Label(frm, text="Notes").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_notes, width=28).grid(row=r, column=1, sticky="w")
        r += 1

        ttk.Label(frm, text="Receipt").grid(row=r, column=0, sticky="w")
        receipt_row = ttk.Frame(frm)
        receipt_row.grid(row=r, column=1, sticky="w")
        ttk.Entry(receipt_row, textvariable=self.var_receipt, width=20).grid(row=0, column=0, sticky="w")
        ttk.Button(receipt_row, text="Browse…", command=self.browse_receipt).grid(row=0, column=1, padx=6)
        ttk.Button(receipt_row, text="Clear", command=lambda: self.var_receipt.set("")).grid(row=0, column=2)
        r += 1

        flags = ttk.Frame(frm)
        flags.grid(row=r, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Checkbutton(flags, text="Billable", variable=self.var_billable, command=self.on_billable_toggle).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(flags, text="Billed", variable=self.var_billed, command=self.on_billed_toggle).grid(row=0, column=1, sticky="w", padx=(10, 0))
        r += 1

        btns = ttk.Frame(frm)
        btns.grid(row=r, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(btns, text="Cancel", command=self.cancel).grid(row=0, column=0, padx=6)
        ttk.Button(btns, text="Save", command=self.save).grid(row=0, column=1)

        self.bind("<Escape>", lambda e: self.cancel())
        self.bind("<Return>", lambda e: self.save())

        self.transient(master)
        self.grab_set()
        self.wait_visibility()
        self.focus()

    def browse_receipt(self):
        path = filedialog.askopenfilename(title="Select receipt")
        if path:
            self.var_receipt.set(path)

    def on_billable_toggle(self):
        if not self.var_billable.get():
            self.var_billed.set(False)

    def on_billed_toggle(self):
        # can't set billed true if not billable
        if self.var_billed.get() and not self.var_billable.get():
            self.var_billable.set(True)

    def cancel(self):
        self.result = None
        self.destroy()

    def save(self):
        d = self.var_date.get().strip()
        if not is_valid_date(d):
            messagebox.showerror("Invalid date", "Use YYYY-MM-DD (example: 2026-01-23).")
            return

        vendor = self.var_vendor.get().strip() or "Unknown"
        cat = self.var_category.get().strip() or "Other"
        amount = safe_float(self.var_amount.get().strip(), default=-1)
        if amount < 0:
            messagebox.showerror("Invalid amount", "Enter a valid non-negative number.")
            return

        self.result = {
            "date": d,
            "vendor": vendor,
            "category": cat,
            "amount": float(amount),
            "notes": self.var_notes.get().strip(),
            "receipt_path": self.var_receipt.get().strip(),
            "billable": bool(self.var_billable.get()),
            "billed": bool(self.var_billed.get()),
        }
        # enforce rule: billed implies billable
        if self.result["billed"]:
            self.result["billable"] = True
        self.destroy()


class App(ttk.Frame):
    def __init__(self, master: tk.Misc | None = None):
        # if no master provided, create a root window (standalone mode)
        if master is None:
            self._own_root = True
            self._root = tk.Tk()
            super().__init__(self._root)
            self._root.title("Expense Tracker")
            self._root.geometry("950x520")
            self.pack(fill="both", expand=True)
        else:
            self._own_root = False
            self._root = master
            super().__init__(master)

        self.expenses = []
        self.filtered = []

        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Filter Month (YYYY-MM or blank):").pack(side="left")
        self.var_month = tk.StringVar(value="")
        ttk.Entry(top, textvariable=self.var_month, width=10).pack(side="left", padx=6)

        self.var_only_billable = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Only billable", variable=self.var_only_billable).pack(side="left", padx=8)

        self.var_only_unbilled = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Only unbilled", variable=self.var_only_unbilled).pack(side="left", padx=8)

        ttk.Button(top, text="Apply", command=self.apply_filter).pack(side="left", padx=8)
        ttk.Button(top, text="Reload", command=self.reload).pack(side="left")
        ttk.Button(top, text="Import", command=self.import_expenses).pack(side="left", padx=8)

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=10, pady=6)

        ttk.Button(btns, text="Add", command=self.add_expense).pack(side="left")
        ttk.Button(btns, text="Edit Selected", command=self.edit_selected).pack(side="left", padx=6)
        ttk.Button(btns, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=6)
        ttk.Button(btns, text="Toggle Billable", command=self.toggle_billable_selected).pack(side="left", padx=12)
        ttk.Button(btns, text="Toggle Billed", command=self.toggle_billed_selected).pack(side="left", padx=6)
        ttk.Button(btns, text="Open Receipt", command=self.open_receipt_selected).pack(side="left", padx=12)

        cols = ("id", "date", "vendor", "category", "amount", "billable", "billed", "receipt", "notes")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)

        headings = {
            "id": "ID",
            "date": "Date",
            "vendor": "Vendor",
            "category": "Category",
            "amount": "Amount",
            "billable": "Billable",
            "billed": "Billed",
            "receipt": "Receipt",
            "notes": "Notes",
        }
        widths = {
            "id": 50,
            "date": 110,
            "vendor": 180,
            "category": 140,
            "amount": 100,
            "billable": 80,
            "billed": 70,
            "receipt": 70,
            "notes": 260,
        }

        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="w")

        # nicer alignment for amount/id
        self.tree.column("id", anchor="e")
        self.tree.column("amount", anchor="e")
        self.tree.column("billable", anchor="center")
        self.tree.column("billed", anchor="center")
        self.tree.column("receipt", anchor="center")

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        self.lbl_total = ttk.Label(bottom, text="Total: $0.00  |  Count: 0")
        self.lbl_total.pack(side="left")

        self.reload()

    def reload(self):
        self.expenses = core.load_expenses()
        self.apply_filter()

    def apply_filter(self):
        month = self.var_month.get().strip()
        only_billable = self.var_only_billable.get()
        only_unbilled = self.var_only_unbilled.get()

        items = self.expenses[:]

        if month:
            items = [e for e in items if (e.get("date", "")[:7] == month)]

        if only_billable:
            items = [e for e in items if bool(e.get("billable", False))]

        if only_unbilled:
            items = [e for e in items if not bool(e.get("billed", False))]

        items.sort(key=lambda e: (e.get("date", ""), e.get("id", 0)))
        self.filtered = items
        self.refresh_table()

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        total = 0.0
        for e in self.filtered:
            total += float(e.get("amount", 0.0))
            receipt_flag = "📎" if e.get("receipt_path") else "-"
            self.tree.insert(
                "",
                "end",
                iid=str(e.get("id")),
                values=(
                    e.get("id", ""),
                    e.get("date", ""),
                    e.get("vendor", ""),
                    e.get("category", ""),
                    f"{float(e.get('amount', 0.0)):.2f}",
                    "Y" if e.get("billable", False) else "N",
                    "Y" if e.get("billed", False) else "N",
                    receipt_flag,
                    (e.get("notes", "") or "")[:120],
                ),
            )

        self.lbl_total.config(text=f"Total: ${total:,.2f}  |  Count: {len(self.filtered)}")

    def get_selected_id(self) -> int | None:
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def add_expense(self):
        form = ExpenseForm(self, "Add Expense", getattr(core, "CATEGORIES", ["Other"]))
        if not form.result:
            return

        new_exp = form.result
        new_exp["id"] = core.next_id(self.expenses)
        self.expenses.append(new_exp)
        core.save_expenses(self.expenses)
        self.reload()

    def edit_selected(self):
        eid = self.get_selected_id()
        if eid is None:
            messagebox.showinfo("Edit", "Select an expense first.")
            return

        e = next((x for x in self.expenses if x.get("id") == eid), None)
        if not e:
            messagebox.showerror("Edit", "Expense not found.")
            return

        form = ExpenseForm(self, f"Edit Expense #{eid}", getattr(core, "CATEGORIES", ["Other"]), initial=e)
        if not form.result:
            return

        updated = form.result
        updated["id"] = eid  # keep ID
        # keep any unknown fields just in case
        for k, v in e.items():
            if k not in updated:
                updated[k] = v

        # replace in list
        for i, item in enumerate(self.expenses):
            if item.get("id") == eid:
                self.expenses[i] = updated
                break

        core.save_expenses(self.expenses)
        self.reload()

    def delete_selected(self):
        eid = self.get_selected_id()
        if eid is None:
            messagebox.showinfo("Delete", "Select an expense first.")
            return

        e = next((x for x in self.expenses if x.get("id") == eid), None)
        if not e:
            messagebox.showerror("Delete", "Expense not found.")
            return

        if not messagebox.askyesno("Delete", f"Delete expense #{eid} ({e.get('vendor','')} ${float(e.get('amount',0.0)):.2f})?"):
            return

        self.expenses = [x for x in self.expenses if x.get("id") != eid]
        core.save_expenses(self.expenses)
        self.reload()

    def toggle_billable_selected(self):
        eid = self.get_selected_id()
        if eid is None:
            messagebox.showinfo("Toggle", "Select an expense first.")
            return

        for e in self.expenses:
            if e.get("id") == eid:
                e["billable"] = not bool(e.get("billable", False))
                if not e["billable"]:
                    e["billed"] = False
                core.save_expenses(self.expenses)
                self.reload()
                return

        messagebox.showerror("Toggle", "Expense not found.")

    def toggle_billed_selected(self):
        eid = self.get_selected_id()
        if eid is None:
            messagebox.showinfo("Toggle", "Select an expense first.")
            return

        for e in self.expenses:
            if e.get("id") == eid:
                # only allow billed true if billable
                if not bool(e.get("billable", False)) and not bool(e.get("billed", False)):
                    messagebox.showinfo("Billed", "Not billable yet. Toggle billable first (or it will auto-enable).")
                    e["billable"] = True

                e["billed"] = not bool(e.get("billed", False))
                if e["billed"]:
                    e["billable"] = True
                core.save_expenses(self.expenses)
                self.reload()
                return

        messagebox.showerror("Toggle", "Expense not found.")

    def open_receipt_selected(self):
        eid = self.get_selected_id()
        if eid is None:
            messagebox.showinfo("Receipt", "Select an expense first.")
            return

        e = next((x for x in self.expenses if x.get("id") == eid), None)
        if not e:
            messagebox.showerror("Receipt", "Expense not found.")
            return

        path = e.get("receipt_path", "")
        if not path:
            messagebox.showinfo("Receipt", "No receipt attached.")
            return

        core.open_receipt(path)

    def import_expenses(self):
        path = filedialog.askopenfilename(title="Import expenses", filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return

        added = 0
        try:
            if path.lower().endswith('.json'):
                import json
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    messagebox.showerror("Import", "JSON file must contain a list of expenses.")
                    return
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    e = {
                        'date': item.get('date') or item.get('created_at') or '',
                        'vendor': item.get('vendor') or item.get('payee') or 'Unknown',
                        'category': item.get('category') or 'Other',
                        'amount': float(item.get('amount', 0.0) or 0.0),
                        'notes': item.get('notes', ''),
                        'receipt_path': item.get('receipt_path', '') or item.get('receipt', ''),
                        'billable': bool(item.get('billable', False)),
                        'billed': bool(item.get('billed', False)),
                    }
                    if not is_valid_date(e['date']):
                        e['date'] = date.today().isoformat()
                    e['id'] = core.next_id(self.expenses)
                    self.expenses.append(e)
                    added += 1
            else:
                import csv
                with open(path, 'r', encoding='utf-8') as f:
                    rdr = csv.DictReader(f)
                    for row in rdr:
                        d = (row.get('date') or row.get('Date') or '').strip()
                        if not is_valid_date(d):
                            d = date.today().isoformat()
                        vendor = (row.get('vendor') or row.get('Vendor') or row.get('payee') or 'Unknown').strip()
                        category = (row.get('category') or row.get('Category') or 'Other').strip()
                        amt = safe_float(row.get('amount') or row.get('Amount') or '0')
                        notes = (row.get('notes') or row.get('Notes') or '').strip()
                        receipt = (row.get('receipt_path') or row.get('Receipt') or '').strip()
                        bill = (row.get('billable') or row.get('Billable') or '').strip().lower() in ('1','true','y','yes')
                        billed = (row.get('billed') or row.get('Billed') or '').strip().lower() in ('1','true','y','yes')
                        e = {'date': d, 'vendor': vendor, 'category': category, 'amount': float(amt), 'notes': notes, 'receipt_path': receipt, 'billable': bill, 'billed': billed}
                        e['id'] = core.next_id(self.expenses)
                        self.expenses.append(e)
                        added += 1
        except Exception as exc:
            messagebox.showerror("Import", f"Error importing file: {exc}")
            return

        if added:
            core.save_expenses(self.expenses)
            self.reload()
            messagebox.showinfo("Import", f"Imported {added} expenses from {os.path.basename(path)}")
        else:
            messagebox.showinfo("Import", "No expenses were imported.")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    app.pack(fill="both", expand=True)
    root.mainloop()
