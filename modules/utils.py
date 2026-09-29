"""Helper utilities: logging setup, input validation and text formatting.

Kept free of business logic so every other module can import from here.
"""

import logging
import os
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")


class ValidationError(ValueError):
    """Raised when user input fails validation."""


def setup_logger(name="expense_tracker"):
    """Create (once) a logger that writes to logs/app.log."""
    logger = logging.getLogger(name)
    if logger.handlers:  # already configured
        return logger
    logger.setLevel(logging.INFO)
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    except OSError:
        handler = logging.NullHandler()  # never crash because logging failed
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
    return logger


def parse_amount(text):
    """Convert text to a positive float rounded to 2 decimals."""
    try:
        value = float(str(text).strip())
    except ValueError:
        raise ValidationError("Amount must be a number, e.g. 250 or 99.50")
    if value <= 0:
        raise ValidationError("Amount must be greater than zero")
    if value > 10_000_000:
        raise ValidationError("Amount is unrealistically large")
    return round(value, 2)


def parse_date(text):
    """Convert 'YYYY-MM-DD' text to a date string; empty text means today."""
    text = str(text).strip()
    if not text:
        return datetime.now().strftime(DATE_FORMAT)
    try:
        return datetime.strptime(text, DATE_FORMAT).strftime(DATE_FORMAT)
    except ValueError:
        raise ValidationError("Date must be in YYYY-MM-DD format")


def parse_month(text):
    """Validate a 'YYYY-MM' month string; empty text means the current month."""
    text = str(text).strip()
    if not text:
        return datetime.now().strftime("%Y-%m")
    try:
        return datetime.strptime(text, "%Y-%m").strftime("%Y-%m")
    except ValueError:
        raise ValidationError("Month must be in YYYY-MM format")


def clean_text(text, field="Text", max_len=40, allow_empty=False):
    """Strip and validate free text such as category or description."""
    text = " ".join(str(text).split())
    if not text and not allow_empty:
        raise ValidationError(f"{field} cannot be empty")
    if len(text) > max_len:
        raise ValidationError(f"{field} must be at most {max_len} characters")
    return text


def format_money(value):
    """Format a number as money with thousands separators."""
    return f"{value:,.2f}"


def bar(fraction, width=20):
    """Return a text progress bar for a value between 0 and 1 (capped at 1)."""
    filled = int(round(min(max(fraction, 0), 1) * width))
    return "#" * filled + "." * (width - filled)
