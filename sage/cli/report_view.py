from decimal import Decimal
from rich.columns import Columns
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.console import Group

from sage.cli.state import AppState
from sage.domain.money import format_amount
from sage.reports.aggregate import by_month, group_by_category

def make_bar(percent: float, width: int = 20, color: str = "red") -> str:
    capped_pct = min(1.0, max(0.0, percent))
    filled = int(width * capped_pct)
    return f"[{color}]" + "█" * filled + "[/]" + "[dim]" + "░" * (width - filled) + "[/]"

def get_reports_renderable(state: AppState):
    if not state.transactions:
        return Text("No transactions available. Import a bank statement first.", style="bold yellow", justify="center")
        
    cat_totals = group_by_category(state.transactions)
    month_totals = by_month(state.transactions)
    
    max_cat_abs = max([abs(v) for v in cat_totals.values()] + [Decimal('0.01')])
    
    cat_table = Table(title="By Category", expand=True)
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Total", justify="right")
    cat_table.add_column("Graph")
    for cat in sorted(cat_totals.keys()):
        tot = cat_totals[cat]
        color = "green" if tot >= 0 else "red"
        pct = float(abs(tot) / max_cat_abs)
        cat_table.add_row(cat, f"[{color}]{format_amount(tot)} PLN[/{color}]", make_bar(pct, color=color))
        
    max_month_abs = max([abs(v) for v in month_totals.values()] + [Decimal('0.01')])
    
    month_table = Table(title="By Month", expand=True)
    month_table.add_column("Month", style="cyan")
    month_table.add_column("Total", justify="right")
    month_table.add_column("Graph")
    for (year, month) in sorted(month_totals.keys()):
        tot = month_totals[(year, month)]
        color = "green" if tot >= 0 else "red"
        pct = float(abs(tot) / max_month_abs)
        month_table.add_row(f"{year}-{month:02d}", f"[{color}]{format_amount(tot)} PLN[/{color}]", make_bar(pct, color=color))
        
    cols = Columns([cat_table, month_table], expand=True)
    
    total_expenses = sum((abs(tot) for tot in cat_totals.values() if tot < 0), Decimal("0"))
    
    if state.budget:
        num_months = max(1, len(month_totals))
        total_budget = state.budget * Decimal(str(num_months))
        pct = float(total_expenses / total_budget) if total_budget > 0 else 0.0
        pct_display = pct * 100
        bar_color = "red" if pct > 1.0 else ("yellow" if pct > 0.8 else "green")
        bar = make_bar(pct, width=50, color=bar_color)
        month_label = "month" if num_months == 1 else "months"
        budget_panel = Panel(f"Spent: {format_amount(total_expenses)} / Total Budget: {format_amount(total_budget)} PLN ({num_months} {month_label} @ {format_amount(state.budget)}/mo)\n{pct_display:.1f}%\n{bar}", title="Budget Spend")
    else:
        budget_panel = Panel("No budget set. Press 'e' to set a budget limit.", title="Budget Spend", border_style="dim")
        
    return Group(budget_panel, Text(""), cols)
