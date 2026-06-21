from rich.console import Group
from rich.table import Table
from rich.text import Text

from sage.cli.state import AppState
from sage.domain.money import format_amount

def get_browse_renderable(state: AppState):
    table = Table(show_lines=True, expand=True)
    table.add_column("Date", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Amount", justify="right")
    table.add_column("Category", style="magenta")
    table.add_column("Rule", style="dim")
    
    filtered = state.get_filtered_transactions()
    per_page = 15
    start = state.browse_page * per_page
    end = start + per_page
    
    for tx_cat in filtered[start:end]:
        amt = tx_cat.tx.amount
        amt_str = f"[green]{format_amount(amt)} PLN[/green]" if amt >= 0 else f"[red]{format_amount(amt)} PLN[/red]"
        desc = tx_cat.tx.description
        if len(desc) > 35: desc = desc[:32] + "..."
        table.add_row(
            str(tx_cat.tx.date),
            desc,
            amt_str,
            tx_cat.result.category,
            tx_cat.result.rule_name or "-"
        )
        
    total_pages = max(1, (len(filtered)-1)//per_page + 1)
    footer_text = f"Page {state.browse_page + 1} of {total_pages} | Total: {len(filtered)} items"
    if state.search_query:
        footer_text += f" | Search: '{state.search_query}'"
    if state.rule_filter:
        footer_text += f" | Rule: '{state.rule_filter}'"
        
    return Group(table, Text(footer_text, justify="center", style="bold"))
