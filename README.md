# SAGE - Spending Analysis and Grouping Engine

A terminal app for personal finance. SAGE imports bank statement CSVs, automatically categorizes each transaction using user-defined rules, and lets you browse transactions and spending reports - all locally, with no network calls.

## Features

- Import CSV exports from Millennium, mBank, and PKO
- Automatic categorization based on configurable rules (text match / amount comparisons, combinable with AND/OR/NOT)
- Interactive rule builder in the terminal
- Browse transactions with search and filtering
- Reports grouped by category and by month
- Monthly budget tracking
- Session persistence between runs

## Requirements

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/)

## Installation

```
git clone git@github.com:Tachakar/SAGE.git
cd SAGE
uv sync
```

## Usage

Before running the app, place your bank statement CSV file in the `data/` directory.

```
uv run sage
```

Global keys: `i` import statement, `b` browse, `r` reports, `u` rule builder, `q` quit/back, `Esc` back.

## Views

- Browse - lists imported transactions with search and rule filtering.
- Reports - shows spending totals grouped by category and by month.
- Rule builder - add, edit, or delete categorization rules.

## Running tests

```
uv run pytest
```

## Project structure

```
sage/
  domain/    # Transaction, Rule, Condition - immutable data models, no external deps
  engine/    # categorization engine (make_categorizer)
  ingest/    # BankParser strategy + concrete parsers (Millennium, mBank, PKO) + registry
  storage/   # JSON serialization for rules and session state
  reports/   # aggregation (by category, by month)
  cli/       # terminal interface (rich + questionary)
```

Adding a new bank only requires a new `BankParser` subclass in `sage/ingest/parsers/` and an entry in `sage/ingest/registry.py`.

