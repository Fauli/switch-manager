import csv
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Static, DataTable, Input
from textual.containers import Horizontal, Vertical
from textual import events

class SwitchManagerApp(App):
    CSS_PATH = "switch_manager.css"  # Ensure this file is in the same directory.
    # We keep up/down/enter as explicit bindings for DataTable navigation and command execution.
    BINDINGS = [
        ("up", "move_up", "Move Up"),
        ("down", "move_down", "Move Down"),
        ("enter", "execute_command", "Execute Command"),
    ]
    
    def __init__(self, csv_path: str, **kwargs):
        super().__init__(**kwargs)
        self.csv_path = csv_path
        self.data = []          # All rows loaded from CSV.
        self.filtered_data = [] # Currently filtered rows (for dynamic search).
        self.commands = ["ssh", "ping", "traceroute", "detail", "exit"]
        self.active_command_index = 0
    
    def compose(self) -> ComposeResult:
        yield Static("Switch Manager", id="title", classes="center")
        with Vertical(id="main_container"):
            with Horizontal(id="command_bar"):
                for i, cmd in enumerate(self.commands):
                    # Each command gets a fixed width so that all are visible.
                    css_class = "command active" if i == self.active_command_index else "command"
                    yield Static(cmd, id=f"cmd-{i}", classes=css_class)
            yield Input(placeholder="Search...", id="search_input")
            yield DataTable(id="data_table")
    
    def on_mount(self) -> None:
        self.load_csv()
        self.update_table(self.data)
        # Focus the table to allow arrow navigation.
        self.query_one(DataTable).focus()
    
    def load_csv(self):
        csv_file = Path(self.csv_path)
        if csv_file.exists():
            with csv_file.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                # Strip header whitespace so keys match expected names.
                self.data = [{k.strip(): v for k, v in row.items()} for row in reader]
        else:
            self.data = []
        self.filtered_data = self.data.copy()
    
    def update_table(self, rows):
        table = self.query_one(DataTable)
        table.clear(columns=True)
        # Use consistent header names.
        table.add_columns("Name", "IP", "subnet", "Alias", "comment")
        for row in rows:
            table.add_row(
                row.get("Name", row.get("name", "")),
                row.get("IP", row.get("ip", "")),
                row.get("subnet", row.get("Subnet", "")),
                row.get("aliases", row.get("Alias", "")),
                row.get("comment", row.get("Comment", ""))
            )
    
    # Command navigation (left/right arrow keys are handled in on_key).
    def action_prev_command(self) -> None:
        self.active_command_index = (self.active_command_index - 1) % len(self.commands)
        self.refresh_command_bar()
    
    def action_next_command(self) -> None:
        self.active_command_index = (self.active_command_index + 1) % len(self.commands)
        self.refresh_command_bar()
    
    def refresh_command_bar(self):
        for i, _ in enumerate(self.commands):
            widget = self.query_one(f"#cmd-{i}", Static)
            if i == self.active_command_index:
                widget.add_class("active")
            else:
                widget.remove_class("active")
    
    # Table navigation: use built-in DataTable actions if rows exist.
    async def action_move_up(self) -> None:
        table = self.query_one(DataTable)
        if table.row_count > 0:
            await table.action_cursor_up()
    
    async def action_move_down(self) -> None:
        table = self.query_one(DataTable)
        if table.row_count > 0:
            await table.action_cursor_down()
    
    # Execute the active command on the currently selected row.
    def action_execute_command(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row is not None and self.filtered_data:
            row_index = table.cursor_row
            if row_index < len(self.filtered_data):
                row_data = self.filtered_data[row_index]
                command = self.commands[self.active_command_index]
                if command == "exit":
                    self.exit()
                else:
                    self.log(f"Executing {command} on {row_data}")
    
    # As soon as any printable key (except arrow keys) is pressed,
    # direct it into the search input.
    async def on_key(self, event: events.Key) -> None:
        # Always handle left/right arrow keys for command switching.
        if event.key in ("left", "right"):
            if event.key == "left":
                self.action_prev_command()
            else:
                self.action_next_command()
            event.stop()
            return
        
        # For printable characters (not arrow keys), send them to the search input.
        if event.character and event.character.isprintable():
            search_input = self.query_one("#search_input", Input)
            if self.focused != search_input:
                search_input.focus()
            # Append the new character.
            search_input.value += event.character
            event.stop()

    # Dynamic search: update table as the search input changes.
    def on_input_changed(self, event: Input.Changed) -> None:
        search_text = event.value.lower()
        if search_text == "":
            self.filtered_data = self.data.copy()
        else:
            self.filtered_data = [
                row for row in self.data
                if (search_text in row.get("Name", row.get("name", "")).lower() or 
                    search_text in row.get("IP", row.get("ip", "")).lower() or 
                    search_text in row.get("subnet", row.get("Subnet", "")).lower() or 
                    search_text in row.get("aliases", row.get("Alias", "")).lower() or 
                    search_text in row.get("comment", row.get("Comment", "")).lower())
            ]
        self.update_table(self.filtered_data)

if __name__ == "__main__":
    app = SwitchManagerApp(csv_path="data.csv")
    app.run()
