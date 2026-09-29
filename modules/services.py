"""Business logic for the three functional modules.

1. Expense management (add / view / edit / delete / search)
2. Budgets and alerts
3. Reports and analytics
"""

from itertools import groupby

import numpy as np

from modules import storage
from modules.models import Expense, RecurringExpense, Budget
from modules.utils import (
    ValidationError, clean_text, parse_month, setup_logger,
)

log = setup_logger()


class NotFoundError(LookupError):
    """Raised when an expense id does not exist."""


class ExpenseService:
    """Coordinates models and storage; the menu in main.py only calls this class."""

    def __init__(self, data_path=storage.DATA_FILE):
        self._path = data_path
        self._expenses, self._budgets, self._next_id = storage.load_data(data_path)

    def _save(self):
        storage.save_data(self._expenses, self._budgets, self._next_id, self._path)

    # ------------------------------------------------------------------
    # Module 1: expense management
    # ------------------------------------------------------------------
    def add_expense(self, amount, category, description="", date="",
                    recurring=False, frequency="monthly"):
        """Validate and store a new expense; returns the created object."""
        if recurring:
            expense = RecurringExpense(self._next_id, amount, category,
                                       description, date, frequency)
        else:
            expense = Expense(self._next_id, amount, category, description, date)
        self._expenses.append(expense)
        self._next_id += 1
        self._save()
        log.info("Added expense %s", expense.id)
        return expense

    def list_expenses(self, month=None):
        """All expenses sorted by date (optionally only one 'YYYY-MM' month)."""
        items = sorted(self._expenses)
        if month:
            items = [e for e in items if e.month == month]
        return items

    def get_expense(self, expense_id):
        for expense in self._expenses:
            if expense.id == expense_id:
                return expense
        raise NotFoundError(f"No expense with id {expense_id}")

    def update_expense(self, expense_id, **changes):
        """Update any of: amount, category, description, date."""
        expense = self.get_expense(expense_id)
        allowed = {"amount", "category", "description", "date"}
        for field, value in changes.items():
            if field not in allowed:
                raise ValidationError(f"Cannot edit field '{field}'")
            if value is None or str(value).strip() == "":
                continue  # blank means "keep current value"
            setattr(expense, field, value)
        self._save()
        log.info("Updated expense %s", expense_id)
        return expense

    def delete_expense(self, expense_id):
        expense = self.get_expense(expense_id)
        self._expenses.remove(expense)
        self._save()
        log.info("Deleted expense %s", expense_id)
        return expense

    def search(self, keyword="", category="", min_amount=None, max_amount=None):
        """Filter by text in description/category, exact category and amount range."""
        keyword = keyword.strip().lower()
        category = category.strip().title()
        results = []
        for e in sorted(self._expenses):
            if keyword and keyword not in (e.description + " " + e.category).lower():
                continue
            if category and e.category != category:
                continue
            if min_amount is not None and e.amount < min_amount:
                continue
            if max_amount is not None and e.amount > max_amount:
                continue
            results.append(e)
        return results
