import operator
from decimal import Decimal

from rich.table import Table
from sage.cli.state import AppState
from sage.domain.conditions import Amount, And, Contains, Or
from sage.domain.rule import Rule

from sage.domain.conditions import Amount, And, Contains, Not, Or, Condition
from sage.storage.serialization import OPERATOR_TO_NAME

COMPARISON_WORDS = {"gt": "more than", "ge": "at least", "lt": "less than", "le": "at most", "eq": "exactly", "ne": "not equal to"}
FLIPPED_OP_NAME = {"gt": "lt", "ge": "le", "lt": "gt", "le": "ge", "eq": "eq", "ne": "ne"}

def format_condition(cond: Condition) -> str:
    if isinstance(cond, Contains):
        return f"description contains '{cond.text}'"
    elif isinstance(cond, Amount):
        op_name = OPERATOR_TO_NAME.get(cond.op, "??")
        if getattr(cond, "absolute", False):
            return f"the amount is {COMPARISON_WORDS.get(op_name, op_name)} {abs(cond.threshold)} zł"
        elif cond.threshold < 0:
            magnitude_name = FLIPPED_OP_NAME.get(op_name, op_name)
            return f"spent {COMPARISON_WORDS.get(magnitude_name, magnitude_name)} {abs(cond.threshold)} zł"
        else:
            return f"received {COMPARISON_WORDS.get(op_name, op_name)} {cond.threshold} zł"
    elif isinstance(cond, And):
        return f"{format_condition(cond.left)} and {format_condition(cond.right)}"
    elif isinstance(cond, Or):
        return f"{format_condition(cond.left)} or {format_condition(cond.right)}"
    elif isinstance(cond, Not):
        return f"not ({format_condition(cond.condition)})"
    return ""

def get_builder_renderable(state: AppState):
    table = Table(show_lines=True, expand=True)
    table.add_column("Type", justify="center")
    table.add_column("Order", style="cyan", justify="right")
    table.add_column("Name", style="white")
    table.add_column("Category", style="magenta")
    table.add_column("Matches when", style="dim")
    
    for r in state.rules:
        if r in state.default_rules:
            r_type = "[dim]Default[/dim]"
            priority = f"[dim]{r.priority}[/dim]"
            name = f"[dim]{r.name}[/dim]"
            category = f"[dim]{r.category}[/dim]"
            condition = f"[dim]{format_condition(r.condition)}[/dim]"
        else:
            r_type = "[green]User[/green]"
            priority = str(r.priority)
            name = str(r.name)
            category = str(r.category)
            condition = format_condition(r.condition)
            
        table.add_row(r_type, priority, name, category, condition)
        
    return table
