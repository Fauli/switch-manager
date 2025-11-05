"""Command bar widget for displaying and selecting commands."""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.reactive import reactive

from switch_manager.models import COMMANDS, CommandType


class CommandBar(Widget):
    """Widget displaying available commands with highlighting for active command."""

    selected_command = reactive(CommandType.SSH)

    def compose(self) -> ComposeResult:
        """Compose the command bar."""
        yield Static(id="command-bar-content")

    def on_mount(self) -> None:
        """Initialize the command bar on mount."""
        self.update_display()

    def watch_selected_command(self, old: CommandType, new: CommandType) -> None:
        """React to selected command changes.

        Args:
            old: Previous command type
            new: New command type
        """
        self.update_display()

    def update_display(self) -> None:
        """Update the command bar display with highlighting."""
        content = self.query_one("#command-bar-content", Static)

        # Build command text with highlighting
        network_cmds = []
        system_cmds = []

        for cmd in COMMANDS:
            # Format: (1)ssh
            cmd_text = f"({cmd.number}){cmd.name}"

            # Highlight if selected
            if cmd.type == self.selected_command:
                cmd_text = f"[bold reverse]{cmd_text}[/bold reverse]"

            if cmd.category == "NETWORK":
                network_cmds.append(cmd_text)
            else:
                system_cmds.append(cmd_text)

        # Combine with separators
        network_str = " ".join(network_cmds)
        system_str = " ".join(system_cmds)

        full_text = f"NETWORK: {network_str} | SYSTEM: {system_str}"
        content.update(full_text)

    def select_command(self, command_type: CommandType) -> None:
        """Select a command.

        Args:
            command_type: Command to select
        """
        self.selected_command = command_type

    def select_next(self) -> None:
        """Select the next command (wraps around)."""
        current_idx = self.selected_command.value
        next_idx = (current_idx % 8) + 1
        self.selected_command = CommandType(next_idx)

    def select_previous(self) -> None:
        """Select the previous command (wraps around)."""
        current_idx = self.selected_command.value
        prev_idx = ((current_idx - 2) % 8) + 1
        self.selected_command = CommandType(prev_idx)
