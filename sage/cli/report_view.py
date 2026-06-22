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
    
    month_totals = {}
    for tx_cat in state.transactions:
        key = (tx_cat.tx.date.year, tx_cat.tx.date.month)
        amt = tx_cat.tx.amount
        if key not in month_totals:
            month_totals[key] = {"total": Decimal('0'), "income": Decimal('0'), "expenses": Decimal('0')}
        month_totals[key]["total"] += amt
        if amt > 0:
            month_totals[key]["income"] += amt
        else:
            month_totals[key]["expenses"] += amt
    
    max_cat_abs = max([abs(v) for v in cat_totals.values()] + [Decimal('0.01')])
    
    cat_table = Table(title="By Category", expand=True)
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Total", justify="right")
    for cat in sorted(cat_totals.keys()):
        tot = cat_totals[cat]
        color = "green" if tot >= 0 else "red"
        pct = float(abs(tot) / max_cat_abs)
        cat_table.add_row(cat, f"[{color}]{format_amount(tot)} PLN[/{color}]")
        
    actual_total_inc = sum([v["income"] for v in month_totals.values()]) if month_totals else Decimal('0')
    actual_total_exp = sum([v["expenses"] for v in month_totals.values()]) if month_totals else Decimal('0')
    actual_total_net = sum([v["total"] for v in month_totals.values()]) if month_totals else Decimal('0')
    
    total_inc = actual_total_inc if actual_total_inc > 0 else Decimal('0.01')
    total_exp_abs = sum([abs(v["expenses"]) for v in month_totals.values()]) if month_totals else Decimal('0')
    total_exp = total_exp_abs if total_exp_abs > 0 else Decimal('0.01')
    total_net_abs = sum([abs(v["total"]) for v in month_totals.values()]) if month_totals else Decimal('0')
    total_net_abs = total_net_abs if total_net_abs > 0 else Decimal('0.01')
    
    month_table = Table(title="By Month", expand=True)
    month_table.add_column("Month", style="cyan")
    month_table.add_column("Earnings", justify="right", style="green")
    month_table.add_column("Graph", justify="left")
    month_table.add_column("Spendings", justify="right", style="red")
    month_table.add_column("Graph", justify="left")
    month_table.add_column("Net", justify="right")
    for (year, month) in sorted(month_totals.keys()):
        data = month_totals[(year, month)]
        tot = data["total"]
        inc = data["income"]
        exp = data["expenses"]
        color = "green" if tot >= 0 else "red"
        
        inc_pct = float(inc / total_inc)
        exp_pct = float(abs(exp) / total_exp)
        net_pct = float(abs(tot) / total_net_abs)
        
        month_table.add_row(
            f"{year}-{month:02d}", 
            f"{format_amount(inc)} PLN ({inc_pct*100:.1f}%)", 
            make_bar(inc_pct, width=10, color="green"),
            f"{format_amount(exp)} PLN ({exp_pct*100:.1f}%)", 
            make_bar(exp_pct, width=10, color="red"),
            f"[{color}]{format_amount(tot)} PLN ({net_pct*100:.1f}%)[/{color}]"
        )
        
    if month_totals:
        month_table.add_row("", "", "", "", "", "")
        net_col = "green" if actual_total_net >= 0 else "red"
        month_table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold green]{format_amount(actual_total_inc)} PLN[/bold green]",
            "",
            f"[bold red]{format_amount(actual_total_exp)} PLN[/bold red]",
            "",
            f"[bold {net_col}]{format_amount(actual_total_net)} PLN[/bold {net_col}]"
        )
        
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
