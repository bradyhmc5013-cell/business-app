import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

DATA_FILE = "invoices.json"
BUSINESS_FILE = "business_info.json"
DEFAULT_TAX_RATE = 0.08  # 8%


# ----------------------------
# Business Info (saved once)
# ----------------------------
def load_business_info() -> dict:
    if not os.path.exists(BUSINESS_FILE):
        return {}
    try:
        with open(BUSINESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_business_info(info: dict) -> None:
    with open(BUSINESS_FILE, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)


def setup_business_info() -> dict:
    print("\n--- Business Setup (saved for future invoices) ---")
    info = {
        "name": input("Business name: ").strip(),
        "address": input("Address (optional): ").strip(),
        "phone": input("Phone (optional): ").strip(),
        "email": input("Email (optional): ").strip(),
    }
    if not info["name"]:
        info["name"] = "My Business"
    save_business_info(info)
    print("Business info saved.\n")
    return info


def edit_business_info() -> dict:
    current = load_business_info()
    if not current:
        current = {"name": "My Business", "address": "", "phone": "", "email": ""}

    print("\n--- Edit Business Info ---")
    print("Press Enter to keep the current value.\n")

    name = input(f"Business name [{current.get('name','')}]: ").strip()
    address = input(f"Address [{current.get('address','')}]: ").strip()
    phone = input(f"Phone [{current.get('phone','')}]: ").strip()
    email = input(f"Email [{current.get('email','')}]: ").strip()

    if name:
        current["name"] = name
    if address:
        current["address"] = address
    if phone:
        current["phone"] = phone
    if email:
        current["email"] = email

    save_business_info(current)
    print("Business info updated.\n")
    return current


# ----------------------------
# Invoice Storage
# ----------------------------
def load_all_invoices() -> list[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            invoices = json.load(f)
    except json.JSONDecodeError:
        return []

    # Migrate older invoices that stored business as "business_name"
    for inv in invoices:
        if "business" not in inv:
            inv["business"] = {
                "name": inv.get("business_name", "My Business"),
                "address": "",
                "phone": "",
                "email": "",
            }
        inv.pop("business_name", None)

    return invoices


def save_all_invoices(invoices: list[dict]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(invoices, f, indent=2)


def next_invoice_number(invoices: list[dict]) -> int:
    if not invoices:
        return 1001
    return max(inv["invoice_number"] for inv in invoices) + 1


# ----------------------------
# Helpers
# ----------------------------
def money(value: float) -> str:
    return f"${value:.2f}"


def calculate_totals(items: list[dict], tax_rate: float) -> tuple[float, float, float]:
    subtotal = sum(item["qty"] * item["unit_price"] for item in items)
    tax = subtotal * tax_rate
    total = subtotal + tax
    return subtotal, tax, total

def safe_filename(text: str) -> str:
    """
    Make a string safe for Windows filenames.
    Keeps letters/numbers/_- and replaces spaces with underscores.
    """
    text = (text or "").strip().replace(" ", "_")
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    return "".join(ch for ch in text if ch in allowed) or "Invoice"


def prompt_float(prompt: str) -> float:
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
            if value < 0:
                print("Enter a non-negative number.")
                continue
            return value
        except ValueError:
            print("Enter a valid number (example: 12.50).")


def prompt_int(prompt: str) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
            if value <= 0:
                print("Enter a number greater than 0.")
                continue
            return value
        except ValueError:
            print("Enter a whole number (example: 3).")

def is_overdue(invoice: dict) -> bool:
    if invoice.get("status", "UNPAID") == "PAID":
        return False

    due = invoice.get("due_date", "")
    if not due:
        return False

    try:
        due_date = datetime.strptime(due, "%Y-%m-%d").date()
    except ValueError:
        return False

    today = datetime.now().date()
    return today > due_date


def prompt_date(prompt: str) -> str:
    """
    Returns a date string in YYYY-MM-DD format.
    Empty input returns "" (meaning no due date).
    """
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return ""
        try:
            datetime.strptime(raw, "%Y-%m-%d")
            return raw
        except ValueError:
            print("Enter date as YYYY-MM-DD (example: 2026-02-15) or press Enter to skip.")


def find_invoice_by_number(invoices: list[dict], inv_num: int) -> dict | None:
    for inv in invoices:
        if inv["invoice_number"] == inv_num:
            return inv
    return None


# ----------------------------
# Core Actions
# ----------------------------
def create_invoice(invoices: list[dict]) -> dict:
    inv_num = next_invoice_number(invoices)

    business_info = load_business_info()
    if not business_info:
        choice = input("No saved business info found. Set it up now? (Y/n): ").strip().lower()
        if choice != "n":
            business_info = setup_business_info()
        else:
            business_info = {
                "name": "My Business",
                "address": "",
                "phone": "",
                "email": "",
            }

    customer_name = input("Customer name: ").strip() or "Customer"

    use_default = input(f"Use default tax rate {DEFAULT_TAX_RATE}? (Y/n): ").strip().lower()
    if use_default == "n":
        tax_rate = prompt_float("Tax rate as decimal (example 0.0825): ")
    else:
        tax_rate = DEFAULT_TAX_RATE

    invoice = {
        "invoice_number": inv_num,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "business": business_info,
        "customer_name": customer_name,
        "tax_rate": tax_rate,
        "items": [],
        "notes": "",
        "due_date": "",
        "status": "UNPAID",
    }

    return invoice


def add_item(invoice: dict) -> None:
    desc = input("Item description: ").strip()
    if not desc:
        print("Description can't be empty.")
        return
    qty = prompt_int("Quantity: ")
    unit_price = prompt_float("Unit price: ")
    invoice["items"].append({"description": desc, "qty": qty, "unit_price": unit_price})
    print("Item added.")


def show_invoice(invoice: dict) -> None:
    biz = invoice.get("business", {})

    print("\n" + "=" * 60)
    print(f"INVOICE #{invoice['invoice_number']}")
    print(f"Business: {biz.get('name', '')}")
    if biz.get("address"):
        print(f"Address:  {biz.get('address')}")
    if biz.get("phone"):
        print(f"Phone:    {biz.get('phone')}")
    if biz.get("email"):
        print(f"Email:    {biz.get('email')}")
    print(f"Customer: {invoice['customer_name']}")
    print(f"Date:     {invoice['created_at']}")
    print("-" * 60)

    if not invoice["items"]:
        print("(No items yet)")
    else:
        for i, item in enumerate(invoice["items"], start=1):
            line_total = item["qty"] * item["unit_price"]
            print(
                f"{i:>2}. {item['description']:<25} x{item['qty']:<3} "
                f"{money(item['unit_price']):>8}  = {money(line_total):>8}"
            )

    subtotal, tax, total = calculate_totals(invoice["items"], invoice["tax_rate"])
    print("-" * 60)
    print(f"{'Subtotal:':>45} {money(subtotal):>10}")
    print(f"{'Tax:':>45} {money(tax):>10}  (rate {invoice['tax_rate']})")
    print(f"{'Total:':>45} {money(total):>10}")

    if invoice.get("notes"):
        print("\nNotes:")
        print(invoice["notes"])

    print(f"Status: {invoice.get('status','UNPAID')}")
    due = invoice.get("due_date", "")
    if due:
        print(f"Due Date: {due}")

    print("=" * 60 + "\n")



def export_invoice_txt(invoice: dict) -> str:
    biz = invoice.get("business", {})
    biz_name = safe_filename(biz.get("name", "My Business"))
    filename = f"{biz_name}_Invoice_{invoice['invoice_number']}.txt"

    subtotal, tax, total = calculate_totals(invoice["items"], invoice["tax_rate"])
    biz = invoice.get("business", {})

    page_width = 72
    line = "-" * page_width

    def center(text: str) -> str:
        return str(text).center(page_width)

    def money2(value: float) -> str:
        return f"${value:,.2f}"

    desc_w, qty_w, unit_w, line_w = 40, 6, 10, 12

    def fit(text: str, width: int) -> str:
        text = str(text)
        return text if len(text) <= width else text[: width - 3] + "..."

    out = []
    out.append(center(biz.get("name", "My Business")))
    if biz.get("address"):
        out.append(center(biz.get("address")))

    contact = " | ".join([x for x in [biz.get("phone", ""), biz.get("email", "")] if x])
    if contact:
        out.append(center(contact))

    out.append(line)

    left = f"Bill To: {invoice.get('customer_name','')}"
    right = f"Invoice #: {invoice['invoice_number']}   Date: {invoice.get('created_at','')}"
    if len(left) + len(right) + 1 <= page_width:
        out.append(left + (" " * (page_width - len(left) - len(right))) + right)
    else:
        out.append(left)
        out.append(right)

    # Status / Due Date (invoice-standard placement)
    out.append(f"Status: {invoice.get('status', 'UNPAID')}")
    due = invoice.get("due_date", "")
    if due:
        out.append(f"Due Date: {due}")

    out.append(line)

    out.append(
        f"{'DESCRIPTION'.ljust(desc_w)} "
        f"{'QTY'.rjust(qty_w)} "
        f"{'UNIT'.rjust(unit_w)} "
        f"{'LINE'.rjust(line_w)}"
    )
    out.append(line)

    if not invoice["items"]:
        out.append("(No items)")
    else:
        for item in invoice["items"]:
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
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    return filename

def export_invoice_pdf(invoice: dict) -> str:
    biz = invoice.get("business", {})
    biz_name = safe_filename(biz.get("name", "My Business"))
    filename = f"{biz_name}_Invoice_{invoice['invoice_number']}.pdf"

    subtotal, tax, total = calculate_totals(invoice["items"], invoice["tax_rate"])
    biz = invoice.get("business", {})

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    left_margin = 50
    y = height - 60
    line_h = 14

    def draw(text: str, x=left_margin, size=11, bold=False):
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        c.drawString(x, y, str(text))
        y -= line_h

    # Header
    draw(biz.get("name", "My Business"), size=16, bold=True)
    if biz.get("address"):
        draw(biz.get("address"))
    contact_bits = [b for b in [biz.get("phone", ""), biz.get("email", "")] if b]
    if contact_bits:
        draw(" | ".join(contact_bits))

    y -= 8
    c.line(left_margin, y, width - left_margin, y)
    y -= 18

    # Invoice meta
    draw(f"Bill To: {invoice.get('customer_name','')}", bold=True)
    draw(f"Invoice #: {invoice['invoice_number']}")
    draw(f"Date: {invoice.get('created_at','')}")
    status_text = "OVERDUE" if is_overdue(invoice) else invoice.get("status", "UNPAID")
    draw(f"Status: {status_text}")
    due = invoice.get("due_date", "")
    if due:
        draw(f"Due Date: {due}")

    y -= 8
    c.line(left_margin, y, width - left_margin, y)
    y -= 18

    # Table header
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left_margin, y, "Description")
    c.drawRightString(width - 240, y, "Qty")
    c.drawRightString(width - 160, y, "Unit")
    c.drawRightString(width - left_margin, y, "Line")
    y -= 10
    c.line(left_margin, y, width - left_margin, y)
    y -= 16

    # Items
    c.setFont("Helvetica", 11)
    for item in invoice.get("items", []):
        desc = str(item.get("description", ""))
        qty = int(item.get("qty", 0))
        unit = float(item.get("unit_price", 0.0))
        lt = qty * unit

        # wrap description if long (simple wrap)
        max_len = 55
        desc_lines = [desc[i:i+max_len] for i in range(0, len(desc), max_len)] or [""]

        for idx, dl in enumerate(desc_lines):
            if y < 80:
                c.showPage()
                y = height - 60
                c.setFont("Helvetica", 11)
            c.drawString(left_margin, y, dl)
            if idx == 0:
                c.drawRightString(width - 240, y, str(qty))
                c.drawRightString(width - 160, y, f"${unit:,.2f}")
                c.drawRightString(width - left_margin, y, f"${lt:,.2f}")
            y -= 14

    if not invoice.get("items"):
        c.drawString(left_margin, y, "(No items)")
        y -= 14

    y -= 6
    c.line(left_margin, y, width - left_margin, y)
    y -= 20

    # Totals
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 160, y, "Subtotal:")
    c.drawRightString(width - left_margin, y, f"${subtotal:,.2f}")
    y -= 14

    c.setFont("Helvetica", 11)
    c.drawRightString(width - 160, y, "Tax:")
    c.drawRightString(width - left_margin, y, f"${tax:,.2f}")
    y -= 14

    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - 160, y, "TOTAL:")
    c.drawRightString(width - left_margin, y, f"${total:,.2f}")
    y -= 22

    # Notes
    notes = invoice.get("notes", "").strip()
    if notes:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left_margin, y, "Notes:")
        y -= 14
        c.setFont("Helvetica", 11)
        for line in notes.splitlines():
            if y < 80:
                c.showPage()
                y = height - 60
                c.setFont("Helvetica", 11)
            c.drawString(left_margin, y, line[:90])
            y -= 14

    y -= 10
    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(width / 2, y, "Thank you for your business!")

    c.save()
    return filename


def invoice_menu(current: dict, invoices: list[dict]) -> None:
    while True:
        print("Invoice Menu")
        print("1) Add item")
        print("2) Add/edit notes")
        print("3) Show invoice")
        print("4) Export invoice to .txt")
        print("4b) Export invoice to .pdf")
        print("5) Set due date")
        print("6) Toggle PAID/UNPAID")
        print("7) Save & exit to main menu")

        choice = input("> ").strip().lower()

        if choice == "1":
            add_item(current)

        elif choice == "2":
            current["notes"] = input("Notes (leave blank to clear): ")

        elif choice == "3":
            show_invoice(current)

        elif choice == "4":
            filename = export_invoice_txt(current)
            print(f"Exported: {filename}")

        elif choice == "4b":
            filename = export_invoice_pdf(current)
            print(f"Exported: {filename}")

        elif choice == "5":
            current["due_date"] = prompt_date("Due date (YYYY-MM-DD) or Enter to clear: ")
            print("Due date updated.")

        elif choice == "6":
            current["status"] = "PAID" if current.get("status", "UNPAID") != "PAID" else "UNPAID"
            print(f"Status set to {current['status']}.")

        elif choice == "7":
            existing = find_invoice_by_number(invoices, current["invoice_number"])
            if existing is None:
                invoices.append(current)
            else:
                idx = invoices.index(existing)
                invoices[idx] = current
            save_all_invoices(invoices)
            print("Saved.")
            return

        else:
            print("Choose 1–7.")




def main():
    invoices = load_all_invoices()

    while True:
        print("\nMain Menu")
        print("1) Create new invoice")
        print("2) Load existing invoice")
        print("3) List invoices")
        print("4) Edit business info")
        print("5) Quit")
        choice = input("> ").strip()

        if choice == "1":
            current = create_invoice(invoices)
            invoice_menu(current, invoices)

        elif choice == "2":
            inv_num = prompt_int("Enter invoice number: ")
            existing = find_invoice_by_number(invoices, inv_num)
            if existing is None:
                print("Invoice not found.")
            else:
                invoice_menu(existing, invoices)
        elif choice == "3":
            if not invoices:
                print("No invoices saved yet.")
            else:
                for inv in sorted(invoices, key=lambda x: x["invoice_number"]):
                    subtotal, tax, total = calculate_totals(inv["items"], inv["tax_rate"])

                    status = inv.get("status", "UNPAID")
                    due = inv.get("due_date", "")
                    due_part = f" | Due {due}" if due else ""
                    flag = " | OVERDUE" if is_overdue(inv) else ""

                    print(
                        f"#{inv['invoice_number']} | {inv['customer_name']} | {inv['created_at']} | "
                        f"{status}{due_part}{flag} | Total {money(total)}"
                    )

        
        elif choice == "4":
            edit_business_info()

        elif choice == "5":
            print("Goodbye.")
            break

        else:
            print("Choose 1–5.")


if __name__ == "__main__":
    main()
