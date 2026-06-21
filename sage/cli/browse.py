from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import DataTable, Input, Label, Static, Select

from sage.domain.categorization import CategorizedTransaction
from sage.domain.money import format_amount


class BrowseTransactions(Static):
    DEFAULT_CSS = """
    BrowseTransactions {
        width: 1fr;
        height: 1fr;
        padding: 1;
    }
    .search-bar {
        height: auto;
        margin-bottom: 1;
    }
    .search-bar Label {
        margin-top: 1;
        margin-right: 1;
        text-style: bold;
    }
    .search-bar Input {
        width: 40;
    }
    DataTable {
        height: 1fr;
        border: solid $accent;
    }
    """

    transactions: reactive[list[CategorizedTransaction]] = reactive([])
    search_query: reactive[str] = reactive("")
    rule_filter_val: reactive[str | None] = reactive(None)

    def compose(self) -> ComposeResult:
        with Horizontal(classes="search-bar"):
            yield Label("Search:")
            yield Input(placeholder="Filter by description or category...", id="search-input")
            yield Label("Rule:")
            yield Select([], id="rule-filter", prompt="No rules", allow_blank=True)
        yield DataTable(id="tx-table")

    def on_mount(self) -> None:
        table = self.query_one("#tx-table", DataTable)
        table.cursor_type = "row"
        table.add_column("Date", width=12)
        table.add_column("Description", width=40)
        table.add_column("Amount", width=15)
        table.add_column("Category", width=20)
        table.add_column("Rule", width=25)
        self.update_table()

    def watch_transactions(self, new_txs: list[CategorizedTransaction]) -> None:
        rule_filter = self.query_one("#rule-filter", Select)
        unique_rules = set()
        for tx in new_txs:
            if tx.result.rule_name:
                unique_rules.add(tx.result.rule_name)
        
        options = [(r, r) for r in sorted(list(unique_rules))]
        rule_filter.set_options(options)
        self.update_table()

    def watch_search_query(self, new_query: str) -> None:
        self.update_table()
        
    def watch_rule_filter_val(self, new_val: str | None) -> None:
        self.update_table()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            self.search_query = event.value

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "rule-filter":
            if event.value == getattr(Select, "NULL", None) or event.value == getattr(Select, "BLANK", False) or event.value is None or str(event.value) == "None":
                self.rule_filter_val = None
            else:
                self.rule_filter_val = str(event.value)

    def update_table(self) -> None:
        try:
            table = self.query_one("#tx-table", DataTable)
        except Exception:
            return

        table.clear()
        query = self.search_query.lower().strip()
        for idx, row in enumerate(self.transactions):
            desc = row.tx.description
            cat = row.result.category
            rule_name = row.result.rule_name or "-"

            if self.rule_filter_val and rule_name != self.rule_filter_val:
                continue

            if query and query not in desc.lower() and query not in cat.lower():
                continue

            amount_str = format_amount(row.tx.amount) + " PLN"
            if row.tx.amount >= 0:
                amount_formatted = f"[bold green]{amount_str}[/bold green]"
            else:
                amount_formatted = f"[bold red]{amount_str}[/bold red]"

            table.add_row(
                str(row.tx.date),
                desc,
                amount_formatted,
                cat,
                rule_name,
                key=str(idx)
            )
