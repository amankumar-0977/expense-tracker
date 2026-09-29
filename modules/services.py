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

    # ------------------------------------------------------------------
    # Module 2: budgets and alerts
    # ------------------------------------------------------------------
    def set_budget(self, category, limit):
        """Create or replace the monthly budget for a category."""
        budget = Budget(category, limit)
        self._budgets[budget.category] = budget
        self._save()
        log.info("Budget set: %s = %s", budget.category, budget.limit)
        return budget

    def remove_budget(self, category):
        key = clean_text(category, "Category", 25).title()
        if key not in self._budgets:
            raise NotFoundError(f"No budget set for '{key}'")
        del self._budgets[key]
        self._save()
        log.info("Budget removed: %s", key)

    def spent_by_category(self, month):
        """Return {category: total spent} for a month."""
        totals = {}
        for e in self.list_expenses(month):
            totals[e.category] = totals.get(e.category, 0.0) + e.amount
        return {cat: round(total, 2) for cat, total in totals.items()}

    def budget_report(self, month=""):
        """List of (Budget, spent, fraction_used, status) for the given month."""
        month = parse_month(month)
        spent = self.spent_by_category(month)
        rows = []
        for category in sorted(self._budgets):
            budget = self._budgets[category]
            used = spent.get(category, 0.0)
            rows.append((budget, used, Budget.usage(used, budget.limit),
                         budget.status(used)))
        return rows

    def check_alert(self, expense):
        """Return a warning message if this expense pushes its category to a limit."""
        budget = self._budgets.get(expense.category)
        if budget is None:
            return None
        spent = self.spent_by_category(expense.month).get(expense.category, 0.0)
        status = budget.status(spent)
        if status == "OK":
            return None
        message = (f"{status}: {expense.category} spending is {spent:,.2f} "
                   f"of {budget.limit:,.2f} for {expense.month}")
        log.warning(message)
        return message

    # ------------------------------------------------------------------
    # Module 3: reports and analytics
    # ------------------------------------------------------------------
    def monthly_summary(self, month=""):
        """Statistics for one month, or None when there is no data.

        Uses NumPy for the numeric statistics and itertools.groupby to
        group expenses by category.
        """
        month = parse_month(month)
        items = self.list_expenses(month)
        if not items:
            return None

        amounts = np.array([e.amount for e in items], dtype=float)
        total = float(amounts.sum())

        by_category = sorted(items, key=lambda e: e.category)
        breakdown = []
        for category, group in groupby(by_category, key=lambda e: e.category):
            group_total = round(sum(e.amount for e in group), 2)
            breakdown.append((category, group_total, group_total / total * 100))
        breakdown.sort(key=lambda row: row[1], reverse=True)

        return {
            "month": month,
            "count": len(items),
            "total": round(total, 2),
            "mean": round(float(amounts.mean()), 2),
            "median": round(float(np.median(amounts)), 2),
            "max": round(float(amounts.max()), 2),
            "min": round(float(amounts.min()), 2),
            "std": round(float(amounts.std()), 2),
            "largest": max(items, key=lambda e: e.amount),
            "breakdown": breakdown,
        }

    def monthly_trend(self):
        """Return [(month, total)] across all data, oldest first."""
        items = sorted(self._expenses, key=lambda e: e.month)
        return [(month, round(sum(e.amount for e in group), 2))
                for month, group in groupby(items, key=lambda e: e.month)]

    def top_categories(self, month="", n=3):
        """The n categories with the highest spending in a month."""
        spent = self.spent_by_category(parse_month(month))
        return sorted(spent.items(), key=lambda pair: pair[1], reverse=True)[:n]

    def export_csv(self, filename="expenses.csv"):
        """Export every expense to CSV and return the file path."""
        clean = clean_text(filename, "File name", 40)
        if not clean.lower().endswith(".csv"):
            clean += ".csv"
        return storage.export_csv(self._expenses, clean)
