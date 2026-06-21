import sys
import termios
import time
import tty
from pathlib import Path
from decimal import Decimal
import operator

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import questionary

from sage.cli.state import AppState
from sage.cli.browse import get_browse_renderable
from sage.cli.report_view import get_reports_renderable
from sage.cli.rule_builder import get_builder_renderable
from sage.domain.categorization import CategorizedTransaction
from sage.domain.conditions import Amount, And, Contains, Or, any_of, all_of
from sage.domain.money import parse_amount
from sage.domain.rule import Rule
from sage.engine.categorizer import make_categorizer
from sage.ingest.registry import SUPPORTED_PARSER, detect_parser
from sage.storage.rule_store import load_rules, save_rules

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def get_available_csvs() -> list[tuple[str, str]]:
    paths = []
    root = Path(__file__).parent.parent.parent
    dirs = [Path("."), root / "data", root / "tests/fixtures"]
    for d in dirs:
        if d.exists() and d.is_dir():
            for p in d.glob("*.csv"):
                paths.append((p.name, str(p.absolute())))
    return sorted(list(set(paths)))

def timed(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        res = func(*args, **kwargs)
        dur = time.perf_counter() - start
        Console().print(f"\n[bold yellow]Pipeline elapsed time: {dur:.4f} seconds[/bold yellow]")
        return res
    return wrapper

@timed
def do_import(csv_path: Path, bank: str, rules: list) -> list[CategorizedTransaction]:
    parser = detect_parser(bank)
    txs = list(parser.parse(csv_path))
    categorize = make_categorizer(rules)
    return [CategorizedTransaction(tx, categorize(tx)) for tx in txs]

def draw_dashboard(console: Console, view: str, state: AppState):
    grid = Table.grid(expand=True)
    grid.add_column(ratio=1)
    grid.add_column(ratio=3)
    
    sidebar_content = f"""[bold]SAGE Finance[/bold]

[cyan]Transactions:[/cyan] {len(state.transactions)}
[cyan]Rules:[/cyan] {len(state.rules)}

[yellow]Current View:[/yellow]
{view.upper()}

[bold white]Global Keys:[/bold white]
[green]i[/green] Import CSV
[green]b[/green] Browse
[green]r[/green] Reports
[green]u[/green] Rule Builder
[green]q[/green] Quit/Back"""

    sidebar = Panel(sidebar_content, title="Status", border_style="cyan")
    
    if view == "browse":
        content = get_browse_renderable(state)
        keys = "[bold]Local Keys:[/bold] [green]j/n[/green] Next Pg | [green]k/p[/green] Prev Pg | [green]s[/green] Search | [green]l[/green] Rule Filter | [green]c[/green] Clear"
        main_content = Group(content, Text(""), Text.from_markup(keys, justify="center"))
    elif view == "reports":
        content = get_reports_renderable(state)
        main_content = Group(content, Text(""), Text.from_markup("[bold]Local Keys:[/bold] (None)", justify="center"))
    elif view == "builder":
        content = get_builder_renderable(state)
        keys = "[bold]Local Keys:[/bold] [green]a[/green] Add Rule | [green]e[/green] Edit Rule | [green]d[/green] Delete Rule"
        main_content = Group(content, Text(""), Text.from_markup(keys, justify="center"))
    else:
        main_content = "\n\nWelcome to SAGE! Press a key from the Global Keys menu to navigate."
        
    main_panel = Panel(main_content, title=view.capitalize(), border_style="blue")
    grid.add_row(sidebar, main_panel)
    
    console.clear()
    console.print(grid)

def main() -> None:
    console = Console()
    state = AppState(
        default_rules=load_rules(Path("data/default_rules.json")),
        user_rules=load_rules(Path("data/user_rules.json")),
        default_rules_path=Path("data/default_rules.json"),
        user_rules_path=Path("data/user_rules.json")
    )
    current_view = "main"
    
    while True:
        draw_dashboard(console, current_view, state)
        
        try:
            key = get_key().lower()
        except KeyboardInterrupt:
            break
            
        if key == '\x03':
            break
            
        if key == 'q':
            if current_view == "main":
                break
            else:
                current_view = "main"
        elif key == 'i':
            console.print()
            csvs = get_available_csvs()
            if not csvs:
                console.print("[red]No CSV files found in data/ or current directory.[/red]")
                time.sleep(1.5)
                continue
            csv_choices = [f"{lbl} ({path})" for lbl, path in csvs] + ["Cancel"]
            csv_choice = questionary.select("Select CSV to import:", choices=csv_choices).ask()
            if not csv_choice or csv_choice == "Cancel": continue
            
            idx = csv_choices.index(csv_choice)
            csv_path = Path(csvs[idx][1])
            bank = questionary.select("Select Bank:", choices=list(SUPPORTED_PARSER)).ask()
            if not bank: continue
            
            with console.status(f"[bold green]Importing from {csv_path.name}...", spinner="dots"):
                try:
                    state.transactions = do_import(csv_path, bank, state.rules)
                    console.print(f"[green]Successfully imported {len(state.transactions)} transactions.[/green]")
                except Exception as e:
                    console.print(f"[red]Error importing: {e}[/red]")
            time.sleep(1.5)
            current_view = "browse"
            
        elif key == 'b':
            if not state.transactions:
                console.print()
                console.print("[yellow]No transactions loaded. Please import first.[/yellow]")
                time.sleep(1.5)
            else:
                current_view = "browse"
        elif key == 'r':
            if not state.transactions:
                console.print()
                console.print("[yellow]No transactions loaded. Please import first.[/yellow]")
                time.sleep(1.5)
            else:
                current_view = "reports"
        elif key == 'u':
            current_view = "builder"
            
        elif current_view == "browse":
            filtered = state.get_filtered_transactions()
            max_pages = max(1, (len(filtered)-1)//15 + 1)
            
            if key in ('n', 'j') and state.browse_page < max_pages - 1:
                state.browse_page += 1
            elif key in ('p', 'k') and state.browse_page > 0:
                state.browse_page -= 1
            elif key == 's':
                console.print()
                query = questionary.text("Enter search query (empty to clear):").ask()
                if query is not None: state.search_query = query.strip().lower()
                state.browse_page = 0
            elif key == 'l':
                console.print()
                rules = sorted(list(set(r.name for r in state.rules)))
                choice = questionary.select("Select rule filter:", choices=["(None)"] + rules).ask()
                if choice:
                    state.rule_filter = choice if choice != "(None)" else None
                    if state.rule_filter:
                        hits = sum(1 for t in state.transactions if t.result.rule_name == state.rule_filter)
                        if hits == 0:
                            console.print(f"\n[yellow]No transaction matches the rule '{state.rule_filter}'.[/yellow]")
                            time.sleep(2)
                state.browse_page = 0
            elif key == 'c':
                state.search_query = ""
                state.rule_filter = None
                state.browse_page = 0
                
        elif current_view == "builder":
            def build_cond():
                c_type = questionary.select("Condition Type:", choices=["Description contains text", "Amount"]).ask()
                if not c_type: return None
                if c_type == "Description contains text":
                    text = questionary.text("Text to match:").ask()
                    if not text: return None
                    return Contains(text)
                else:
                    op_str = questionary.select("Operator:", choices=["Greater than", "Greater than or equal", "Less than", "Less than or equal", "Equal to"]).ask()
                    if not op_str: return None
                    mapping = {"Greater than": operator.gt, "Greater than or equal": operator.ge, "Less than": operator.lt, "Less than or equal": operator.le, "Equal to": operator.eq}
                    amt_str = questionary.text("Amount threshold:").ask()
                    if not amt_str: return None
                    try: amt = parse_amount(amt_str)
                    except ValueError: return None
                    abs_val = questionary.confirm("Check absolute value (ignore sign)?", default=True).ask()
                    if abs_val is None: return None
                    return Amount(mapping[op_str], amt, absolute=abs_val)

            if key == 'd':
                if not state.user_rules:
                    console.print()
                    console.print("[yellow]No user rules to delete. (Default rules cannot be deleted)[/yellow]")
                    time.sleep(1.5)
                    continue
                console.print()
                choices = [f"{r.priority} - {r.name} ({r.category})" for r in state.user_rules] + ["Cancel"]
                choice = questionary.select("Select rule to delete:", choices=choices).ask()
                if choice and choice != "Cancel":
                    idx = choices.index(choice)
                    deleted = state.user_rules.pop(idx)
                    save_rules(state.user_rules, state.user_rules_path)
                    console.print(f"[green]Deleted rule '{deleted.name}'[/green]")
                    if state.transactions:
                        categorize = make_categorizer(state.rules)
                        state.transactions = [CategorizedTransaction(ct.tx, categorize(ct.tx)) for ct in state.transactions]
                    time.sleep(1.5)
            elif key == 'e':
                if not state.user_rules:
                    console.print()
                    console.print("[yellow]No user rules to edit. (Default rules cannot be edited)[/yellow]")
                    time.sleep(1.5)
                    continue
                console.print()
                choices = [f"{r.priority} - {r.name} ({r.category})" for r in state.user_rules] + ["Cancel"]
                choice = questionary.select("Select rule to edit:", choices=choices).ask()
                if choice and choice != "Cancel":
                    idx = choices.index(choice)
                    rule = state.user_rules[idx]
                    
                    name = questionary.text("Rule Name:", default=rule.name).ask()
                    if not name: continue
                    
                    cats = sorted(list(set(r.category for r in state.rules)))
                    def_cat = rule.category if rule.category in cats else None
                    cat_choice = questionary.select("Category:", choices=cats + ["++ New Category ++"], default=def_cat).ask()
                    if not cat_choice: continue
                    if cat_choice == "++ New Category ++":
                        category = questionary.text("New Category Name:", default=rule.category).ask()
                        if not category: continue
                    else: category = cat_choice
                    
                    priority_str = questionary.text("Priority (lower = higher prio):", default=str(rule.priority)).ask()
                    if not priority_str: continue
                    try: priority = int(priority_str)
                    except ValueError: priority = rule.priority
                        
                    keep = questionary.confirm(f"Keep existing condition ({rule.condition.__class__.__name__})?").ask()
                    if keep:
                        final_cond = rule.condition
                    elif keep is False:
                        conds = []
                        while True:
                            c = build_cond()
                            if c: conds.append(c)
                            more = questionary.confirm(f"Add another condition? (Currently {len(conds)})", default=False).ask()
                            if not more: break
                        if not conds: continue
                        if len(conds) == 1:
                            final_cond = conds[0]
                        else:
                            join = questionary.select("How to join them?", choices=["ALL must match (AND)", "ANY can match (OR)"]).ask()
                            if join == "ALL must match (AND)": final_cond = all_of(conds)
                            elif join == "ANY can match (OR)": final_cond = any_of(conds)
                            else: continue
                    else:
                        continue
                        
                    new_rule = Rule(name=name, condition=final_cond, category=category, priority=priority)
                    state.user_rules[idx] = new_rule
                    state.user_rules.sort(key=lambda r: r.priority)
                    save_rules(state.user_rules, state.user_rules_path)
                    console.print(f"[green]Rule '{name}' updated![/green]")
                    if state.transactions:
                        categorize = make_categorizer(state.rules)
                        state.transactions = [CategorizedTransaction(ct.tx, categorize(ct.tx)) for ct in state.transactions]
                    time.sleep(1.5)
            elif key == 'a':
                console.print()
                name = questionary.text("Rule Name:").ask()
                if not name: continue
                
                cats = sorted(list(set(r.category for r in state.rules)))
                cat_choice = questionary.select("Category:", choices=cats + ["++ New Category ++"]).ask()
                if not cat_choice: continue
                if cat_choice == "++ New Category ++":
                    category = questionary.text("New Category Name:").ask()
                    if not category: continue
                else: category = cat_choice
                    
                priority_str = questionary.text("Priority (lower = higher prio, default 100):", default="100").ask()
                if not priority_str: continue
                try: priority = int(priority_str)
                except ValueError: priority = 100
                    
                conds = []
                while True:
                    c = build_cond()
                    if c: conds.append(c)
                    more = questionary.confirm(f"Add another condition? (Currently {len(conds)})", default=False).ask()
                    if not more: break
                if not conds: continue
                if len(conds) == 1:
                    final_cond = conds[0]
                else:
                    join = questionary.select("How to join them?", choices=["ALL must match (AND)", "ANY can match (OR)"]).ask()
                    if join == "ALL must match (AND)": final_cond = all_of(conds)
                    elif join == "ANY can match (OR)": final_cond = any_of(conds)
                    else: continue
                    
                new_rule = Rule(name=name, condition=final_cond, category=category, priority=priority)
                state.user_rules.append(new_rule)
                state.user_rules.sort(key=lambda r: r.priority)
                save_rules(state.user_rules, state.user_rules_path)
                console.print(f"[green]Rule '{name}' added![/green]")
                if state.transactions:
                    categorize = make_categorizer(state.rules)
                    state.transactions = [CategorizedTransaction(ct.tx, categorize(ct.tx)) for ct in state.transactions]
                time.sleep(1.5)

if __name__ == "__main__":
    main()
