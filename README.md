# Expense Tracker & Analyzer

A command-line application for recording personal expenses, setting category budgets, and analysing spending patterns. Built in Python as the *Build Your Own Project* for the VITyarthi **Python Essentials** course.

## Features

- **Expense management:** add, view, edit, delete, and search expenses (by keyword, category, and amount range)
- **Recurring expenses:** mark an expense as weekly, monthly, or yearly
- **Budgets and alerts:** set a monthly limit per category, see a progress bar for each budget, and get a warning when an expense pushes a category over its limit
- **Monthly report:** transaction count, total, mean, median, min/max, standard deviation, largest expense, and a per-category percentage breakdown
- **Spending trend:** month-by-month totals shown as a text bar chart
- **CSV export:** save all expenses to a CSV file for use in Excel or Google Sheets
- **Persistent storage:** data is saved in a JSON file between runs
- **Robust input handling:** invalid input shows a friendly message instead of crashing, and unexpected errors are written to a log

## Project Structure

```
expense-tracker/
├── README.md          # this file
├── statement.md       # problem statement, scope, and requirements
├── main.py            # command-line entry point (menu and user interaction)
├── screenshots/       # screenshots of the program running
└── modules/
    ├── storage.py     # reading/writing the JSON data file
    ├── services.py    # business logic: expenses, budgets, reports, export
    └── utils.py       # validation, parsing, formatting, logging helpers
```

## Requirements

- Python 3.8 or newer
- No third-party packages (standard library only)

## How to Run

```bash
# clone the repository
git clone <your-repository-url>
cd expense-tracker

# run with the default data file (data/expenses.json)
python main.py

# or use a different data file
python main.py --data my_expenses.json
```

## Menu

```
 1. Add expense            6. Set category budget
 2. View expenses          7. Budget status
 3. Edit expense           8. Monthly report
 4. Delete expense         9. Spending trend
 5. Search expenses       10. Export to CSV
                           0. Exit
```

## Example Session

```
Choose an option: 1
Amount: 450
Category (e.g. Food, Travel): Food
Description (optional): Lunch with friends
Date YYYY-MM-DD (blank = today):
Recurring? (y/N): n
Saved -> 1     2026-09-30  Food                450  Lunch with friends
```

Screenshots are added in the `screenshots/` folder to show each menu option in use.

## Design Overview

The program is split into three layers so each part has one job:

| Layer | File | Responsibility |
|-------|------|----------------|
| Interface | `main.py` | Shows the menu, reads input, prints results, catches errors |
| Logic | `modules/services.py` | Rules for expenses, budgets, statistics, trends, and CSV export |
| Data | `modules/storage.py` | Loading and saving the JSON file |
| Helpers | `modules/utils.py` | Input validation, month/amount parsing, money formatting, progress bars, logger |

Errors are raised as specific exceptions (`ValidationError`, `NotFoundError`, `StorageError`) in the lower layers and handled in one place in `main.py`, so the menu keeps running after a bad input.

## Python Concepts Used

Functions and modules, dictionaries and lists, classes and objects (OOP), exception handling, file I/O (JSON and CSV), string formatting, command-line arguments with `argparse`, and basic statistics (mean, median, standard deviation).

## Author

Aman Kumar
Reg. No. 26BCE10228
VITyarthi, Python Essentials



