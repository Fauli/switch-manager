import asyncio
import csv
import os
import subprocess
import logging
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Static, DataTable, Input
from textual.containers import Horizontal, Vertical
from textual import events
from textual.timer import Timer
from textual.screen import Screen
from textual.scroll_view import ScrollView

logging.basicConfig(filename="textual.log", level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

class StreamingOutputScreen(Screen):
    """A modal screen that streams command output as it is produced."""
    def __init__(self, cmd: list, **kwargs):
        self.cmd = cmd
        self.output = ""
        super().__init__(**kwargs)
    
    def compose(self) -> ComposeResult:
        yield Static("Press ESC to close", id="modal_header")
        yield ScrollView(Static("", id="output_text"), id="modal_body")
    
    async def on_mount(self) -> None:
        asyncio.create_task(self.stream_output())
    
    async def stream_output(self) -> None:
        proc = await asyncio.create_subprocess_exec(
            *self.cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        output_widget = self.query_one("#output_text", Static)
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            decoded = line.decode()
            self.output += decoded
            output_widget.update(self.output)
        await proc.wait()
    
    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            await self.app.pop_screen()
            event.stop()
    
    async def on_unmount(self) -> None:
        # Wait a bit and restore focus to the main DataTable.
        await asyncio.sleep(0.3)
        try:
            self.app.set_focus(self.app.query_one(DataTable))
        except Exception as e:
            self.app.log(f"Focus restoration error (streaming): {e}")

class OutputScreen(Screen):
    """A modal screen to display immediate output (or details)."""
    def __init__(self, output_text: str, **kwargs):
        self.output_text = output_text
        super().__init__(**kwargs)
    
    def compose(self) -> ComposeResult:
        yield Static("Press ESC to close", id="modal_header")
        yield ScrollView(Static(self.output_text, id="output_text"), id="modal_body")
    
    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            await self.app.pop_screen()
            event.stop()
    
    async def on_unmount(self) -> None:
        # Wait a bit and restore focus to the main DataTable.
        await asyncio.sleep(0.3)
        try:
            self.app.set_focus(self.app.query_one(DataTable))
        except Exception as e:
            self.app.log(f"Focus restoration error (output): {e}")

class SwitchManagerApp(App):
    CSS_PATH = "switch_manager.css"
    BINDINGS = [
        ("up", "move_up", "Move Up"),
        ("down", "move_down", "Move Down"),
    ]
    
    def __init__(self, csv_path: str, **kwargs):
        super().__init__(**kwargs)
        self.csv_path = csv_path
        self.data = []          # All rows loaded from CSV.
        self.filtered_data = [] # Filtered rows.
        self.commands = ["ssh", "ping", "traceroute", "detail", "exit"]
        self.active_command_index = 0
        self.status_timer: Timer | None = None
    
    def compose(self) -> ComposeResult:
        yield Static("Switch Manager", id="title", classes="center")
        with Vertical(id="main_container"):
            with Horizontal(id="command_bar"):
                for i, cmd in enumerate(self.commands):
                    css_class = "command active" if i == self.active_command_index else "command"
                    yield Static(cmd, id=f"cmd-{i}", classes=css_class)
            yield Input(placeholder="Search...", id="search_input")
            with Vertical(id="table_container"):
                yield DataTable(id="data_table")
            yield Static("", id="status", classes="status")
    
    def on_mount(self) -> None:
        self.load_csv()
        self.update_table(self.data)
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.focus()
    
    def load_csv(self) -> None:
        csv_file = Path(self.csv_path)
        if csv_file.exists():
            with csv_file.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                self.data = [{k.strip(): v for k, v in row.items()} for row in reader]
        else:
            self.data = []
        self.filtered_data = self.data.copy()
    
    def update_table(self, rows) -> None:
        table = self.query_one(DataTable)
        table.clear(columns=True)
        table.add_columns("Name", "IP", "subnet", "Alias", "comment")
        for row in rows:
            table.add_row(
                row.get("Name", row.get("name", "")),
                row.get("IP", row.get("ip", "")),
                row.get("subnet", row.get("Subnet", "")),
                row.get("aliases", row.get("Alias", "")),
                row.get("comment", row.get("Comment", ""))
            )
    
    def action_prev_command(self) -> None:
        self.active_command_index = (self.active_command_index - 1) % len(self.commands)
        self.refresh_command_bar()
    
    def action_next_command(self) -> None:
        self.active_command_index = (self.active_command_index + 1) % len(self.commands)
        self.refresh_command_bar()
    
    def refresh_command_bar(self) -> None:
        for i, _ in enumerate(self.commands):
            widget = self.query_one(f"#cmd-{i}", Static)
            if i == self.active_command_index:
                widget.add_class("active")
            else:
                widget.remove_class("active")
    
    def action_move_up(self) -> None:
        table = self.query_one(DataTable)
        if table.row_count > 0:
            table.action_cursor_up()
    
    def action_move_down(self) -> None:
        table = self.query_one(DataTable)
        if table.row_count > 0:
            table.action_cursor_down()
    
    async def action_execute_command(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row is None or not self.filtered_data:
            return
        row_index = table.cursor_row
        if row_index >= len(self.filtered_data):
            return
        row_data = self.filtered_data[row_index]
        ip = row_data.get("IP", "").strip()
        command = self.commands[self.active_command_index]
        
        if command == "exit":
            self.exit()
        elif command == "ssh":
            self.exit()
            os.system("clear")  # Clear the terminal screen
            os.system(f"ssh {ip}")
           # self.exit()  # exit the TUI first
           # import pty
           # pty.spawn(["ssh", ip])
        elif command == "ping":
            await self.push_screen(StreamingOutputScreen(["ping", "-c", "4", ip]))
        elif command == "traceroute":
            await self.push_screen(StreamingOutputScreen(["traceroute", ip]))
        elif command == "detail":
            details = "\n".join([f"{k}: {v}" for k, v in row_data.items()])
            await self.push_screen(OutputScreen(details))
    
    def clear_status(self) -> None:
        status_widget = self.query_one("#status", Static)
        status_widget.update("")
    
    async def on_key(self, event: events.Key) -> None:
        if event.key in ("left", "right"):
            if event.key == "left":
                self.action_prev_command()
            else:
                self.action_next_command()
            event.stop()
            return
        
        if event.key == "enter":
            await self.action_execute_command()
            try:
                self.query_one(DataTable).focus()
            except Exception:
                pass
            event.stop()
            return
        
        if event.character and event.character.isprintable():
            search_input = self.query_one("#search_input", Input)
            if not search_input.has_focus:
                search_input.focus()
    
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

    async def pop_screen(self) -> None:
        await super().pop_screen()
        # Immediately restore focus to the DataTable after a modal is popped.
        try:
            self.set_focus(self.query_one(DataTable))
        except Exception as e:
            self.log(f"Error restoring focus: {e}")

if __name__ == "__main__":
    app = SwitchManagerApp(csv_path="data.csv")
    app.run()
