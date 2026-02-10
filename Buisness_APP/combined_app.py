import os
import sys
import tkinter as tk
from tkinter import ttk

# Ensure package imports work when running from repo root
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def run_embedded():
    # instantiate both apps as Frames inside Notebook tabs
    from expenses_tracker.expense_gui import App as ExpensesApp
    from invoice_generator.invoice_GUI.invoice_gui import InvoiceGUI

    root = tk.Tk()
    root.title("Business Suite")
    root.geometry("1200x720")

    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=6, pady=6)

    # Expenses tab
    exp_frame = ttk.Frame(nb)
    nb.add(exp_frame, text="Expenses")
    expenses_app = ExpensesApp(exp_frame)
    expenses_app.pack(fill="both", expand=True)

    # Invoices tab
    inv_frame = ttk.Frame(nb)
    nb.add(inv_frame, text="Invoices")
    invoices_app = InvoiceGUI(inv_frame)
    invoices_app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    run_embedded()
