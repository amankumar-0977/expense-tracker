"""Persistent storage: JSON load/save with safe writes, backup and CSV export."""

import csv
import json
import os
import shutil

from modules.models import Expense, Budget
from modules.utils import setup_logger

log = setup_logger()

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "expenses.json")
EXPORT_DIR = "exports"


class StorageError(Exception):
    """Raised when data cannot be read or written."""


def load_data(path=DATA_FILE):
    """Return (expenses, budgets, next_id). A missing file gives empty data."""
    if not os.path.exists(path):
        log.info("No data file found at %s, starting empty", path)
        return [], {}, 1
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        expenses = [Expense.from_dict(item) for item in raw.get("expenses", [])]
        budgets = {b["category"]: Budget(b["category"], b["limit"])
                   for b in raw.get("budgets", [])}
        next_id = raw.get("next_id", max((e.id for e in expenses), default=0) + 1)
        log.info("Loaded %d expenses and %d budgets", len(expenses), len(budgets))
        return expenses, budgets, next_id
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        # keep the damaged file for inspection and start clean instead of crashing
        broken = path + ".corrupt"
        shutil.copyfile(path, broken)
        log.error("Data file unreadable (%s); copy saved to %s", error, broken)
        raise StorageError(
            f"Data file is damaged ({error}). A copy was kept at {broken}.")
    except OSError as error:
        log.error("Cannot read %s: %s", path, error)
        raise StorageError(f"Cannot read data file: {error}")


def save_data(expenses, budgets, next_id, path=DATA_FILE):
    """Write everything to disk safely (temp file, backup, then replace)."""
    payload = {
        "next_id": next_id,
        "expenses": [e.to_dict() for e in expenses],
        "budgets": [b.to_dict() for b in budgets.values()],
    }
    folder = os.path.dirname(path)
    temp_path = path + ".tmp"
    try:
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        if os.path.exists(path):
            shutil.copyfile(path, path + ".bak")  # one-step backup
        os.replace(temp_path, path)  # atomic: never leaves half-written data
        log.info("Saved %d expenses", len(expenses))
    except OSError as error:
        log.error("Cannot write %s: %s", path, error)
        raise StorageError(f"Cannot save data: {error}")


def export_csv(expenses, filename="expenses.csv", folder=EXPORT_DIR):
    """Export expenses to a CSV file and return its path."""
    try:
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["id", "date", "category", "amount", "description", "type"])
            for e in sorted(expenses):
                writer.writerow([e.id, e.date, e.category, e.amount, e.description, e.kind])
        log.info("Exported %d rows to %s", len(expenses), path)
        return path
    except OSError as error:
        log.error("CSV export failed: %s", error)
        raise StorageError(f"Cannot export CSV: {error}")
