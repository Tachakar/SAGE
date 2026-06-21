import operator
from decimal import Decimal

from rich.table import Table
from sage.cli.state import AppState
from sage.domain.conditions import Amount, And, Contains, Or
from sage.domain.rule import Rule

from sage.domain.conditions import Amount, And, Contains, Not, Or, Condition
from sage.storage.serialization import OPERATOR_TO_NAME

def format_condition(cond: Condition) -> str:
    if isinstance(cond, Contains):
        return f"Contains('{cond.text}')"
    elif isinstance(cond, Amount):
        op_name = OPERATOR_TO_NAME.get(cond.op, "??")
        sym = {"gt": ">", "lt": "<", "eq": "=", "ge": ">=", "le": "<=", "ne": "!="}.get(op_name, op_name)
        name = "|Amount|" if getattr(cond, "absolute", False) else "Amount"
        return f"{name} {sym} {cond.threshold}"
    elif isinstance(cond, And):
        return f"({format_condition(cond.left)} AND {format_condition(cond.right)})"
    elif isinstance(cond, Or):
        return f"({format_condition(cond.left)} OR {format_condition(cond.right)})"
    elif isinstance(cond, Not):
        return f"NOT {format_condition(cond.condition)}"
    return cond.__class__.__name__

def get_builder_renderable(state: AppState):
    table = Table(show_lines=True, expand=True)
    table.add_column("Type", justify="center")
    table.add_column("Priority", style="cyan", justify="right")
    table.add_column("Name", style="white")
    table.add_column("Category", style="magenta")
    table.add_column("Condition", style="dim")
    
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
