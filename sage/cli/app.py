import time
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Button, DataTable, Footer, Header, HelpPanel, Input, Label, RadioSet, RadioButton, Select, Static, TabbedContent, TabPane

from sage.cli.browse import BrowseTransactions
from sage.cli.widgets import ModalInput
from sage.cli.report_view import ReportView
from sage.cli.rule_builder import RuleBuilder, RulesChanged
from sage.domain.categorization import CategorizedTransaction
from sage.domain.rule import Rule
from sage.engine.categorizer import make_categorizer
from sage.ingest.registry import SUPPORTED_PARSER, detect_parser
from sage.storage.rule_store import load_rules


def get_available_csvs() -> list[tuple[str, str]]:
    paths = []
    # Find project root relative to this file
    root = Path(__file__).parent.parent.parent
    
    # common directories
    dirs = [Path("."), root / "data", root / "tests/fixtures"]
    for d in dirs:
        if d.exists() and d.is_dir():
            for p in d.glob("*.csv"):
                # Use absolute path for value, but short path for label
                paths.append((p.name, str(p.absolute())))
    return sorted(list(set(paths)))


class ImportView(Static):
    DEFAULT_CSS = """
    ImportView {
        padding: 1;
    }
    .import-container {
        border: solid $accent;
        padding: 1 2;
        margin: 1;
    }
    RadioSet {
        margin-bottom: 1;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(classes="import-container"):
            yield Label("[bold]Select CSV File to Import[/bold]", id="import-label")
            options = get_available_csvs()
            with RadioSet(id="csv-select"):
                for idx, (label, value) in enumerate(options):
                    yield RadioButton(label, id=f"csv-radio-{idx}")
            yield Label("[bold]Select Bank[/bold]")
            yield Select(
                [(name, name) for name in SUPPORTED_PARSER],
                id="bank-select",
                prompt="Select bank...",
                allow_blank=True,
            )
            yield Button("Import", id="import-btn", variant="primary")
            yield Label("", id="import-status")


class SageApp(App):
    CSS = """
    TabPane {
        padding: 1;
    }
    .in-section {
        background: $success 25%;
    }
    """
    TAB_IDS = ["tab-import", "tab-browse", "tab-reports", "tab-builder"]
    SECTION_WIDGETS = (RadioSet, DataTable, Input)
    nav_mode: reactive[bool] = reactive(True)
    BINDINGS = [
        Binding("1", "switch_tab('tab-import')", "Tabs", key_display="1-4", priority=True),
        Binding("2", "switch_tab('tab-browse')", show=False, priority=True),
        Binding("3", "switch_tab('tab-reports')", show=False, priority=True),
        Binding("4", "switch_tab('tab-builder')", show=False, priority=True),
        Binding("down", "focus_next", "Move", key_display="↑↓", priority=True),
        Binding("up", "focus_previous", show=False, priority=True),
        Binding("enter", "enter_section", "Edit/Open", priority=True),
        Binding("escape", "leave_section", "Back", priority=True),
        Binding("f1", "toggle_help", "Help"),
        Binding("q", "quit", "Quit", priority=True),
    ]

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        focused = self.focused
        in_overlay = focused is not None and type(focused).__name__ == "SelectOverlay"
        editing = (not self.nav_mode) and isinstance(focused, Input)
        if action in ("switch_tab", "quit"):
            return not editing
        if action in ("focus_next", "focus_previous"):
            return self.nav_mode and not in_overlay
        if action == "enter_section":
            return (
                self.nav_mode
                and not in_overlay
                and isinstance(focused, self.SECTION_WIDGETS)
            )
        if action == "leave_section":
            return not in_overlay and (bool(self.query(HelpPanel)) or not self.nav_mode)
        return True

    def action_enter_section(self) -> None:
        self.nav_mode = False
        if isinstance(self.focused, ModalInput):
            self.focused.locked = False

    def action_leave_section(self) -> None:
        if self.query(HelpPanel):
            self.action_hide_help_panel()
            return
        if isinstance(self.focused, ModalInput):
            self.focused.locked = True
        self.nav_mode = True

    def action_toggle_help(self) -> None:
        if self.query(HelpPanel):
            self.action_hide_help_panel()
        else:
            self.action_show_help_panel()

    def action_switch_tab(self, tab_id: str) -> None:
        if isinstance(self.focused, ModalInput):
            self.focused.locked = True
        self.nav_mode = True
        self.set_focus(None)
        tabs = self.query_one(TabbedContent)
        tabs.active = tab_id
        pane = self.query_one(f"#{tab_id}", TabPane)
        for widget in pane.query("*"):
            if isinstance(widget, (RadioSet, Select, Button, DataTable)) and widget.focusable:
                self.set_focus(widget)
                break

    def watch_nav_mode(self, nav: bool) -> None:
        self.refresh_bindings()
        focused = self.focused
        if focused is not None:
            focused.set_class(not nav, "in-section")

    rules: reactive[list[Rule]] = reactive([])
    transactions: reactive[list[CategorizedTransaction]] = reactive([])
    rules_path = Path("data/rules.json")

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="tabs"):
            with TabPane("Import", id="tab-import"):
                yield ImportView()
            with TabPane("Browse", id="tab-browse"):
                yield BrowseTransactions(id="view-browse")
            with TabPane("Reports", id="tab-reports"):
                yield ReportView(id="view-reports")
            with TabPane("Rule Builder", id="tab-builder"):
                yield RuleBuilder(id="view-builder")
        yield Footer()

    def on_mount(self) -> None:
        self.rules = load_rules(self.rules_path)
        builder = self.query_one("#view-builder", RuleBuilder)
        builder.rules = self.rules
        builder.rules_file_path = self.rules_path

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "import-btn":
            self.do_import()

    def do_import(self) -> None:
        status = self.query_one("#import-status", Label)
        radioset = self.query_one("#csv-select", RadioSet)
        
        pressed = radioset.pressed_button
        if not pressed:
            status.update("[bold red]Please select a file.[/bold red]")
            return
            
        selected_label = str(pressed.label)
        csv_path_str = None
        for label, path in get_available_csvs():
            if label == selected_label:
                csv_path_str = path
                break
                
        if not csv_path_str:
            status.update("[bold red]Could not find the selected file path.[/bold red]")
            return
            
        csv_path = Path(csv_path_str)
        if not csv_path.exists():
            status.update(f"[bold red]File not found: {csv_path}[/bold red]")
            return

        bank = self.query_one("#bank-select", Select).value
        if bank == Select.NULL:
            status.update("[bold red]Please select a bank.[/bold red]")
            return

        try:
            start = time.perf_counter()
            parser = detect_parser(str(bank))
            txs = list(parser.parse(csv_path))
            categorize = make_categorizer(self.rules)
            self.transactions = [CategorizedTransaction(tx, categorize(tx)) for tx in txs]
            duration = time.perf_counter() - start
            
            # Update views
            self.query_one("#view-browse", BrowseTransactions).transactions = self.transactions
            self.query_one("#view-reports", ReportView).transactions = self.transactions
            
            status.update(f"[bold green]Loaded {len(txs)} transactions in {duration:.3f}s[/bold green]")
            
            # Switch to browse tab
            # We defer this slightly to avoid the freeze issue with Select widgets that was observed before
            def switch_tab():
                self.query_one(TabbedContent).active = "tab-browse"
            self.set_timer(0.1, switch_tab)
            
        except Exception as e:
            status.update(f"[bold red]Error parsing CSV: {e}[/bold red]")

    def on_rules_changed(self, event: RulesChanged) -> None:
        """Handle event when rule is added in RuleBuilder."""
        self.rules = event.rules
        self.re_categorize()

    def re_categorize(self) -> None:
        if not self.transactions:
            return
            
        categorize = make_categorizer(self.rules)
        updated = []
        for ct in self.transactions:
            result = categorize(ct.tx)
            updated.append(CategorizedTransaction(ct.tx, result))
            
        self.transactions = updated
        
        # Manually update the views
        self.query_one("#view-browse", BrowseTransactions).transactions = self.transactions
        self.query_one("#view-reports", ReportView).transactions = self.transactions


def main() -> None:
    app = SageApp()
    app.run(mouse=False)
