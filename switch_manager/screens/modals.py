"""Modal dialog screens for the application."""

import asyncio
from textual import events
from textual.screen import ModalScreen
from textual.widgets import Static, RichLog
from textual.containers import Container, Vertical
from textual.app import ComposeResult


class BaseModal(ModalScreen):
    """Base modal screen with common styling and behavior."""

    DEFAULT_CSS = """
    BaseModal {
        align: center middle;
    }

    BaseModal > Container {
        width: 80;
        height: auto;
        max-height: 80%;
        border: thick $background 80%;
        background: $surface;
    }

    .modal-title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        background: $primary;
        color: $text;
        padding: 1;
    }

    .modal-content {
        width: 100%;
        height: auto;
        padding: 1 2;
        overflow-y: auto;
    }

    .modal-footer {
        width: 100%;
        content-align: center middle;
        background: $panel;
        padding: 1;
        text-style: italic;
    }
    """

    def on_key(self, event: events.Key) -> None:
        """Handle key events - ESC closes modal.

        Args:
            event: Key event
        """
        if event.key == "escape":
            self.dismiss()
            event.stop()


class OutputModal(BaseModal):
    """Modal for displaying static output/text."""

    def __init__(self, title: str, content: str) -> None:
        """Initialize the output modal.

        Args:
            title: Modal title
            content: Content to display
        """
        super().__init__()
        self.title_text = title
        self.content_text = content

    def compose(self) -> ComposeResult:
        """Compose the modal."""
        with Container():
            yield Static(self.title_text, classes="modal-title")
            yield Static(self.content_text, classes="modal-content")
            yield Static("Press ESC to close", classes="modal-footer")


class ConfirmationModal(BaseModal):
    """Modal for yes/no confirmation dialogs."""

    DEFAULT_CSS = BaseModal.DEFAULT_CSS + """
    .modal-message {
        width: 100%;
        padding: 2;
        content-align: center middle;
    }

    .modal-options {
        width: 100%;
        padding: 2;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    .modal-instructions {
        width: 100%;
        padding: 1;
        content-align: center middle;
        background: $panel;
        text-style: italic;
    }
    """

    def __init__(self, title: str, message: str, warning: str = "") -> None:
        """Initialize the confirmation modal.

        Args:
            title: Modal title
            message: Confirmation message
            warning: Optional warning message
        """
        super().__init__()
        self.title_text = title
        self.message_text = message
        self.warning_text = warning

    def compose(self) -> ComposeResult:
        """Compose the modal."""
        with Container():
            yield Static(self.title_text, classes="modal-title")

            # Message
            yield Static(self.message_text, classes="modal-message")

            # Warning (if provided)
            if self.warning_text:
                yield Static(
                    f"⚠  {self.warning_text}",
                    classes="modal-message"
                )

            # Options
            yield Static(
                "Press:  Y = Yes  |  N = No  |  ESC = Cancel",
                classes="modal-options"
            )

            # Instructions
            yield Static(
                "Keyboard input required - use Y, N, or ESC keys",
                classes="modal-instructions"
            )

    def on_key(self, event: events.Key) -> None:
        """Handle key events - y/n/ESC.

        Args:
            event: Key event
        """
        if event.key in ("y", "Y"):
            self.dismiss(True)
            event.stop()
        elif event.key in ("n", "N", "escape"):
            self.dismiss(False)
            event.stop()


class DetailsModal(OutputModal):
    """Modal for displaying switch details."""

    def __init__(self, switch) -> None:
        """Initialize the details modal.

        Args:
            switch: Switch object to display
        """
        title = "Switch Details"
        content = (
            f"Name:    {switch.name}\n"
            f"IP:      {switch.ip}\n"
            f"Subnet:  {switch.subnet}\n"
            f"Aliases: {switch.aliases}\n"
            f"Comment: {switch.comment}"
        )
        super().__init__(title, content)


class HelpModal(OutputModal):
    """Modal for displaying help information."""

    def __init__(self) -> None:
        """Initialize the help modal."""
        title = "V-Li Switch Manager - Help"
        content = """
╔══════════════════════════════════════════════════════════╗
║         V-Li: Switch Manager                             ║
║         Master Your Network Magic!                       ║
╚══════════════════════════════════════════════════════════╝

NAVIGATION
  ↑/↓     - Move selection up/down (wraps around)
  ←/→     - Switch between commands

SEARCH
  Type    - Auto-focus search and filter switches
  Ctrl+L  - Toggle OR/AND search mode
  Ctrl+H  - Show search history (Coming soon!)
  ESC     - Clear search / Exit app
  Enter   - Return focus to table

SORTING
  F1      - Sort by Name
  F2      - Sort by IP
  F3      - Sort by subnet
  F4      - Sort by Alias
  F5      - Sort by comment
  (Press twice to toggle ascending/descending)

COMMANDS
  1       - SSH to selected switch
  2       - Ping selected switch
  3       - Traceroute to selected switch
  4       - Batch ping all filtered switches
  5       - Open TMUX synchronized session
  6       - Show switch details
  7       - Show this help
  8       - Exit application

  Enter   - Execute selected command
  ?       - Quick help shortcut

SEARCH MODES
  OR Mode  - Find switches matching ANY search term
  AND Mode - Find switches matching ALL search terms

TIPS
  • Type to search instantly - no need to click!
  • Combine search + sort for powerful filtering
  • Use batch operations on filtered results
  • TMUX mode syncs commands across all switches

Press ESC to close this help.
"""
        super().__init__(title, content)


class BatchPingModal(BaseModal):
    """Modal for displaying batch ping results from multiple switches."""

    DEFAULT_CSS = BaseModal.DEFAULT_CSS + """
    .batch-output {
        width: 100%;
        height: 35;
        padding: 1;
        overflow-y: auto;
        background: $surface;
        color: $text;
        border: solid $primary;
    }

    .batch-status {
        width: 100%;
        padding: 1;
        content-align: center middle;
        background: $panel;
        text-style: italic;
    }
    """

    def __init__(self, switches: list) -> None:
        """Initialize the batch ping modal.

        Args:
            switches: List of Switch objects to ping
        """
        super().__init__()
        self.switches = switches
        self.results = []
        self.completed = 0
        self.total = len(switches)

    def compose(self) -> ComposeResult:
        """Compose the modal."""
        with Container():
            yield Static(f"Batch Ping Results ({self.total} switches)", classes="modal-title")
            yield RichLog(id="batch-output", classes="batch-output", wrap=True, highlight=False, markup=True)
            yield Static(f"Running batch ping on {self.total} switches...", id="batch-status", classes="batch-status")
            yield Static("Press ESC to close", classes="modal-footer")

    async def on_mount(self) -> None:
        """Start batch ping when mounted."""
        output_log = self.query_one("#batch-output", RichLog)
        status = self.query_one("#batch-status", Static)

        # Start background task for batch ping
        self._ping_task = asyncio.create_task(self._run_batch_ping(output_log, status))

    async def _run_batch_ping(self, output_log: RichLog, status: Static) -> None:
        """Run batch ping on all switches in parallel.

        Args:
            output_log: RichLog widget for output
            status: Status widget for progress
        """
        try:
            # Create ping tasks for all switches
            tasks = [self._ping_single_switch(switch) for switch in self.switches]

            # Run all pings in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Display results
            for i, (switch, result) in enumerate(zip(self.switches, results)):
                self.completed += 1
                status.update(f"Completed {self.completed}/{self.total} pings")

                # Format header
                output_log.write(f"\n[bold cyan]>> {switch.name} ({switch.ip})[/bold cyan]")

                # Display result
                if isinstance(result, Exception):
                    output_log.write(f"[red]✗ Error: {str(result)}[/red]")
                elif result["success"]:
                    output_log.write(f"[green]✓ {result['output']}[/green]")
                else:
                    output_log.write(f"[yellow]{result['output']}[/yellow]")

            # Update final status
            status.update(f"✓ Batch ping completed ({self.completed}/{self.total})")

        except Exception as e:
            output_log.write(f"\n[red]✗ Batch ping error: {str(e)}[/red]")
            status.update("✗ Batch ping failed")

    async def _ping_single_switch(self, switch) -> dict:
        """Ping a single switch.

        Args:
            switch: Switch object to ping

        Returns:
            Dictionary with success flag and output/error message
        """
        try:
            # Run ping command (1 packet for speed)
            process = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", switch.ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            # Wait for completion with timeout
            stdout, _ = await asyncio.wait_for(
                process.communicate(),
                timeout=5.0
            )

            output = stdout.decode('utf-8', errors='replace').strip()

            # Check if ping was successful
            success = process.returncode == 0

            return {
                "success": success,
                "output": output if output else "No output"
            }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "output": "Timeout after 5 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "output": f"Error: {str(e)}"
            }

    def on_key(self, event: events.Key) -> None:
        """Handle key events - ESC closes modal and cancels pings.

        Args:
            event: Key event
        """
        if event.key == "escape":
            # Cancel ping task if still running
            if hasattr(self, '_ping_task') and not self._ping_task.done():
                self._ping_task.cancel()

            self.dismiss()
            event.stop()


class StreamingModal(BaseModal):
    """Modal for displaying live streaming command output."""

    DEFAULT_CSS = BaseModal.DEFAULT_CSS + """
    .modal-output {
        width: 100%;
        height: 30;
        padding: 1;
        overflow-y: auto;
        background: $surface;
        color: $text;
        border: solid $primary;
    }
    """

    def __init__(self, title: str, command: list[str]) -> None:
        """Initialize the streaming modal.

        Args:
            title: Modal title
            command: Command to execute as list of arguments
        """
        super().__init__()
        self.title_text = title
        self.command = command
        self.process = None

    def compose(self) -> ComposeResult:
        """Compose the modal."""
        with Container():
            yield Static(self.title_text, classes="modal-title")
            yield RichLog(id="output-log", classes="modal-output", wrap=True, highlight=False)
            yield Static("Press ESC to close", classes="modal-footer")

    async def on_mount(self) -> None:
        """Start streaming command output when mounted."""
        output_log = self.query_one("#output-log", RichLog)

        # Start background task to stream output
        self._stream_task = asyncio.create_task(self._stream_output(output_log))

    async def _stream_output(self, output_log: RichLog) -> None:
        """Stream command output in background task.

        Args:
            output_log: RichLog widget to write output to
        """
        try:
            # Start subprocess
            self.process = await asyncio.create_subprocess_exec(
                *self.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            # Stream output character by character for real-time display
            buffer = b""
            while True:
                try:
                    # Try to read 1 byte at a time for immediate display
                    chunk = await asyncio.wait_for(
                        self.process.stdout.read(1),
                        timeout=0.01  # 10ms timeout to keep UI responsive
                    )

                    if not chunk:
                        # Process finished
                        break

                    buffer += chunk

                    # Write complete lines immediately
                    if chunk == b'\n':
                        text = buffer.decode('utf-8', errors='replace').rstrip('\n')
                        if text:
                            output_log.write(text)
                        buffer = b""
                        # Small delay to allow UI to update
                        await asyncio.sleep(0)

                except asyncio.TimeoutError:
                    # No data available, write any buffered partial line
                    if buffer:
                        text = buffer.decode('utf-8', errors='replace')
                        output_log.write(text)
                        buffer = b""
                    continue

            # Write any remaining buffer
            if buffer:
                text = buffer.decode('utf-8', errors='replace')
                output_log.write(text)

            # Wait for process to complete
            await self.process.wait()

            # Show completion status
            if self.process.returncode == 0:
                output_log.write("[green]✓ Command completed successfully[/green]")
            else:
                output_log.write(f"[red]✗ Command exited with code {self.process.returncode}[/red]")

        except Exception as e:
            output_log.write(f"[red]✗ Error: {str(e)}[/red]")

    def on_key(self, event: events.Key) -> None:
        """Handle key events - ESC closes modal and terminates process.

        Args:
            event: Key event
        """
        if event.key == "escape":
            # Cancel streaming task
            if hasattr(self, '_stream_task') and not self._stream_task.done():
                self._stream_task.cancel()

            # Terminate process if still running
            if self.process and self.process.returncode is None:
                try:
                    self.process.terminate()
                except Exception:
                    pass

            self.dismiss()
            event.stop()
