import json
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "expenses.json")


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
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def next_id(expenses: list[dict]) -> int:
    if not expenses:
        return 1
    return max(e.get("id", 0) for e in expenses) + 1
