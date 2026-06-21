import select
import sys
import termios
import time
import tty
from pathlib import Path
from decimal import Decimal
import operator

from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import questionary

from sage.cli.state import AppState
from sage.cli.browse import get_browse_renderable
from sage.cli.report_view import get_reports_renderable
from sage.cli.rule_builder import get_builder_renderable, format_condition
from sage.domain.categorization import CategorizedTransaction
from sage.domain.conditions import Amount, And, Contains, Or, any_of, all_of
from sage.domain.money import parse_amount
from sage.domain.rule import Rule
from sage.engine.categorizer import make_categorizer
from sage.ingest.registry import SUPPORTED_PARSER, detect_parser
from sage.storage.rule_store import load_rules, save_rules
from sage.storage.session_store import load_session, save_session

SESSION_PATH = Path("data/session.json")

ESC = "\x1b"

def get_key() -> str:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == ESC:
            if select.select([sys.stdin], [], [], 0.05)[0]:
                sys.stdin.read(1)
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    sys.stdin.read(1)
                return ""
            return "esc"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

ESCAPE_KB = KeyBindings()

@ESCAPE_KB.add("escape", eager=True)
def _cancel_on_escape(event):
    event.app.exit(exception=KeyboardInterrupt)

def ask(question):
    try:
        question.application.key_bindings.add("escape", eager=True)(_cancel_on_escape)
    except AttributeError:
        pass
    return question.ask()

def qtext(*args, **kwargs):
    kwargs.setdefault("key_bindings", ESCAPE_KB)
    return ask(questionary.text(*args, **kwargs))

def qselect(*args, **kwargs):
    return ask(questionary.select(*args, **kwargs))

def qconfirm(*args, **kwargs):
    return ask(questionary.confirm(*args, **kwargs))

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
        Console().print(f"\n[bold yellow]Imported in {dur:.2f} seconds[/bold yellow]")
        return res
    return wrapper

@timed
def do_import(csv_path: Path, bank: str, rules: list) -> list[CategorizedTransaction]:
    parser = detect_parser(bank)
    txs = list(parser.parse(csv_path))
    categorize = make_categorizer(rules)
    return [CategorizedTransaction(tx, categorize(tx)) for tx in txs]

def persist_session(state: AppState) -> None:
    if not state.last_csv_path or not state.last_bank:
        return
    save_session({
        "csv_path": state.last_csv_path,
        "bank": state.last_bank,
        "search_query": state.search_query,
        "rule_filter": state.rule_filter,
        "browse_page": state.browse_page,
        "budget": str(state.budget) if state.budget is not None else None,
    }, SESSION_PATH)

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
[green]i[/green] Import statement
[green]b[/green] Browse
[green]r[/green] Reports
[green]u[/green] Rule Builder
[green]q[/green] Quit/Back | [green]Esc[/green] Back"""

    sidebar = Panel(sidebar_content, title="Status", border_style="cyan")
    
    if view == "browse":
        content = get_browse_renderable(state)
        keys = "[bold]Local Keys:[/bold] [green]j/n[/green] Next Pg | [green]k/p[/green] Prev Pg | [green]gg/G[/green] Top/Bottom | [green]s[/green] Search | [green]l[/green] Rule Filter | [green]c[/green] Clear"
        main_content = Group(content, Text(""), Text.from_markup(keys, justify="center"))
    elif view == "reports":
        content = get_reports_renderable(state)
        keys = "[bold]Local Keys:[/bold] [green]e[/green] Edit Budget"
        main_content = Group(content, Text(""), Text.from_markup(keys, justify="center"))
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

def safe_load_rules(console: Console, path: Path) -> list[Rule]:
    try:
        return load_rules(path)
    except Exception as e:
        console.print(f"\n[bold red]FATAL ERROR[/bold red]: Failed to load rules from [yellow]{path}[/yellow].")
        console.print(f"[red]Reason:[/red] {e}")
        console.print("Please fix the file or delete it.")
        sys.exit(1)

def main() -> None:
    console = Console()
    
    default_rules_path = Path("data/default_rules.json")
    user_rules_path = Path("data/user_rules.json")
    
    state = AppState(
        default_rules=safe_load_rules(console, default_rules_path),
        user_rules=safe_load_rules(console, user_rules_path),
        default_rules_path=default_rules_path,
        user_rules_path=user_rules_path
    )
    current_view = "main"

    session = load_session(SESSION_PATH)
    if session and session.get("csv_path") and Path(session["csv_path"]).exists():
        csv_path = Path(session["csv_path"])
        bank = session["bank"]
        try:
            with console.status(f"[bold cyan]Restoring last session: {csv_path.name}...[/bold cyan]", spinner="dots"):
                state.transactions = do_import(csv_path, bank, state.rules)
            state.last_csv_path = str(csv_path)
            state.last_bank = bank
            state.search_query = session.get("search_query", "")
            state.rule_filter = session.get("rule_filter")
            state.browse_page = session.get("browse_page", 0)
            budget_str = session.get("budget")
            if budget_str:
                state.budget = Decimal(budget_str)
            current_view = "browse"
        except Exception as e:
            console.print(f"[red]Could not restore last session: {e}[/red]")
            time.sleep(1.5)
            SESSION_PATH.unlink(missing_ok=True)

    try:
        _run_loop(console, state, current_view)
    finally:
        persist_session(state)

def _run_loop(console: Console, state: AppState, current_view: str) -> None:
    while True:
        draw_dashboard(console, current_view, state)

        try:
            raw_key = get_key()
        except KeyboardInterrupt:
            break
        key = raw_key.lower()

        if key == '\x03':
            break

        if key == 'q':
            if current_view == "main":
                break
            else:
                current_view = "main"
        elif raw_key == "esc":
            if current_view != "main":
                current_view = "main"
        elif key == 'i':
            console.print()
            csvs = get_available_csvs()
            if not csvs:
                console.print("[red]No bank statement files found.[/red]")
                time.sleep(1.5)
                continue
            csv_choices = [f"{lbl} ({path})" for lbl, path in csvs] + ["Cancel"]
            csv_choice = qselect("Select a bank statement to import:", choices=csv_choices)
            if not csv_choice or csv_choice == "Cancel": continue
            
            idx = csv_choices.index(csv_choice)
            csv_path = Path(csvs[idx][1])
            bank = qselect("Select Bank:", choices=list(SUPPORTED_PARSER))
            if not bank: continue
            
            with console.status(f"[bold green]Importing from {csv_path.name}...", spinner="dots"):
                try:
                    state.transactions = do_import(csv_path, bank, state.rules)
                    console.print(f"[green]Successfully imported {len(state.transactions)} transactions.[/green]")
                    state.last_csv_path = str(csv_path)
                    state.last_bank = bank
                    state.search_query = ""
                    state.rule_filter = None
                    state.browse_page = 0
                    persist_session(state)
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
            elif raw_key == 'G':
                state.browse_page = max_pages - 1
            elif key == 'g':
                if get_key().lower() == 'g':
                    state.browse_page = 0
            elif key == 's':
                console.print()
                query = qtext("Enter search query (empty to clear):")
                if query is not None: state.search_query = query.strip().lower()
                state.browse_page = 0
                persist_session(state)
            elif key == 'l':
                console.print()
                rules = sorted(list(set(r.name for r in state.rules)))
                choice = qselect("Select rule filter:", choices=["(None)"] + rules)
                if choice:
                    state.rule_filter = choice if choice != "(None)" else None
                    if state.rule_filter:
                        hits = sum(1 for t in state.transactions if t.result.rule_name == state.rule_filter)
                        if hits == 0:
                            console.print(f"\n[yellow]No transaction matches the rule '{state.rule_filter}'.[/yellow]")
                            time.sleep(2)
                state.browse_page = 0
                persist_session(state)
            elif key == 'c':
                state.search_query = ""
                state.rule_filter = None
                state.browse_page = 0
                persist_session(state)
                
        elif current_view == "reports":
            if key == 'e':
                console.print()
                budget_str = qtext("Enter monthly budget limit:", default=str(state.budget) if state.budget else "")
                if budget_str is not None:
                    budget_str = budget_str.strip()
                    if budget_str == "":
                        state.budget = None
                        persist_session(state)
                    else:
                        try:
                            state.budget = parse_amount(budget_str)
                            persist_session(state)
                        except Exception:
                            console.print("[red]Invalid budget amount[/red]")
                            time.sleep(1.5)
                            
        elif current_view == "builder":
            COMPARISON_OPS = {
                "More than": operator.gt, "At least": operator.ge, "Less than": operator.lt,
                "At most": operator.le, "Exactly": operator.eq,
            }
            FLIP_OP = {operator.gt: operator.lt, operator.ge: operator.le, operator.lt: operator.gt, operator.le: operator.ge, operator.eq: operator.eq}

            def build_cond():
                c_type = qselect("What should this condition check?", choices=["The description contains some text", "How much money was involved"])
                if not c_type: return None
                if c_type == "The description contains some text":
                    text = qtext("Text to match:")
                    if not text: return None
                    return Contains(text), f"description contains '{text}'"
                else:
                    direction = qselect("This amount is:", choices=["Money spent (expense)", "Money received (income)", "Either direction (by magnitude)"])
                    if not direction: return None
                    comp_str = qselect("Compare the amount:", choices=list(COMPARISON_OPS.keys()))
                    if not comp_str: return None
                    amt_str = qtext("Amount (always positive, e.g. 150):")
                    if not amt_str: return None
                    try: amt = parse_amount(amt_str)
                    except ValueError: return None
                    magnitude_op = COMPARISON_OPS[comp_str]
                    comp_word = comp_str.lower()
                    if direction == "Money spent (expense)":
                        op, threshold, absolute = FLIP_OP[magnitude_op], (-amt if amt != 0 else amt), False
                        summary = f"spent {comp_word} {amt} zł"
                    elif direction == "Money received (income)":
                        op, threshold, absolute = magnitude_op, amt, False
                        summary = f"received {comp_word} {amt} zł"
                    else:
                        op, threshold, absolute = magnitude_op, amt, True
                        summary = f"the amount (regardless of direction) is {comp_word} {amt} zł"
                    return Amount(op, threshold, absolute=absolute), summary

            if key == 'd':
                if not state.user_rules:
                    console.print()
                    console.print("[yellow]No user rules to delete. (Default rules cannot be deleted)[/yellow]")
                    time.sleep(1.5)
                    continue
                console.print()
                choices = [f"{r.priority} - {r.name} ({r.category})" for r in state.user_rules] + ["Cancel"]
                choice = qselect("Select rule to delete:", choices=choices)
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
                choice = qselect("Select rule to edit:", choices=choices)
                if choice and choice != "Cancel":
                    idx = choices.index(choice)
                    rule = state.user_rules[idx]
                    
                    name = qtext("What should this rule be called?", default=rule.name)
                    if not name: continue
                    
                    cats = sorted(list(set(r.category for r in state.rules)))
                    def_cat = rule.category if rule.category in cats else None
                    cat_choice = qselect("Category:", choices=cats + ["Create a new category"], default=def_cat)
                    if not cat_choice: continue
                    if cat_choice == "Create a new category":
                        category = qtext("What should the new category be called?", default=rule.category)
                        if not category: continue
                    else: category = cat_choice
                    
                    priority_str = qtext("Which order should this rule be checked in? (1 = checked first)", default=str(rule.priority))
                    if not priority_str: continue
                    try: priority = int(priority_str)
                    except ValueError: priority = rule.priority
                        
                    keep = qconfirm(f"Keep existing condition ({format_condition(rule.condition)})?")
                    if keep:
                        final_cond = rule.condition
                    elif keep is False:
                        conds = []
                        summaries = []
                        while True:
                            result = build_cond()
                            if result:
                                c, s = result
                                conds.append(c)
                                summaries.append(s)
                            more = qconfirm(f"Add another condition? (Currently {len(conds)})", default=False)
                            if not more: break
                        if not conds: continue
                        if len(conds) == 1:
                            final_cond = conds[0]
                            sentence = summaries[0]
                        else:
                            join = qselect("Should every condition match, or just one of them?", choices=["Every condition must match", "Just one of them must match"])
                            if join == "Every condition must match": final_cond, join_word = all_of(conds), "and"
                            elif join == "Just one of them must match": final_cond, join_word = any_of(conds), "or"
                            else: continue
                            sentence = f" {join_word} ".join(summaries)
                        console.print(f"\n[bold]This rule will match: {sentence}[/bold]")
                        if not qconfirm("Save this rule?", default=True): continue
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
                name = qtext("What should this rule be called?")
                if not name: continue
                
                cats = sorted(list(set(r.category for r in state.rules)))
                cat_choice = qselect("Category:", choices=cats + ["Create a new category"])
                if not cat_choice: continue
                if cat_choice == "Create a new category":
                    category = qtext("What should the new category be called?")
                    if not category: continue
                else: category = cat_choice
                    
                priority_str = qtext("Which order should this rule be checked in? (1 = checked first, default 100)", default="100")
                if not priority_str: continue
                try: priority = int(priority_str)
                except ValueError: priority = 100
                    
                conds = []
                summaries = []
                while True:
                    result = build_cond()
                    if result:
                        c, s = result
                        conds.append(c)
                        summaries.append(s)
                    more = qconfirm(f"Add another condition? (Currently {len(conds)})", default=False)
                    if not more: break
                if not conds: continue
                if len(conds) == 1:
                    final_cond = conds[0]
                    sentence = summaries[0]
                else:
                    join = qselect("Should every condition match, or just one of them?", choices=["Every condition must match", "Just one of them must match"])
                    if join == "Every condition must match": final_cond, join_word = all_of(conds), "and"
                    elif join == "Just one of them must match": final_cond, join_word = any_of(conds), "or"
                    else: continue
                    sentence = f" {join_word} ".join(summaries)
                console.print(f"\n[bold]This rule will match: {sentence}[/bold]")
                if not qconfirm("Save this rule?", default=True): continue

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
