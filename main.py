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
from textual.css.query import NoMatches
import pty  # Make sure this import is present for SSH modal

# Check for SM_DEBUG environment variable (set to true to enable debug logging).
SM_DEBUG = os.getenv("SM_DEBUG", "false").lower() == "true"
log_filename = "switch-manager.log" if SM_DEBUG else "textual.log"
log_level = logging.DEBUG if SM_DEBUG else logging.INFO

logging.basicConfig(
    filename=log_filename,
    level=log_level,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# --- StreamingOutputScreen with container styling ---

class StreamingOutputScreen(Screen):
    """A modal screen that streams command output as it is produced."""
    def __init__(self, cmd: list, **kwargs):
        logging.debug(f"Initializing StreamingOutputScreen with command: {cmd}")
        self.cmd = cmd
        self.output = ""
        self._stream_task = None
        self._closed = False  # Flag to signal that the modal should close
        super().__init__(**kwargs)
    
    def compose(self) -> ComposeResult:
        logging.debug("Composing StreamingOutputScreen widgets")
        with Vertical(classes="modal-container"):
            yield Static("Press ESC to close", id="modal_header", classes="modal-header")
            yield ScrollView(Static("", id="output_text", classes="modal-text"),
                             id="modal_body", classes="modal-body")
    
    async def on_mount(self) -> None:
        logging.debug("StreamingOutputScreen mounted, starting stream_output")
        self._stream_task = asyncio.create_task(self.stream_output())
    
    async def stream_output(self) -> None:
        logging.debug(f"Starting subprocess for command: {self.cmd}")
        proc = await asyncio.create_subprocess_exec(
            *self.cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        try:
            output_widget = self.query("Static#output_text").first()
        except Exception:
            output_widget = None
            logging.debug("No output_text widget found in StreamingOutputScreen")
        try:
            while True:
                if self._closed:
                    logging.debug("stream_output detected close flag; breaking out of loop")
                    break
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode()
                logging.debug(f"StreamingOutputScreen output line: {decoded.strip()}")
                self.output += decoded
                if output_widget:
                    output_widget.update(self.output)
        except asyncio.CancelledError:
            logging.debug("stream_output task was cancelled")
            proc.kill()
            raise
        await proc.wait()
        logging.debug("Subprocess finished in StreamingOutputScreen")
    
    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            logging.debug("StreamingOutputScreen received ESC key, setting close flag")
            self._closed = True
            self.app.call_later(self.app.pop_screen)
            event.stop()
    
    async def on_unmount(self) -> None:
        logging.debug("StreamingOutputScreen unmounting, cancelling stream task if still running")
        if self._stream_task and not self._stream_task.done():
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                logging.debug("Stream task cancelled in on_unmount")
        await asyncio.sleep(0.3)
        try:
            data_table = self.app.query(DataTable).first()
        except Exception:
            data_table = None
        if data_table:
            self.app.set_focus(data_table)
            logging.debug("Focus successfully restored to DataTable in StreamingOutputScreen")
        else:
            logging.debug("No DataTable found in StreamingOutputScreen on_unmount")

# --- OutputScreen with container styling ---

class OutputScreen(Screen):
    """A modal screen to display immediate output (or details)."""
    def __init__(self, output_text: str, **kwargs):
        logging.debug(f"Initializing OutputScreen with output length: {len(output_text)}")
        self.output_text = output_text
        super().__init__(**kwargs)
    
    def compose(self) -> ComposeResult:
        logging.debug("Composing OutputScreen widgets")
        with Vertical(classes="modal-container"):
            yield Static("Press ESC to close", id="modal_header", classes="modal-header")
            yield ScrollView(
                Static(self.output_text, id="output_text", classes="modal-text"),
                id="modal_body", classes="modal-body"
            )
    
    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            logging.debug("OutputScreen received ESC key, scheduling pop_screen")
            self.app.call_later(self.app.pop_screen)
            event.stop()
    
    async def on_unmount(self) -> None:
        logging.debug("OutputScreen unmounting, restoring focus to DataTable")
        await asyncio.sleep(0.3)
        try:
            data_table = self.app.query(DataTable).first()
        except Exception:
            data_table = None
        if data_table:
            self.app.set_focus(data_table)
            logging.debug("Focus successfully restored to DataTable in OutputScreen")
        else:
            logging.debug("No DataTable found in OutputScreen on_unmount")

# --- New SshScreen with container styling ---

class SshScreen(Screen):
    """A modal screen that acts as an interactive SSH window."""
    def __init__(self, ip: str, **kwargs):
        logging.debug(f"Initializing SshScreen for SSH to {ip}")
        self.ip = ip
        self.master_fd = None
        self.slave_fd = None
        self.ssh_proc = None
        self._read_task = None
        super().__init__(**kwargs)
    
    def compose(self) -> ComposeResult:
        logging.debug("Composing SshScreen widgets")
        with Vertical(classes="modal-container"):
            yield Static(f"SSH session to {self.ip} - Press ESC to close", id="modal_header", classes="modal-header")
            yield ScrollView(Static("", id="ssh_output", classes="modal-text"), 
                             id="modal_body", classes="modal-body")
            yield Input(placeholder="Type command...", id="ssh_input")
    
    async def on_mount(self) -> None:
        logging.debug("SshScreen mounted, opening PTY and starting SSH process")
        self.master_fd, self.slave_fd = pty.openpty()
        self.ssh_proc = await asyncio.create_subprocess_exec(
            "ssh", self.ip,
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            close_fds=True
        )
        self._read_task = asyncio.create_task(self.read_pty_output())
    
    async def read_pty_output(self) -> None:
        logging.debug("SshScreen starting to read PTY output")
        master_file = os.fdopen(self.master_fd, "rb", buffering=0)
        try:
            output_widget = self.query("Static#ssh_output").first()
        except Exception:
            output_widget = None
            logging.debug("No ssh_output widget found in SshScreen")
        while True:
            try:
                data = await asyncio.to_thread(master_file.read, 1024)
            except Exception as e:
                logging.debug(f"Error reading from PTY: {e}")
                break
            if not data:
                break
            text = data.decode(errors="ignore")
            if output_widget:
                # Append new text to the existing output.
                current = output_widget.renderable if output_widget.renderable is not None else ""
                output_widget.update(current + text)
        logging.debug("SSH process output reading finished")
        self.app.call_later(self.app.pop_screen)
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.master_fd is not None:
            command = event.value + "\n"
            os.write(self.master_fd, command.encode())
            try:
                input_widget = self.query("Input#ssh_input").first()
                input_widget.value = ""
            except Exception:
                pass
    
    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            logging.debug("SshScreen received ESC key, terminating SSH session")
            if self.ssh_proc:
                self.ssh_proc.kill()
            self.app.call_later(self.app.pop_screen)
            event.stop()
    
    async def on_unmount(self) -> None:
        logging.debug("SshScreen unmounting, cleaning up PTY and tasks")
        if self._read_task and not self._read_task.done():
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                logging.debug("PTY read task cancelled in SshScreen on_unmount")
        if self.slave_fd:
            os.close(self.slave_fd)
        if self.master_fd:
            os.close(self.master_fd)
        await asyncio.sleep(0.3)
        try:
            data_table = self.app.query(DataTable).first()
        except Exception:
            data_table = None
        if data_table:
            self.app.set_focus(data_table)
            logging.debug("Focus restored to DataTable in SshScreen")
        else:
            logging.debug("No DataTable found in SshScreen on_unmount")


# --- SwitchManagerApp remains largely the same ---

class SwitchManagerApp(App):
    CSS_PATH = "switch_manager.css"
    BINDINGS = [
        ("up", "move_up", "Move Up"),
        ("down", "move_down", "Move Down"),
    ]
    
    def __init__(self, csv_path: str, **kwargs):
        logging.debug(f"Initializing SwitchManagerApp with CSV path: {csv_path}")
        super().__init__(**kwargs)
        self.csv_path = csv_path
        self.data = []          # All rows loaded from CSV.
        self.filtered_data = [] # Filtered rows.
        self.commands = ["ssh", "ping", "traceroute", "details", "exit"]
        self.active_command_index = 0
        self.status_timer: Timer | None = None
    
    def compose(self) -> ComposeResult:
        logging.debug("Composing main SwitchManagerApp widgets")
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
        logging.debug("SwitchManagerApp mounting: loading CSV and updating table")
        self.load_csv()
        self.update_table(self.data)
        try:
            table = self.query(DataTable).first()
        except NoMatches:
            table = None
        if table:
            table.cursor_type = "row"
            table.focus()
            logging.debug("DataTable focused in SwitchManagerApp on_mount")
        else:
            logging.debug("No DataTable found in on_mount")
    
    def load_csv(self) -> None:
        logging.debug("Loading CSV data")
        csv_file = Path(self.csv_path)
        if csv_file.exists():
            with csv_file.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                self.data = [{k.strip(): v for k, v in row.items()} for row in reader]
            logging.debug(f"CSV loaded with {len(self.data)} rows")
        else:
            logging.debug("CSV file does not exist; no data loaded")
            self.data = []
        self.filtered_data = self.data.copy()
    
    def update_table(self, rows) -> None:
        logging.debug(f"Updating table with {len(rows)} rows")
        try:
            table = self.query(DataTable).first()
        except NoMatches:
            table = None
        if not table:
            logging.debug("No DataTable found when updating table")
            return
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
        logging.debug("SwitchManagerApp: Moving to previous command")
        self.active_command_index = (self.active_command_index - 1) % len(self.commands)
        self.refresh_command_bar()
    
    def action_next_command(self) -> None:
        logging.debug("SwitchManagerApp: Moving to next command")
        self.active_command_index = (self.active_command_index + 1) % len(self.commands)
        self.refresh_command_bar()
    
    def refresh_command_bar(self) -> None:
        logging.debug(f"Refreshing command bar, active_command_index: {self.active_command_index}")
        for i, _ in enumerate(self.commands):
            try:
                widget = self.query(f"#cmd-{i}").first()
            except NoMatches:
                widget = None
            if widget:
                if i == self.active_command_index:
                    widget.add_class("active")
                else:
                    widget.remove_class("active")
    
    def action_move_up(self) -> None:
        try:
            table = self.query(DataTable).first()
        except NoMatches:
            table = None
        if table and table.row_count > 0:
            logging.debug("SwitchManagerApp: Moving cursor up in DataTable")
            table.action_cursor_up()
    
    def action_move_down(self) -> None:
        try:
            table = self.query(DataTable).first()
        except NoMatches:
            table = None
        if table and table.row_count > 0:
            logging.debug("SwitchManagerApp: Moving cursor down in DataTable")
            table.action_cursor_down()
    
    async def action_execute_command(self) -> None:
        try:
            table = self.query(DataTable).first()
        except NoMatches:
            table = None
        if table is None or table.cursor_row is None or not self.filtered_data:
            logging.debug("No row selected or filtered data is empty; aborting command execution")
            return
        row_index = table.cursor_row
        if row_index >= len(self.filtered_data):
            logging.debug("Cursor row index out of range; aborting command execution")
            return
        row_data = self.filtered_data[row_index]
        ip = row_data.get("IP", "").strip()
        command = self.commands[self.active_command_index]
        logging.debug(f"Executing command '{command}' on IP: {ip} (row index {row_index})")
        
        if command == "exit":
            logging.debug("Exit command received; exiting application")
            self.exit()
        elif command == "ssh":
            logging.debug(f"SSH command received; pushing SshScreen for {ip}")
            await self.push_screen(SshScreen(ip))
        elif command == "ping":
            logging.debug(f"Ping command received; pushing StreamingOutputScreen for {ip}")
            await self.push_screen(StreamingOutputScreen(["ping", "-c", "4", ip]))
        elif command == "traceroute":
            logging.debug(f"Traceroute command received; pushing StreamingOutputScreen for {ip}")
            await self.push_screen(StreamingOutputScreen(["traceroute", ip]))
        elif command == "details":
            details = "\n".join([f"{k}: {v}" for k, v in row_data.items()])
            logging.debug("Details command received; pushing OutputScreen")
            await self.push_screen(OutputScreen(details))
    
    def clear_status(self) -> None:
        logging.debug("Clearing status message")
        try:
            status_widget = self.query("#status").first()
        except NoMatches:
            status_widget = None
        if status_widget:
            status_widget.update("")
    
    async def on_key(self, event: events.Key) -> None:
        logging.debug(f"SwitchManagerApp received key event: {event.key}")
        if event.key in ("left", "right"):
            if event.key == "left":
                logging.debug("Processing left key: switching to previous command")
                self.action_prev_command()
            else:
                logging.debug("Processing right key: switching to next command")
                self.action_next_command()
            event.stop()
            return
        
        if event.key == "enter":
            logging.debug("Processing enter key: executing command")
            await self.action_execute_command()
            try:
                table = self.query(DataTable).first()
            except NoMatches:
                table = None
            if table:
                table.focus()
                logging.debug("DataTable focused after command execution")
            else:
                logging.debug("No DataTable found to set focus after command execution")
            event.stop()
            return
        
        if event.character and event.character.isprintable():
            try:
                search_input = self.query("#search_input").first()
            except NoMatches:
                search_input = None
            if search_input and not search_input.has_focus:
                logging.debug("Transferring focus to search_input due to printable key press")
                search_input.focus()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        logging.debug(f"Search input changed: {event.value}")
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
        logging.debug(f"{len(self.filtered_data)} rows match search text")
        self.update_table(self.filtered_data)

    async def pop_screen(self) -> None:
        logging.debug("SwitchManagerApp popping screen (modal closed)")
        await super().pop_screen()
        try:
            table = self.query(DataTable).first()
        except NoMatches:
            table = None
        if table:
            self.set_focus(table)
            logging.debug("Focus restored to DataTable after popping modal")
        else:
            logging.debug("No DataTable found after popping modal")

if __name__ == "__main__":
    logging.debug("Starting SwitchManagerApp")
    app = SwitchManagerApp(csv_path="data.csv")
    app.run()