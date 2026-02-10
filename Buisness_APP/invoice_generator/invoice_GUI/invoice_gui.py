import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "invoices.json")
BUSINESS_FILE = os.path.join(APP_DIR, "business_info.json")
DEFAULT_TAX_RATE = 0.08


# ----------------------------
# Storage
# ----------------------------
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default


def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load_business_info():
    info = load_json(BUSINESS_FILE, {})
    if not isinstance(info, dict):
        return {}
    return info


def save_business_info(info):
    save_json(BUSINESS_FILE, info)


def load_all_invoices():
    invoices = load_json(DATA_FILE, [])
    if not isinstance(invoices, list):
        invoices = []

    # migrate older shape if needed
    for inv in invoices:
        if "business" not in inv:
            inv["business"] = {
                "name": inv.get("business_name", "My Business"),
                "address": "",
                "phone": "",
                "email": "",
            }
        inv.pop("business_name", None)
        inv.setdefault("items", [])
        inv.setdefault("notes", "")
        inv.setdefault("due_date", "")
        inv.setdefault("status", "UNPAID")
        inv.setdefault("tax_rate", DEFAULT_TAX_RATE)

    return invoices


def save_all_invoices(invoices):
    save_json(DATA_FILE, invoices)


def next_invoice_number(invoices):
    if not invoices:
        return 1001
    return max(int(inv.get("invoice_number", 1000)) for inv in invoices) + 1


# ----------------------------
# Helpers
# ----------------------------
def load_expenses_file(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def save_expenses_file(path: str, expenses: list[dict]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(expenses, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def money2(x):
    return f"${float(x):,.2f}"


def calculate_totals(items, tax_rate):
    subtotal = 0.0
    for it in items:
        subtotal += float(it.get("qty", 0)) * float(it.get("unit_price", 0.0))
    tax = subtotal * float(tax_rate)
    total = subtotal + tax
    return subtotal, tax, total


def safe_filename(name: str) -> str:
    keep = []
    for ch in (name or ""):
        if ch.isalnum() or ch in (" ", "_", "-", "."):
            keep.append(ch)
    s = "".join(keep).strip().replace(" ", "_")
    return s or "Invoice"


def export_invoice_txt(invoice: dict, out_dir: str) -> str:
    biz = invoice.get("business", {})
    page_width = 72
    line = "-" * page_width

    def center(text: str) -> str:
        return str(text).center(page_width)

    desc_w, qty_w, unit_w, line_w = 40, 6, 10, 12

    def fit(text: str, width: int) -> str:
        text = str(text)
        return text if len(text) <= width else text[: width - 3] + "..."

    subtotal, tax, total = calculate_totals(invoice.get("items", []), invoice.get("tax_rate", DEFAULT_TAX_RATE))

    out = []
    out.append(center(biz.get("name", "My Business")))
    if biz.get("address"):
        out.append(center(biz.get("address")))

    contact = " | ".join([x for x in [biz.get("phone", ""), biz.get("email", "")] if x])
    if contact:
        out.append(center(contact))

    out.append(line)

    left = f"Bill To: {invoice.get('customer_name','')}"
    right = f"Invoice #: {invoice.get('invoice_number','')}   Date: {invoice.get('created_at','')}"
    if len(left) + len(right) + 1 <= page_width:
        out.append(left + (" " * (page_width - len(left) - len(right))) + right)
    else:
        out.append(left)
        out.append(right)

    # status + due date under header line
    out.append(f"Status: {invoice.get('status','UNPAID')}")
    if invoice.get("due_date"):
        out.append(f"Due Date: {invoice.get('due_date')}")

    out.append(line)

    out.append(
        f"{'DESCRIPTION'.ljust(desc_w)} "
        f"{'QTY'.rjust(qty_w)} "
        f"{'UNIT'.rjust(unit_w)} "
        f"{'LINE'.rjust(line_w)}"
    )
    out.append(line)

    items = invoice.get("items", [])
    if not items:
        out.append("(No items)")
    else:
        for item in items:
            desc = fit(item.get("description", ""), desc_w)
            qty = int(item.get("qty", 0))
            unit = float(item.get("unit_price", 0.0))
            lt = qty * unit
            out.append(
                f"{desc.ljust(desc_w)} "
                f"{str(qty).rjust(qty_w)} "
                f"{money2(unit).rjust(unit_w)} "
                f"{money2(lt).rjust(line_w)}"
            )

    out.append(line)
    label_w = page_width - 14
    out.append(f"{'Subtotal:'.rjust(label_w)} {money2(subtotal).rjust(14)}")
    out.append(f"{'Tax:'.rjust(label_w)} {money2(tax).rjust(14)}")
    out.append(f"{'TOTAL:'.rjust(label_w)} {money2(total).rjust(14)}")

    if invoice.get("notes"):
        out.append("")
        out.append("Notes:")
        out.append(invoice["notes"])

    out.append("")
    out.append(center("Thank you for your business!"))

    biz_name = safe_filename(biz.get("name", "My Business"))
    filename = f"{biz_name}_Invoice_{invoice.get('invoice_number','')}.txt"
    path = os.path.join(out_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    return path


# ----------------------------
# GUI
# ----------------------------
class InvoiceGUI(ttk.Frame):
    def __init__(self, master: tk.Misc | None = None):
        # support embedding as a Frame; if no master provided, create root
        if master is None:
            self._own_root = True
            self._root = tk.Tk()
            super().__init__(self._root)
            self._root.title("Invoice Generator (GUI)")
            self._root.geometry("980x640")
            self.pack(fill="both", expand=True)
        else:
            self._own_root = False
            self._root = master
            super().__init__(master)

        self.invoices = load_all_invoices()
        self.business = load_business_info()

        self.current = None  # current invoice dict

        self._build_ui()
        self._refresh_invoice_list()

    def import_expenses(self):
        if not self.current:
            messagebox.showinfo("Import", "Create or load an invoice first.")
            return

        expenses_path = filedialog.askopenfilename(
            title="Select expenses.json",
            filetypes=[("JSON files", "*.json")]
        )
        if not expenses_path:
            return

        expenses = load_expenses_file(expenses_path)

        billable = [
            e for e in expenses
            if e.get("billable") and not e.get("billed")
        ]

        if not billable:
            messagebox.showinfo("Import", "No billable unbilled expenses found.")
            return
        
        added = 0
        for e in billable:
            desc = f"{e.get('vendor','Expense')} ({e.get('category','')})"
            amount = float(e.get("amount", 0.0))

            self.current["items"].append({
                "description": desc,
                "qty": 1,
                "unit_price": amount,
            })

            e["billed"] = True
            added += 1

        save_expenses_file(expenses_path, expenses)

        self._refresh_items_table()
        self._refresh_totals()

        messagebox.showinfo(
            "Imported",
            f"Imported {added} expenses and marked them as billed."
        )


    def _build_ui(self):
        # Top toolbar
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Button(top, text="New Invoice", command=self.new_invoice).pack(side="left")
        ttk.Button(top, text="Load Selected", command=self.load_selected).pack(side="left", padx=6)
        ttk.Button(top, text="Save Invoice", command=self.save_current).pack(side="left", padx=6)
        ttk.Button(top, text="Delete Invoice", command=self.delete_current).pack(side="left", padx=6)
        ttk.Button(top, text="Export TXT", command=self.export_txt).pack(side="left", padx=6)
        ttk.Button(top, text="Import Expenses", command=self.import_expenses).pack(side="left", padx=6)

        ttk.Button(top, text="Edit Business Info", command=self.edit_business_dialog).pack(side="right")

        # Left: invoice list
        left = ttk.Frame(self)
        left.pack(side="left", fill="y", padx=(10, 5), pady=10)

        ttk.Label(left, text="Saved Invoices").pack(anchor="w")
        self.invoice_list = tk.Listbox(left, width=34, height=26)
        self.invoice_list.pack(fill="y", pady=6)

        # Right: editor
        right = ttk.Frame(self)
        right.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)

        # Header fields
        header = ttk.LabelFrame(right, text="Invoice Details")
        header.pack(fill="x", padx=2, pady=2)

        self.var_number = tk.StringVar()
        self.var_created = tk.StringVar()
        self.var_customer = tk.StringVar()
        self.var_tax = tk.StringVar(value=str(DEFAULT_TAX_RATE))
        self.var_due = tk.StringVar()
        self.var_status = tk.StringVar(value="UNPAID")

        row1 = ttk.Frame(header)
        row1.pack(fill="x", padx=8, pady=6)
        ttk.Label(row1, text="Invoice #:").pack(side="left")
        ttk.Entry(row1, textvariable=self.var_number, width=10, state="readonly").pack(side="left", padx=5)
        ttk.Label(row1, text="Created:").pack(side="left", padx=(15, 0))
        ttk.Entry(row1, textvariable=self.var_created, width=22, state="readonly").pack(side="left", padx=5)

        row2 = ttk.Frame(header)
        row2.pack(fill="x", padx=8, pady=6)
        ttk.Label(row2, text="Customer:").pack(side="left")
        ttk.Entry(row2, textvariable=self.var_customer, width=28).pack(side="left", padx=5)
        ttk.Label(row2, text="Tax rate:").pack(side="left", padx=(15, 0))
        ttk.Entry(row2, textvariable=self.var_tax, width=10).pack(side="left", padx=5)
        ttk.Label(row2, text="Due date (YYYY-MM-DD):").pack(side="left", padx=(15, 0))
        ttk.Entry(row2, textvariable=self.var_due, width=14).pack(side="left", padx=5)

        row3 = ttk.Frame(header)
        row3.pack(fill="x", padx=8, pady=6)
        ttk.Label(row3, text="Status:").pack(side="left")
        self.status_combo = ttk.Combobox(row3, textvariable=self.var_status, values=["UNPAID", "PAID"], width=10, state="readonly")
        self.status_combo.pack(side="left", padx=5)

        # Items table
        items_box = ttk.LabelFrame(right, text="Items")
        items_box.pack(fill="both", expand=True, padx=2, pady=(8, 2))

        self.tree = ttk.Treeview(items_box, columns=("desc", "qty", "unit", "line"), show="headings", height=14)
        self.tree.heading("desc", text="Description")
        self.tree.heading("qty", text="Qty")
        self.tree.heading("unit", text="Unit Price")
        self.tree.heading("line", text="Line Total")
        self.tree.column("desc", width=420)
        self.tree.column("qty", width=80, anchor="e")
        self.tree.column("unit", width=120, anchor="e")
        self.tree.column("line", width=120, anchor="e")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        controls = ttk.Frame(items_box)
        controls.pack(fill="x", padx=8, pady=(0, 8))

        ttk.Button(controls, text="Add Item", command=self.add_item_dialog).pack(side="left")
        ttk.Button(controls, text="Remove Selected Item", command=self.remove_selected_item).pack(side="left", padx=6)

        # Notes + totals
        bottom = ttk.Frame(right)
        bottom.pack(fill="x", padx=2, pady=(8, 2))

        notes_box = ttk.LabelFrame(bottom, text="Notes")
        notes_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.notes = tk.Text(notes_box, height=6)
        self.notes.pack(fill="both", expand=True, padx=8, pady=8)

        totals_box = ttk.LabelFrame(bottom, text="Totals")
        totals_box.pack(side="right", fill="y")

        self.lbl_sub = ttk.Label(totals_box, text="Subtotal: $0.00")
        self.lbl_tax = ttk.Label(totals_box, text="Tax: $0.00")
        self.lbl_total = ttk.Label(totals_box, text="TOTAL: $0.00", font=("Segoe UI", 10, "bold"))

        self.lbl_sub.pack(anchor="e", padx=12, pady=(10, 2))
        self.lbl_tax.pack(anchor="e", padx=12, pady=2)
        self.lbl_total.pack(anchor="e", padx=12, pady=(2, 10))

        self._set_editor_enabled(False)

    def _set_editor_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for w in [self.notes]:
            w.configure(state=state)

        # entries (customer/tax/due) should toggle
        # easiest: enable/disable by setting state on children we care about
        # (readonly entries we leave)
        # We'll just block actions if no current invoice.

    def _refresh_invoice_list(self):
        self.invoice_list.delete(0, tk.END)
        for inv in sorted(self.invoices, key=lambda x: int(x.get("invoice_number", 0))):
            num = inv.get("invoice_number", "")
            cust = inv.get("customer_name", "")
            status = inv.get("status", "UNPAID")
            self.invoice_list.insert(tk.END, f"#{num} | {cust} | {status}")

    def _load_into_editor(self, inv: dict):
        self.current = inv

        self.var_number.set(str(inv.get("invoice_number", "")))
        self.var_created.set(inv.get("created_at", ""))
        self.var_customer.set(inv.get("customer_name", ""))
        self.var_tax.set(str(inv.get("tax_rate", DEFAULT_TAX_RATE)))
        self.var_due.set(inv.get("due_date", ""))
        self.var_status.set(inv.get("status", "UNPAID"))

        self.notes.configure(state="normal")
        self.notes.delete("1.0", tk.END)
        self.notes.insert("1.0", inv.get("notes", ""))
        self.notes.configure(state="normal")

        self._refresh_items_table()
        self._refresh_totals()

    def _refresh_items_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        if not self.current:
            return
        for it in self.current.get("items", []):
            qty = int(it.get("qty", 0))
            unit = float(it.get("unit_price", 0.0))
            line = qty * unit
            self.tree.insert("", tk.END, values=(it.get("description", ""), qty, money2(unit), money2(line)))

    def _refresh_totals(self):
        if not self.current:
            self.lbl_sub.config(text="Subtotal: $0.00")
            self.lbl_tax.config(text="Tax: $0.00")
            self.lbl_total.config(text="TOTAL: $0.00")
            return
        try:
            tax_rate = float(self.var_tax.get().strip())
        except ValueError:
            tax_rate = DEFAULT_TAX_RATE
        subtotal, tax, total = calculate_totals(self.current.get("items", []), tax_rate)
        self.lbl_sub.config(text=f"Subtotal: {money2(subtotal)}")
        self.lbl_tax.config(text=f"Tax: {money2(tax)}")
        self.lbl_total.config(text=f"TOTAL: {money2(total)}")

    def new_invoice(self):
        # ensure business exists
        if not self.business:
            if messagebox.askyesno("Business Info", "No business info saved. Set it up now?"):
                self.edit_business_dialog()
            self.business = load_business_info()

        inv_num = next_invoice_number(self.invoices)
        inv = {
            "invoice_number": inv_num,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "business": self.business if self.business else {"name": "My Business", "address": "", "phone": "", "email": ""},
            "customer_name": "Customer",
            "tax_rate": DEFAULT_TAX_RATE,
            "items": [],
            "notes": "",
            "due_date": "",
            "status": "UNPAID",
        }
        self._load_into_editor(inv)

    def load_selected(self):
        sel = self.invoice_list.curselection()
        if not sel:
            messagebox.showinfo("Load", "Select an invoice on the left first.")
            return
        idx = sel[0]
        inv = sorted(self.invoices, key=lambda x: int(x.get("invoice_number", 0)))[idx]
        self._load_into_editor(inv)

    def save_current(self):
        if not self.current:
            messagebox.showinfo("Save", "Create or load an invoice first.")
            return

        # pull UI fields into invoice
        self.current["customer_name"] = self.var_customer.get().strip() or "Customer"
        self.current["status"] = self.var_status.get().strip() or "UNPAID"
        self.current["due_date"] = self.var_due.get().strip()

        try:
            self.current["tax_rate"] = float(self.var_tax.get().strip())
        except ValueError:
            self.current["tax_rate"] = DEFAULT_TAX_RATE

        self.current["notes"] = self.notes.get("1.0", tk.END).strip()

        # upsert into invoices list by invoice_number
        existing = None
        for inv in self.invoices:
            if int(inv.get("invoice_number", -1)) == int(self.current.get("invoice_number", -2)):
                existing = inv
                break
        if existing is None:
            self.invoices.append(self.current)
        else:
            i = self.invoices.index(existing)
            self.invoices[i] = self.current

        save_all_invoices(self.invoices)
        self._refresh_invoice_list()
        self._refresh_totals()
        messagebox.showinfo("Saved", "Invoice saved to invoices.json")

    def delete_current(self):
        if not self.current:
            messagebox.showinfo("Delete", "Create or load an invoice first.")
            return

        num = self.current.get("invoice_number")
        if not messagebox.askyesno("Delete", f"Delete invoice #{num}? This cannot be undone."):
            return

        # remove from list
        self.invoices = [inv for inv in self.invoices if int(inv.get("invoice_number", -1)) != int(num)]
        save_all_invoices(self.invoices)

        # clear editor
        self.current = None
        self.var_number.set("")
        self.var_created.set("")
        self.var_customer.set("")
        self.var_tax.set(str(DEFAULT_TAX_RATE))
        self.var_due.set("")
        self.var_status.set("UNPAID")
        self.notes.configure(state="normal")
        self.notes.delete("1.0", tk.END)
        self.notes.configure(state="disabled")
        self._refresh_items_table()
        self._refresh_totals()
        self._refresh_invoice_list()
        messagebox.showinfo("Deleted", f"Invoice #{num} deleted.")

    def add_item_dialog(self):
        if not self.current:
            messagebox.showinfo("Add Item", "Create or load an invoice first.")
            return

        win = tk.Toplevel(self)
        win.title("Add Item")
        win.geometry("460x220")
        win.transient(self)
        win.grab_set()

        desc = tk.StringVar()
        qty = tk.StringVar(value="1")
        unit = tk.StringVar(value="0.00")

        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Description").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=desc, width=48).grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 10))

        ttk.Label(frm, text="Qty").grid(row=2, column=0, sticky="w")
        ttk.Entry(frm, textvariable=qty, width=10).grid(row=3, column=0, sticky="w", pady=(0, 10))

        ttk.Label(frm, text="Unit Price").grid(row=2, column=1, sticky="w")
        ttk.Entry(frm, textvariable=unit, width=14).grid(row=3, column=1, sticky="w", pady=(0, 10))

        def do_add():
            d = desc.get().strip()
            if not d:
                messagebox.showerror("Error", "Description can't be empty.")
                return
            try:
                q = int(qty.get().strip())
                if q <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Qty must be a whole number > 0.")
                return
            try:
                u = float(unit.get().strip().replace("$", "").replace(",", ""))
                if u < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Unit price must be a number >= 0.")
                return

            self.current["items"].append({"description": d, "qty": q, "unit_price": u})
            self._refresh_items_table()
            self._refresh_totals()
            win.destroy()

        btns = ttk.Frame(frm)
        btns.grid(row=4, column=0, columnspan=2, sticky="e")
        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="right")
        ttk.Button(btns, text="Add", command=do_add).pack(side="right", padx=6)

    def remove_selected_item(self):
        if not self.current:
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Remove Item", "Select an item in the table first.")
            return
        # remove by index in table order
        idx = self.tree.index(sel[0])
        try:
            del self.current["items"][idx]
        except Exception:
            return
        self._refresh_items_table()
        self._refresh_totals()

    def export_txt(self):
        if not self.current:
            messagebox.showinfo("Export", "Create or load an invoice first.")
            return
        # make sure latest UI edits are included
        self.save_current()

        out_dir = filedialog.askdirectory(title="Choose export folder")
        if not out_dir:
            return
        path = export_invoice_txt(self.current, out_dir)
        messagebox.showinfo("Exported", f"Exported:\n{path}")

    def edit_business_dialog(self):
        win = tk.Toplevel(self)
        win.title("Business Info")
        win.geometry("520x260")
        win.transient(self)
        win.grab_set()

        info = load_business_info() or {"name": "", "address": "", "phone": "", "email": ""}

        name = tk.StringVar(value=info.get("name", ""))
        address = tk.StringVar(value=info.get("address", ""))
        phone = tk.StringVar(value=info.get("phone", ""))
        email = tk.StringVar(value=info.get("email", ""))

        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)

        def row(label, var, r):
            ttk.Label(frm, text=label).grid(row=r, column=0, sticky="w")
            ttk.Entry(frm, textvariable=var, width=56).grid(row=r+1, column=0, sticky="we", pady=(0, 10))

        row("Business name", name, 0)
        row("Address", address, 2)
        row("Phone", phone, 4)
        row("Email", email, 6)

        def save():
            n = name.get().strip() or "My Business"
            new_info = {"name": n, "address": address.get().strip(), "phone": phone.get().strip(), "email": email.get().strip()}
            save_business_info(new_info)
            self.business = new_info
            messagebox.showinfo("Saved", "Business info saved.")
            win.destroy()

        btns = ttk.Frame(frm)
        btns.grid(row=8, column=0, sticky="e")
        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="right")
        ttk.Button(btns, text="Save", command=save).pack(side="right", padx=6)


if __name__ == "__main__":
    root = tk.Tk()
    app = InvoiceGUI(root)
    app.pack(fill="both", expand=True)
    root.mainloop()
