from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import DataTable, Static

from sage.domain.categorization import CategorizedTransaction
from sage.domain.money import format_amount
from sage.reports.aggregate import by_month, group_by_category


class ReportView(Static):
    DEFAULT_CSS = """
    ReportView {
        width: 1fr;
        height: 1fr;
        padding: 1;
    }
    DataTable {
        height: auto;
        margin-bottom: 2;
        border: solid $accent;
    }
    """

    transactions: reactive[list[CategorizedTransaction]] = reactive([])

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield DataTable(id="category-table")
            yield DataTable(id="month-table")

    def on_mount(self) -> None:
        cat_table = self.query_one("#category-table", DataTable)
        cat_table.cursor_type = "row"
        cat_table.add_column("Category", width=30)
        cat_table.add_column("Total", width=20)

        month_table = self.query_one("#month-table", DataTable)
        month_table.cursor_type = "row"
        month_table.add_column("Month", width=15)
        month_table.add_column("Total", width=20)

        self.update_tables()

    def watch_transactions(self, new_txs: list[CategorizedTransaction]) -> None:
        self.update_tables()

    def update_tables(self) -> None:
        try:
            cat_table = self.query_one("#category-table", DataTable)
            month_table = self.query_one("#month-table", DataTable)
        except Exception:
            return

        cat_table.clear()
        month_table.clear()

        # Category
        cat_totals = group_by_category(self.transactions)
        for cat in sorted(cat_totals.keys()):
            total = cat_totals[cat]
            amt_str = format_amount(total) + " PLN"
            if total >= 0:
                amt_str = f"[bold green]{amt_str}[/bold green]"
            else:
                amt_str = f"[bold red]{amt_str}[/bold red]"
            cat_table.add_row(cat, amt_str)

        # Month
        month_totals = by_month(self.transactions)
        for (year, month) in sorted(month_totals.keys()):
            total = month_totals[(year, month)]
            amt_str = format_amount(total) + " PLN"
            if total >= 0:
                amt_str = f"[bold green]{amt_str}[/bold green]"
            else:
                amt_str = f"[bold red]{amt_str}[/bold red]"
            month_table.add_row(f"{year}-{month:02d}", amt_str)
