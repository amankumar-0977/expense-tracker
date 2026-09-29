"""Data models: Expense, RecurringExpense and Budget.

Demonstrates classes, encapsulation (properties), inheritance, method
overriding, operator overloading and class/static methods.
"""

from modules.utils import (
    clean_text, parse_amount, parse_date, format_money, ValidationError,
)


class Expense:
    """A single expense record."""

    kind = "one-time"

    def __init__(self, expense_id, amount, category, description="", date=""):
        self._id = expense_id
        self._amount = parse_amount(amount)
        self._category = clean_text(category, "Category", 25).title()
        self._description = clean_text(description, "Description", 60, allow_empty=True)
        self._date = parse_date(date)

    # ---- encapsulated attributes (read via properties, change via setters) ----
    @property
    def id(self):
        return self._id

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        self._amount = parse_amount(value)

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        self._category = clean_text(value, "Category", 25).title()

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = clean_text(value, "Description", 60, allow_empty=True)

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value):
        self._date = parse_date(value)

    @property
    def month(self):
        """Month key such as '2026-09', used for grouping."""
        return self._date[:7]

    # ---- conversion ----
    def to_dict(self):
        return {
            "id": self._id, "type": self.kind, "amount": self._amount,
            "category": self._category, "description": self._description,
            "date": self._date,
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild the right class from a stored dictionary."""
        try:
            if data.get("type") == RecurringExpense.kind:
                return RecurringExpense(
                    data["id"], data["amount"], data["category"],
                    data.get("description", ""), data["date"],
                    data.get("frequency", "monthly"),
                )
            return cls(data["id"], data["amount"], data["category"],
                       data.get("description", ""), data["date"])
        except KeyError as missing:
            raise ValidationError(f"Stored record is missing field {missing}")

    # ---- operator overloading / display ----
    def __lt__(self, other):
        """Sort by date, then id (so sorted(expenses) works)."""
        return (self._date, self._id) < (other._date, other._id)

    def __str__(self):
        return (f"#{self._id:<4} {self._date}  {self._category:<14} "
                f"{format_money(self._amount):>10}  {self._description}")

    def __repr__(self):
        return f"{type(self).__name__}(id={self._id}, amount={self._amount}, category={self._category!r})"


class RecurringExpense(Expense):
    """An expense that repeats (rent, subscriptions). Inherits from Expense."""

    kind = "recurring"
    FREQUENCIES = ("weekly", "monthly", "yearly")

    def __init__(self, expense_id, amount, category, description="", date="",
                 frequency="monthly"):
        super().__init__(expense_id, amount, category, description, date)
        frequency = str(frequency).strip().lower()
        if frequency not in self.FREQUENCIES:
            raise ValidationError("Frequency must be weekly, monthly or yearly")
        self._frequency = frequency

    @property
    def frequency(self):
        return self._frequency

    def to_dict(self):  # method overriding: add the extra field
        data = super().to_dict()
        data["frequency"] = self._frequency
        return data

    def __str__(self):  # method overriding: mark recurring entries
        return super().__str__() + f"  [{self._frequency}]"


class Budget:
    """Monthly spending limit for one category."""

    WARN_AT = 0.8  # warn when 80% of the limit is used

    def __init__(self, category, limit):
        self.category = clean_text(category, "Category", 25).title()
        self.limit = parse_amount(limit)

    def status(self, spent):
        """Return 'OK', 'WARNING' or 'EXCEEDED' for the amount spent so far."""
        if spent > self.limit:
            return "EXCEEDED"
        if spent >= self.limit * self.WARN_AT:
            return "WARNING"
        return "OK"

    @staticmethod
    def usage(spent, limit):
        """Fraction of the limit that has been used."""
        return spent / limit if limit else 0.0

    def to_dict(self):
        return {"category": self.category, "limit": self.limit}
