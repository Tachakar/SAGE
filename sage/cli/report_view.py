from rich.columns import Columns
from rich.text import Text
from rich.table import Table

from sage.cli.state import AppState
from sage.domain.money import format_amount
from sage.reports.aggregate import by_month, group_by_category

def get_reports_renderable(state: AppState):
    if not state.transactions:
        return Text("No transactions available. Import a CSV first.", style="bold yellow", justify="center")
        
    cat_totals = group_by_category(state.transactions)
    month_totals = by_month(state.transactions)
    
    cat_table = Table(title="By Category", expand=True)
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Total", justify="right")
    for cat in sorted(cat_totals.keys()):
        tot = cat_totals[cat]
        color = "green" if tot >= 0 else "red"
        cat_table.add_row(cat, f"[{color}]{format_amount(tot)} PLN[/{color}]")
        
    month_table = Table(title="By Month", expand=True)
    month_table.add_column("Month", style="cyan")
    month_table.add_column("Total", justify="right")
    for (year, month) in sorted(month_totals.keys()):
        tot = month_totals[(year, month)]
        color = "green" if tot >= 0 else "red"
        month_table.add_row(f"{year}-{month:02d}", f"[{color}]{format_amount(tot)} PLN[/{color}]")
        
    return Columns([cat_table, month_table], expand=True)
