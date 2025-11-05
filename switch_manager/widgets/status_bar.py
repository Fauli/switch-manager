"""Status bar widget for displaying application status."""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.reactive import reactive

from switch_manager.models import CommandType, COMMANDS


class StatusBar(Widget):
    """Widget displaying current status: switch count, active command, sort state, last result."""

    switch_count = reactive((0, 0))  # (filtered, total)
    active_command = reactive(CommandType.SSH)
    sort_indicator = reactive("")
    last_result = reactive("")

    def compose(self) -> ComposeResult:
        """Compose the status bar."""
        yield Static(id="status-bar-content")

    def on_mount(self) -> None:
        """Initialize the status bar on mount."""
        self.update_display()

    def watch_switch_count(self, old, new) -> None:
        """React to switch count changes."""
        self.update_display()

    def watch_active_command(self, old, new) -> None:
        """React to active command changes."""
        self.update_display()

    def watch_sort_indicator(self, old, new) -> None:
        """React to sort indicator changes."""
        self.update_display()

    def watch_last_result(self, old, new) -> None:
        """React to last result changes."""
        self.update_display()

    def update_display(self) -> None:
        """Update the status bar display."""
        content = self.query_one("#status-bar-content", Static)

        filtered, total = self.switch_count

        # Build status parts
        parts = []

        # Switch count
        if filtered == total:
            parts.append(f"{total} switches")
        else:
            parts.append(f"{filtered}/{total} switches")

        # Active command
        cmd_name = next(cmd.name for cmd in COMMANDS if cmd.type == self.active_command)
        parts.append(cmd_name)

        # Sort indicator
        if self.sort_indicator:
            parts.append(self.sort_indicator)

        # Last result
        if self.last_result:
            parts.append(self.last_result)

        # Join with separators
        status_text = " | ".join(parts)
        content.update(status_text)

    def set_switch_count(self, filtered: int, total: int) -> None:
        """Set the switch count.

        Args:
            filtered: Number of filtered switches
            total: Total number of switches
        """
        self.switch_count = (filtered, total)

    def set_active_command(self, command: CommandType) -> None:
        """Set the active command.

        Args:
            command: Active command type
        """
        self.active_command = command

    def set_sort_indicator(self, indicator: str) -> None:
        """Set the sort indicator.

        Args:
            indicator: Sort indicator string (e.g., "↑ Name")
        """
        self.sort_indicator = indicator

    def set_last_result(self, result: str) -> None:
        """Set the last operation result.

        Args:
            result: Result string (e.g., "✓ SSH opened")
        """
        self.last_result = result

    def clear_last_result(self) -> None:
        """Clear the last operation result."""
        self.last_result = ""
