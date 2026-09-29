"""Expense Tracker & Analyzer - the command line part of the project.

How to run it:
    python main.py                  -> uses data/expenses.json
    python main.py --data my.json   -> uses a different data file
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

TABLE_HEADER = f"{'ID':<5} {'Date':<11} {'Category':<14} {'Amount':>10}  Description"
LINE = "-" * 70


def ask(prompt):
    """Read a line from the user and strip the extra spaces."""
    return input(prompt).strip()


def ask_int(prompt):
    """Ask for a whole number, complain if the user types something else."""
    text = ask(prompt)
    try:
        return int(text)
    except ValueError:
        raise ValidationError("That doesn't look like a whole number, please try again.")


def print_expenses(expenses):
    """Show a list of expenses as a small table with a total at the bottom."""
    if len(expenses) == 0:
        print("Nothing to show - no expenses found.")
        return

    print(TABLE_HEADER)
    print(LINE)
    total = 0
    for expense in expenses:
        print(expense)
        total += expense.amount
    print(LINE)
    print(f"{len(expenses)} record(s), total {format_money(total)}")


# ------------------------------------------------------------
# Menu actions - one function for each menu option
# ------------------------------------------------------------
def add_expense(service):
    amount = ask("Amount: ")
    category = ask("Category (for example Food, Travel): ")
    description = ask("Description (you can skip this): ")
    date = ask("Date as YYYY-MM-DD (press Enter for today): ")

    is_recurring = ask("Is this a recurring expense? (y/N): ").lower() == "y"
    if is_recurring:
        frequency = ask("How often - weekly, monthly or yearly? ")
    else:
        frequency = "monthly"

    expense = service.add_expense(amount, category, description, date, is_recurring, frequency)
    print(f"Saved: {expense}")

    # warn the user if this expense pushes them over a budget
    alert = service.check_alert(expense)
    if alert:
        print(f"*** {alert} ***")


def view_expenses(service):
    month = ask("Month as YYYY-MM (press Enter to see everything): ")
    if month:
        month = parse_month(month)
    else:
        month = None
    print_expenses(service.list_expenses(month))


def edit_expense(service):
    expense_id = ask_int("ID of the expense to edit: ")
    current = service.get_expense(expense_id)
    print(f"Current: {current}")
    print("(press Enter on any field to keep the old value)")

    new_amount = ask("New amount: ")
    new_category = ask("New category: ")
    new_description = ask("New description: ")
    new_date = ask("New date: ")

    updated = service.update_expense(
        expense_id,
        amount=new_amount,
        category=new_category,
        description=new_description,
        date=new_date,
    )
    print(f"Updated: {updated}")


def delete_expense(service):
    expense_id = ask_int("ID of the expense to delete: ")
    print(f"You are about to delete: {service.get_expense(expense_id)}")

    if ask("Are you sure? (y/N): ").lower() == "y":
        service.delete_expense(expense_id)
        print("Deleted.")
    else:
        print("Okay, nothing was deleted.")


def search_expenses(service):
    keyword = ask("Keyword (Enter to skip): ")
    category = ask("Category (Enter to skip): ")
    low = ask("Minimum amount (Enter to skip): ")
    high = ask("Maximum amount (Enter to skip): ")

    # only convert the amounts if the user actually typed something
    min_amount = parse_amount(low) if low else None
    max_amount = parse_amount(high) if high else None

    print_expenses(service.search(keyword, category, min_amount, max_amount))


def set_budget(service):
    category = ask("Category: ")
    limit = ask("Monthly limit: ")
    budget = service.set_budget(category, limit)
    print(f"Budget set: {budget.category} = {format_money(budget.limit)} per month")


def budget_status(service):
    month = parse_month(ask("Month as YYYY-MM (press Enter for this month): "))
    rows = service.budget_report(month)
    if not rows:
        print("You haven't set any budgets yet. Use option 6 to add one.")
        return

    print(f"\nBudget status for {month}")
    for budget, spent, used, status in rows:
        print(f"{budget.category:<14} [{bar(used)}] {used * 100:5.1f}%  "
              f"{format_money(spent)} / {format_money(budget.limit)}  {status}")


def monthly_report(service):
    month = parse_month(ask("Month as YYYY-MM (press Enter for this month): "))
    summary = service.monthly_summary(month)
    if summary is None:
        print(f"No expenses were recorded for {month}.")
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
        print("There is no data yet.")
        return

    # the biggest month gets a full bar, the others are scaled against it
    peak = max(total for _, total in trend)
    print("\nMonthly spending trend")
    for month, total in trend:
        print(f"{month}  {format_money(total):>12}  [{bar(total / peak, 30)}]")


def export_csv(service):
    name = ask("File name (press Enter for expenses.csv): ")
    if not name:
        name = "expenses.csv"
    path = service.export_csv(name)
    print(f"Exported to {path}")


# maps what the user types to the function that handles it
ACTIONS = {
    "1": add_expense,
    "2": view_expenses,
    "3": edit_expense,
    "4": delete_expense,
    "5": search_expenses,
    "6": set_budget,
    "7": budget_status,
    "8": monthly_report,
    "9": spending_trend,
    "10": export_csv,
}


def main():
    parser = argparse.ArgumentParser(description="Expense Tracker & Analyzer")
    parser.add_argument("--data", default=storage.DATA_FILE,
                        help="path to the JSON file where expenses are stored")
    args = parser.parse_args()

    try:
        service = ExpenseService(args.data)
    except storage.StorageError as error:
        print(f"Could not start the app: {error}")
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
            print("That's not a valid option, please pick a number from the menu.")
            continue

        try:
            action(service)
        except (ValidationError, NotFoundError, storage.StorageError) as error:
            # expected problems: show a friendly message and keep going
            print(f"Error: {error}")
        except (EOFError, KeyboardInterrupt):
            print("\nInput cancelled.")
            break
        except Exception as error:
            # anything we didn't plan for - log it so the program doesn't just crash
            log.exception("Unexpected error")
            print(f"Something unexpected went wrong: {error}")

    log.info("Application closed")


if __name__ == "__main__":
    main()
    