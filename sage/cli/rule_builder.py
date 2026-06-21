import operator
from decimal import Decimal
from pathlib import Path

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, DataTable, Input, Label, RadioButton, RadioSet, Select, Static

from sage.cli.widgets import ModalInput
from sage.domain.conditions import Amount, And, Contains, Or
from sage.domain.rule import Rule
from sage.storage.rule_store import save_rules


class RulesChanged(Message):
    """Fired when the user saves a new rule."""
    def __init__(self, rules: list[Rule]) -> None:
        self.rules = rules
        super().__init__()


class RuleBuilder(Static):
    DEFAULT_CSS = """
    RuleBuilder {
        width: 1fr;
        height: 1fr;
        padding: 1;
    }
    #builder-layout {
        height: 1fr;
    }
    #rule-mode {
        height: auto;
        layout: horizontal;
        margin-bottom: 1;
    }
    #rule-mode RadioButton {
        margin-right: 2;
    }
    #rule-form {
        width: 100%;
        height: 1fr;
    }
    #rules-list {
        width: 100%;
        height: 1fr;
    }
    .form-group {
        height: auto;
        margin-bottom: 1;
    }
    .form-group Label {
        margin-bottom: 1;
        text-style: bold;
    }
    .form-row {
        height: auto;
        margin-bottom: 1;
    }
    .hidden {
        display: none;
    }
    .cond1-inputs, .cond2-inputs {
        width: 1fr;
    }
    .help-text {
        text-style: italic;
        color: $text-muted;
        margin-bottom: 1;
    }
    Button {
        margin-top: 1;
    }
    DataTable {
        height: 1fr;
        margin-bottom: 1;
        border: solid $accent;
    }
    #rule-status {
        margin-top: 1;
        text-style: bold;
    }
    """

    rules: reactive[list[Rule]] = reactive([])
    rules_file_path: Path | None = None

    def compose(self) -> ComposeResult:
        yield RadioSet(
            RadioButton("Add Rule", id="mode-add", value=True),
            RadioButton("Remove Rule", id="mode-remove"),
            id="rule-mode"
        )
        
        with Vertical(id="builder-layout"):
            with VerticalScroll(id="rule-form"):
                yield Label("[bold]Add New Rule[/bold]")

                with Static(classes="form-group"):
                    yield Label("Rule Name:")
                    yield ModalInput(id="rule-name", placeholder="e.g. Groceries")

                with Static(classes="form-group"):
                    yield Label("Category:")
                    yield Select([], id="rule-category-select", prompt="Select category...", allow_blank=True)
                    yield ModalInput(id="rule-category-new", placeholder="Type new category name...", classes="hidden")

                with Static(classes="form-group"):
                    yield Label("Priority (lower is higher priority):")
                    yield ModalInput(id="rule-priority", value="100")

                yield Label("[bold]Condition 1[/bold]")
                with Horizontal(classes="form-row"):
                    yield Select([
                        ("Description contains text", "contains"),
                        ("Amount", "amount"),
                    ], id="cond1-type", prompt="Condition Type", allow_blank=True)
                
                with Horizontal(classes="form-row"):
                    yield ModalInput(id="cond1-text", placeholder="Text to match...", classes="cond1-inputs hidden")
                    yield Select([
                        ("Greater than", "gt"), 
                        ("Greater than or equal", "ge"),
                        ("Less than", "lt"), 
                        ("Less than or equal", "le"),
                        ("Equal to", "eq")
                    ], id="cond1-op", prompt="Operator", allow_blank=True, classes="cond1-inputs hidden")
                    yield ModalInput(id="cond1-amount", placeholder="Amount (e.g. 50.00)", classes="cond1-inputs hidden")
                yield Label(id="cond1-help", classes="hidden help-text")

                yield Label("[bold]Condition 2 (Optional)[/bold]")
                with Horizontal(classes="form-row"):
                    yield Select([
                        ("AND", "and"),
                        ("OR", "or"),
                    ], id="join-type", prompt="Join with previous...", allow_blank=True)

                with Horizontal(classes="form-row"):
                    yield Select([
                        ("Description contains text", "contains"),
                        ("Amount", "amount"),
                    ], id="cond2-type", prompt="Condition Type", allow_blank=True)
                
                with Horizontal(classes="form-row"):
                    yield ModalInput(id="cond2-text", placeholder="Text to match...", classes="cond2-inputs hidden")
                    yield Select([
                        ("Greater than", "gt"), 
                        ("Greater than or equal", "ge"),
                        ("Less than", "lt"), 
                        ("Less than or equal", "le"),
                        ("Equal to", "eq")
                    ], id="cond2-op", prompt="Operator", allow_blank=True, classes="cond2-inputs hidden")
                    yield ModalInput(id="cond2-amount", placeholder="Amount", classes="cond2-inputs hidden")
                yield Label(id="cond2-help", classes="hidden help-text")

                yield Button("Save Rule", id="save-rule-btn", variant="primary")

            with Vertical(id="rules-list", classes="hidden"):
                yield Label("[bold]Select Rule to Remove[/bold]")
                yield Select([], id="rule-delete-select", prompt="Select a rule...", allow_blank=True)
                yield Button("Delete Selected", id="delete-rule-btn", variant="error")

            yield Label("", id="rule-status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-rule-btn":
            self.save_rule()
        elif event.button.id == "delete-rule-btn":
            self.delete_rule()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "rule-category-select":
            self.query_one("#rule-category-new").set_class(event.value != "__NEW__", "hidden")
        elif event.select.id == "cond1-type":
            is_amount = event.value == "amount"
            is_contains = event.value == "contains"
            self.query_one("#cond1-help").set_class(not is_amount, "hidden")
            self.query_one("#cond1-text").set_class(not is_contains, "hidden")
            self.query_one("#cond1-op").set_class(not is_amount, "hidden")
            self.query_one("#cond1-amount").set_class(not is_amount, "hidden")
        elif event.select.id == "cond2-type":
            is_amount = event.value == "amount"
            is_contains = event.value == "contains"
            self.query_one("#cond2-help").set_class(not is_amount, "hidden")
            self.query_one("#cond2-text").set_class(not is_contains, "hidden")
            self.query_one("#cond2-op").set_class(not is_amount, "hidden")
            self.query_one("#cond2-amount").set_class(not is_amount, "hidden")

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id == "rule-mode":
            is_add = event.pressed.id == "mode-add"
            self.query_one("#rule-form").set_class(not is_add, "hidden")
            self.query_one("#rules-list").set_class(is_add, "hidden")

    def parse_condition(self, prefix: str):
        ctype = self.query_one(f"#{prefix}-type", Select).value
        if ctype == "contains":
            text = self.query_one(f"#{prefix}-text", Input).value.strip()
            if not text:
                raise ValueError("Text to match is required.")
            return Contains(text)
        elif ctype == "amount":
            op_str = self.query_one(f"#{prefix}-op", Select).value
            if not op_str or op_str == getattr(Select, "NULL", None) or op_str == getattr(Select, "BLANK", False):
                raise ValueError("Operator is required for amount condition.")
            mapping = {"gt": operator.gt, "ge": operator.ge, "lt": operator.lt, "le": operator.le, "eq": operator.eq}
            amt_str = self.query_one(f"#{prefix}-amount", Input).value.strip()
            try:
                amt = Decimal(amt_str)
            except Exception:
                raise ValueError(f"Invalid amount: {amt_str}")
            return Amount(mapping[str(op_str)], amt)
        else:
            return None

    def save_rule(self) -> None:
        status = self.query_one("#rule-status", Label)
        
        name = self.query_one("#rule-name", Input).value.strip()
        
        cat_sel = self.query_one("#rule-category-select", Select).value
        if cat_sel == getattr(Select, "NULL", None) or cat_sel == getattr(Select, "BLANK", False) or cat_sel is None:
            status.update("[bold red]Category is required.[/bold red]")
            return
            
        if cat_sel == "__NEW__":
            cat = self.query_one("#rule-category-new", Input).value.strip()
        else:
            cat = str(cat_sel)
            
        pri_str = self.query_one("#rule-priority", Input).value.strip()

        if not name or not cat:
            status.update("[bold red]Rule Name and Category are required.[/bold red]")
            return

        try:
            priority = int(pri_str)
        except ValueError:
            priority = 1

        try:
            cond1 = self.parse_condition("cond1")
            if not cond1:
                status.update("[bold red]Condition 1 is required.[/bold red]")
                return

            join_val = self.query_one("#join-type", Select).value
            cond2 = self.parse_condition("cond2")

            if cond2 and join_val not in (getattr(Select, "NULL", None), getattr(Select, "BLANK", False), None):
                if join_val == "and":
                    final_cond = And(cond1, cond2)
                else:
                    final_cond = Or(cond1, cond2)
            else:
                final_cond = cond1

            new_rule = Rule(name=name, condition=final_cond, category=cat, priority=priority)
            
            updated_rules = list(self.rules)
            updated_rules.append(new_rule)
            updated_rules.sort(key=lambda r: r.priority)
            self.rules = updated_rules
            
            if self.rules_file_path:
                save_rules(updated_rules, self.rules_file_path)

            status.update(f"[bold green]Rule '{name}' saved successfully![/bold green]")
            
            self.query_one("#rule-name", Input).value = ""
            self.query_one("#rule-category-new", Input).value = ""
            self.query_one("#rule-category-select", Select).clear()
            
            self.query_one("#cond1-type", Select).clear()
            self.query_one("#cond1-text", Input).value = ""
            self.query_one("#cond1-op", Select).clear()
            self.query_one("#cond1-amount", Input).value = ""
            
            self.query_one("#join-type", Select).clear()
            self.query_one("#cond2-type", Select).clear()
            self.query_one("#cond2-text", Input).value = ""
            self.query_one("#cond2-op", Select).clear()
            self.query_one("#cond2-amount", Input).value = ""
            
            self.post_message(RulesChanged(updated_rules))

        except Exception as e:
            status.update(f"[bold red]Error: {e}[/bold red]")

    def on_mount(self) -> None:
        self.update_rules_dropdown()

    def watch_rules(self, new_rules: list[Rule]) -> None:
        self.update_rules_dropdown()

    def update_rules_dropdown(self) -> None:
        try:
            sel_del = self.query_one("#rule-delete-select", Select)
            sel_cat = self.query_one("#rule-category-select", Select)
        except Exception:
            return
            
        options_del = [(f"{rule.name} (Priority {rule.priority}, {rule.category})", str(idx)) for idx, rule in enumerate(self.rules)]
        sel_del.set_options(options_del)
        
        unique_cats = sorted(list({rule.category for rule in self.rules}))
        options_cat = [(c, c) for c in unique_cats]
        options_cat.append(("++ Add New Category ++", "__NEW__"))
        sel_cat.set_options(options_cat)

    def delete_rule(self) -> None:
        status = self.query_one("#rule-status", Label)
        sel = self.query_one("#rule-delete-select", Select)
        
        val = sel.value
        if val == getattr(Select, "NULL", None) or val == getattr(Select, "BLANK", False) or val is None:
            status.update("[bold red]Please select a rule to delete.[/bold red]")
            return
            
        idx = int(str(val))
        if 0 <= idx < len(self.rules):
            deleted_name = self.rules[idx].name
            updated_rules = list(self.rules)
            updated_rules.pop(idx)
            
            self.rules = updated_rules
            if self.rules_file_path:
                save_rules(updated_rules, self.rules_file_path)
                
            status.update(f"[bold green]Deleted rule '{deleted_name}'[/bold green]")
            sel.clear()
            
            self.post_message(RulesChanged(updated_rules))
