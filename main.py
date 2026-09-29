"""Expense Tracker & Analyzer - command line entry point.

Run:  python main.py            (uses data/expenses.json)
      python main.py --data my.json   (use a different data file)
"""

import argparse

from modules import storage
from modules.services import ExpenseService, NotFoundError
from modules.utils import (
    ValidationError, bar, format_money, parse_amount, parse_month, setup_logger,
)

log = setup_logger()

MENU = """
========== EXPENSE TRACKER ==========
 1. Add expense
 2. View expenses
 3. Edit expense
 4. Delete expense
 5. Search expenses
 6. Set category budget
 7. Budget status
 8. Monthly report
 9. Spending trend
10. Export to CSV
 0. Exit
====================================="""

HEADER = f"{'ID':<5} {'Date':<11} {'Category':<14} {'Amount':>10}  Description"


def ask(prompt):
    return input(prompt).strip()


def ask_int(prompt):
    text = ask(prompt)
    try:
        return int(text)
    except ValueError:
        raise ValidationError("Please enter a whole number")


def print_expenses(items):
    if not items:
        print("No expenses found.")
        return
    print(HEADER)
    print("-" * 70)
    for expense in items:
        print(expense)
    print("-" * 70)
    print(f"{len(items)} record(s), total {format_money(sum(e.amount for e in items))}")


# ---------------- menu actions ----------------
def add_expense(service):
    amount = ask("Amount: ")
    category = ask("Category (e.g. Food, Travel): ")
    description = ask("Description (optional): ")
    date = ask("Date YYYY-MM-DD (blank = today): ")
    recurring = ask("Recurring? (y/N): ").lower() == "y"
    frequency = ask("Frequency weekly/monthly/yearly: ") if recurring else "monthly"
    expense = service.add_expense(amount, category, description, date, recurring, frequency)
    print(f"Saved -> {expense}")
    alert = service.check_alert(expense)
    if alert:
        print(f"*** {alert} ***")


def view_expenses(service):
    month = ask("Month YYYY-MM (blank = all): ")
    month = parse_month(month) if month else None
    print_expenses(service.list_expenses(month))


def edit_expense(service):
    expense_id = ask_int("Expense id to edit: ")
    current = service.get_expense(expense_id)
    print(f"Current: {current}\n(leave a field blank to keep it)")
    updated = service.update_expense(
        expense_id,
        amount=ask("New amount: "),
        category=ask("New category: "),
        description=ask("New description: "),
        date=ask("New date: "),
    )
    print(f"Updated -> {updated}")


def delete_expense(service):
    expense_id = ask_int("Expense id to delete: ")
    print(f"About to delete: {service.get_expense(expense_id)}")
    if ask("Confirm (y/N): ").lower() == "y":
        service.delete_expense(expense_id)
        print("Deleted.")
    else:
        print("Cancelled.")


def search_expenses(service):
    keyword = ask("Keyword (blank = any): ")
    category = ask("Category (blank = any): ")
    low, high = ask("Min amount (blank = none): "), ask("Max amount (blank = none): ")
    results = service.search(keyword, category,
                             parse_amount(low) if low else None,
                             parse_amount(high) if high else None)
    print_expenses(results)


def set_budget(service):
    budget = service.set_budget(ask("Category: "), ask("Monthly limit: "))
    print(f"Budget set: {budget.category} = {format_money(budget.limit)} per month")


def budget_status(service):
    month = parse_month(ask("Month YYYY-MM (blank = current): "))
    rows = service.budget_report(month)
    if not rows:
        print("No budgets set yet. Use option 6.")
        return
    print(f"\nBudget status for {month}")
    for budget, spent, used, status in rows:
        print(f"{budget.category:<14} [{bar(used)}] {used * 100:5.1f}%  "
              f"{format_money(spent)} / {format_money(budget.limit)}  {status}")


def monthly_report(service):
    month = parse_month(ask("Month YYYY-MM (blank = current): "))
    summary = service.monthly_summary(month)
    if summary is None:
        print(f"No expenses recorded for {month}.")
        return
    print(f"\n----- Report for {summary['month']} -----")
    print(f"Transactions : {summary['count']}")
    print(f"Total spent  : {format_money(summary['total'])}")
    print(f"Average      : {format_money(summary['mean'])}   Median: {format_money(summary['median'])}")
    print(f"Min / Max    : {format_money(summary['min'])} / {format_money(summary['max'])}")
    print(f"Std. dev.    : {format_money(summary['std'])}")
    print(f"Largest      : {summary['largest']}")
    print("\nBy category:")
    for category, total, percent in summary["breakdown"]:
        print(f"  {category:<14} {format_money(total):>10}  {percent:5.1f}%  [{bar(percent / 100)}]")


def spending_trend(service):
    trend = service.monthly_trend()
    if not trend:
        print("No data yet.")
        return
    peak = max(total for _, total in trend)
    print("\nMonthly spending trend")
    for month, total in trend:
        print(f"{month}  {format_money(total):>12}  [{bar(total / peak, 30)}]")


def export_csv(service):
    name = ask("File name (blank = expenses.csv): ") or "expenses.csv"
    print(f"Exported to {service.export_csv(name)}")


ACTIONS = {
    "1": add_expense, "2": view_expenses, "3": edit_expense, "4": delete_expense,
    "5": search_expenses, "6": set_budget, "7": budget_status,
    "8": monthly_report, "9": spending_trend, "10": export_csv,
}


def main():
    parser = argparse.ArgumentParser(description="Expense Tracker & Analyzer")
    parser.add_argument("--data", default=storage.DATA_FILE, help="path to the JSON data file")
    args = parser.parse_args()

    try:
        service = ExpenseService(args.data)
    except storage.StorageError as error:
        print(f"Startup problem: {error}")
        return

    log.info("Application started")
    while True:
        print(MENU)
        try:
            choice = ask("Choose an option: ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if choice == "0":
            print("Goodbye!")
            break
        action = ACTIONS.get(choice)
        if action is None:
            print("Invalid choice. Enter a number from the menu.")
            continue
        try:
            action(service)
        except (ValidationError, NotFoundError, storage.StorageError) as error:
            print(f"Error: {error}")  # friendly message, program keeps running
        except (EOFError, KeyboardInterrupt):
            print("\nInput cancelled.")
            break
        except Exception as error:  # last-resort safety net
            log.exception("Unexpected error")
            print(f"Unexpected error: {error}")
    log.info("Application closed")


if __name__ == "__main__":
    main()
