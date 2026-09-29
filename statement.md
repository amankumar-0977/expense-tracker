# Problem Statement

## Problem
Students and young professionals often lose track of where their money goes. Spreadsheets are
tedious to maintain, and most apps are heavy, need accounts, or hide the data. There is a need
for a lightweight, offline tool that records expenses quickly, warns when spending crosses a
budget, and turns raw entries into clear monthly summaries.

## Scope
- A command-line application written in pure Python (NumPy for calculations).
- Local JSON storage; no network, accounts, or external services.
- Single-user, single-currency (amounts are plain numbers).
- Out of scope: bank integration, GUI/web front-end, multi-user support.

## Target Users
- Students managing a monthly allowance.
- Individuals who want a simple personal expense log without installing large apps.

## High-Level Features
1. **Expense management (CRUD):** add, view, edit, delete and search expenses; recurring expenses supported.
2. **Budgets & alerts:** set a monthly budget per category and get warnings at 80% and 100% usage.
3. **Reports & analytics:** monthly summary, category breakdown with percentages, statistics (mean, median, max), top categories, and CSV export.
4. **Reliability:** input validation, safe file writes with automatic backup, and activity logging.
