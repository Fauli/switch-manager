"""Main screen for the switch manager application."""

import asyncio
from textual import events
from textual.screen import Screen
from textual.widgets import DataTable, Static, Input, Header, Footer
from textual.containers import Container, Vertical
from textual.reactive import reactive

from switch_manager.config import Config
from switch_manager.manager import SwitchManager
from switch_manager.models import SearchMode, CommandType, COMMANDS
from switch_manager.widgets.command_bar import CommandBar
from switch_manager.widgets.status_bar import StatusBar
from switch_manager.screens.modals import DetailsModal, HelpModal, ConfirmationModal, StreamingModal, OutputModal, BatchPingModal
from switch_manager.utils.validation import validate_ip, validate_username
from switch_manager.utils.terminal import spawn_ssh_terminal, get_platform_name
from switch_manager.utils.tmux_handler import is_tmux_available, create_tmux_session, attach_to_session


class MainScreen(Screen):
    """Main application screen with switch table and controls."""

    # Reactive properties
    search_text = reactive("")
    search_mode = reactive(SearchMode.OR)
    selected_command = reactive(CommandType.SSH)

    def __init__(self, config: Config, manager: SwitchManager) -> None:
        """Initialize the main screen.

        Args:
            config: Application configuration
            manager: Switch manager instance
        """
        super().__init__()
        self.config = config
        self.manager = manager
        self.table_cursor_row = 0
        self.search_input_focused = False
        self.selected_rows = set()  # Track selected row indices for batch operations

    def compose(self):
        """Build the UI layout."""
        with Vertical():
            # Title bar
            yield Static("V-Li: Switch Manager", id="title")

            # Command bar (interactive widget)
            yield CommandBar()

            # Search help bar
            yield Static(
                "🔍 Search (OR mode) - Ctrl+L: Toggle | Ctrl+H: History | ESC: Clear",
                id="search-help"
            )

            # Search input
            yield Input(
                placeholder="Search... (OR mode)",
                id="search-input"
            )

            # Result counter
            yield Static("Loading switches...", id="result-counter")

            # Main data table
            yield DataTable(id="switch-table", zebra_stripes=True, cursor_type="row")

            # Keyboard shortcuts bar
            yield Static(
                "F1-F5:Sort | 1-8:Cmd | ↑↓:Nav | Space:Select | ←→:Cmd | Enter:Exec | "
                "Ctrl+L:Mode | ?:Help",
                id="shortcuts"
            )

            # Status bar (interactive widget)
            yield StatusBar()

    async def on_mount(self) -> None:
        """Initialize the screen after mounting."""
        # Get widgets
        table = self.query_one("#switch-table", DataTable)

        # Set up table columns
        table.add_column("Name", key="name")
        table.add_column("IP", key="ip")
        table.add_column("subnet", key="subnet")
        table.add_column("Alias", key="aliases")
        table.add_column("comment", key="comment")

        # Focus the table
        table.focus()

        # Load CSV data asynchronously
        await self.load_data()

    async def load_data(self) -> None:
        """Load CSV data and populate the table."""
        result_counter = self.query_one("#result-counter", Static)
        table = self.query_one("#switch-table", DataTable)
        status_bar = self.query_one(StatusBar)

        try:
            # Show loading message
            result_counter.update("V-Li is collecting all the data for you... Please be patient...")

            # Load CSV in background to avoid blocking UI
            await asyncio.to_thread(
                self.manager.load_csv,
                self.config.sm_csv_data,
                self.config.sm_delimiter
            )

            # Populate table
            switches = self.manager.all_switches

            if switches:
                for idx, switch in enumerate(switches):
                    is_selected = idx in self.selected_rows
                    name_display = f"{'☑' if is_selected else '☐'} {switch.name}"

                    table.add_row(
                        name_display,
                        switch.ip,
                        switch.subnet,
                        switch.aliases,
                        switch.comment,
                        key=switch.name  # Use name as unique key
                    )

                # Update result counter
                count = len(switches)
                result_counter.update(f"Showing all {count} switches")

                # Update status bar
                status_bar.set_switch_count(count, count)
                status_bar.set_active_command(CommandType.SSH)

                # Move cursor to first row
                if table.row_count > 0:
                    table.move_cursor(row=0)
                    self.table_cursor_row = 0
            else:
                # No data loaded
                result_counter.update("No switches found. Check CSV file.")
                status_bar.set_switch_count(0, 0)
                status_bar.set_active_command(CommandType.SSH)

        except Exception as e:
            # Handle loading errors
            result_counter.update(f"Error loading CSV: {str(e)}")
            status_bar.set_switch_count(0, 0)
            status_bar.set_last_result("✗ Error loading CSV")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Track the currently highlighted row."""
        self.table_cursor_row = event.cursor_row

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes - filter in real-time.

        Args:
            event: Input change event
        """
        if event.input.id != "search-input":
            return

        self.search_text = event.value
        self.perform_search()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission (Enter key).

        Args:
            event: Input submission event
        """
        if event.input.id != "search-input":
            return

        # Add to history
        if event.value.strip():
            self.manager.add_to_history(event.value.strip())

        # Return focus to table
        table = self.query_one("#switch-table", DataTable)
        table.focus()
        self.search_input_focused = False

    def perform_search(self) -> None:
        """Perform search and update table."""
        search_terms = self.search_text.split() if self.search_text else []

        # Filter switches
        filtered = self.manager.filter(search_terms)

        # Refresh table
        self.refresh_table(filtered)

        # Update result counter
        self.update_result_counter(filtered, self.search_text)

    def refresh_table(self, switches) -> None:
        """Refresh the table with given switches.

        Args:
            switches: List of Switch objects to display
        """
        table = self.query_one("#switch-table", DataTable)

        # Clear existing rows
        table.clear()

        # Clear selection when table is refreshed (filtered switches changed)
        self.selected_rows.clear()

        # Add rows with selection indicators
        for idx, switch in enumerate(switches):
            # Add selection indicator to name
            is_selected = idx in self.selected_rows
            name_display = f"{'☑' if is_selected else '☐'} {switch.name}"

            table.add_row(
                name_display,
                switch.ip,
                switch.subnet,
                switch.aliases,
                switch.comment,
                key=switch.name
            )

        # Reset cursor to first row
        if table.row_count > 0:
            table.move_cursor(row=0)
            self.table_cursor_row = 0
        else:
            self.table_cursor_row = -1

    def update_result_counter(self, filtered_switches, search_text: str = "") -> None:
        """Update the result counter display.

        Args:
            filtered_switches: List of filtered switches
            search_text: Current search text
        """
        result_counter = self.query_one("#result-counter", Static)
        status_bar = self.query_one(StatusBar)

        total_count = len(self.manager.all_switches)
        filtered_count = len(filtered_switches)

        if filtered_count == total_count:
            # Showing all
            result_counter.update(f"Showing all {total_count} switches")
        elif search_text:
            # Filtered with search text
            result_counter.update(
                f"Showing {filtered_count} of {total_count} switches "
                f"(filtered by: '{search_text}')"
            )
        else:
            # Filtered but no search text
            result_counter.update(f"Showing {filtered_count} of {total_count} switches")

        # Update status bar widget
        status_bar.set_switch_count(filtered_count, total_count)
        status_bar.set_sort_indicator(self.get_sort_indicator())

    def get_sort_indicator(self) -> str:
        """Get sort indicator string for status bar.

        Returns:
            Sort indicator string (e.g., " | ↑ Name")
        """
        sort_state = self.manager.sort_state
        if sort_state.column:
            arrow = "↑" if sort_state.ascending else "↓"
            col_name = sort_state.column.capitalize()
            return f" | {arrow} {col_name}"
        return ""

    def watch_search_mode(self, old_mode: SearchMode, new_mode: SearchMode) -> None:
        """Watcher for search_mode reactive property.

        Args:
            old_mode: Previous search mode
            new_mode: New search mode
        """
        # Update search help bar
        search_help = self.query_one("#search-help", Static)
        mode_str = new_mode.value
        search_help.update(
            f"🔍 Search ({mode_str} mode) - Ctrl+L: Toggle | Ctrl+H: History | ESC: Clear"
        )

        # Update search input placeholder
        search_input = self.query_one("#search-input", Input)
        search_input.placeholder = f"Search... ({mode_str} mode)"

        # Re-run search with new mode
        if self.search_text:
            self.perform_search()

    async def on_key(self, event: events.Key) -> None:
        """Handle global keyboard shortcuts.

        Args:
            event: Key event
        """
        table = self.query_one("#switch-table", DataTable)
        search_input = self.query_one("#search-input", Input)

        # Check if search input has focus
        search_has_focus = search_input.has_focus

        # Ctrl+L: Toggle search mode
        if event.key == "ctrl+l":
            self.search_mode = self.manager.toggle_search_mode()
            event.stop()
            return

        # ESC: Clear search (if search has focus and has text)
        if event.key == "escape" and search_has_focus and search_input.value:
            search_input.value = ""
            self.search_text = ""
            self.perform_search()
            table.focus()
            event.stop()
            return

        # ESC: Exit (if search is empty or doesn't have focus)
        if event.key == "escape" and (not search_has_focus or not search_input.value):
            self.app.exit()
            return

        # Column sorting: F1-F5
        if event.key == "f1":
            self.sort_by_column("name")
            event.stop()
            return
        elif event.key == "f2":
            self.sort_by_column("ip")
            event.stop()
            return
        elif event.key == "f3":
            self.sort_by_column("subnet")
            event.stop()
            return
        elif event.key == "f4":
            self.sort_by_column("aliases")
            event.stop()
            return
        elif event.key == "f5":
            self.sort_by_column("comment")
            event.stop()
            return

        # Command selection: 1-8 keys (when search doesn't have focus)
        if not search_has_focus and event.key in "12345678":
            command_num = int(event.key)
            self.select_command_by_number(command_num)
            event.stop()
            return

        # Command selection: ← and → arrows (when search doesn't have focus)
        if not search_has_focus:
            if event.key == "left":
                self.select_previous_command()
                event.stop()
                return
            elif event.key == "right":
                self.select_next_command()
                event.stop()
                return

        # Execute command: Enter key (when table has focus)
        if event.key == "enter" and not search_has_focus:
            await self.execute_selected_command()
            event.stop()
            return

        # ? shortcut for help (when search doesn't have focus)
        if event.key == "question_mark" and not search_has_focus:
            self.selected_command = CommandType.HELP
            await self.execute_selected_command()
            event.stop()
            return

        # Space: Toggle selection (when table has focus)
        if event.key == "space" and not search_has_focus:
            self.toggle_selection()
            event.stop()
            return

        # Auto-focus search on printable characters (if not already focused)
        if not search_has_focus and len(event.key) == 1 and event.key.isprintable():
            search_input.focus()
            # Don't stop the event - let it go to the input
            return

        # Navigation: Arrow keys (only when table has focus)
        if not search_has_focus:
            if event.key == "up":
                if table.row_count > 0:
                    new_row = (self.table_cursor_row - 1) % table.row_count
                    table.move_cursor(row=new_row)
                    self.table_cursor_row = new_row
                    event.stop()

            elif event.key == "down":
                if table.row_count > 0:
                    new_row = (self.table_cursor_row + 1) % table.row_count
                    table.move_cursor(row=new_row)
                    self.table_cursor_row = new_row
                    event.stop()

        # 'q' to quit (when search doesn't have focus)
        if event.key == "q" and not search_has_focus:
            await self.execute_exit_command()
            event.stop()

    def sort_by_column(self, column: str) -> None:
        """Sort table by specified column.

        Args:
            column: Column name (name, ip, subnet, aliases, comment)
        """
        # Perform sort
        sorted_switches = self.manager.sort(column, toggle=True)

        # Refresh table
        self.refresh_table(sorted_switches)

        # Update result counter with sort indicator
        self.update_result_counter(sorted_switches, self.search_text)

        # Update column headers with sort indicator
        self.update_column_headers()

    def update_column_headers(self) -> None:
        """Update table column headers with sort indicators."""
        table = self.query_one("#switch-table", DataTable)
        sort_state = self.manager.sort_state

        # Column label mapping
        column_labels = {
            "name": "Name",
            "ip": "IP",
            "subnet": "subnet",
            "aliases": "Alias",
            "comment": "comment"
        }

        # Update each column header
        for col_key, base_label in column_labels.items():
            if sort_state.column == col_key:
                # This column is being sorted - add indicator
                arrow = "↑" if sort_state.ascending else "↓"
                label = f"{base_label} {arrow}"
            else:
                # No sort indicator
                label = base_label

            # Update column label
            table.columns[col_key].label = label

    def select_command_by_number(self, number: int) -> None:
        """Select a command by its number (1-8).

        Args:
            number: Command number
        """
        command_bar = self.query_one(CommandBar)
        status_bar = self.query_one(StatusBar)

        # Update selected command
        self.selected_command = CommandType(number)
        command_bar.select_command(self.selected_command)
        status_bar.set_active_command(self.selected_command)

    def select_next_command(self) -> None:
        """Select the next command (wraps around)."""
        command_bar = self.query_one(CommandBar)
        status_bar = self.query_one(StatusBar)

        command_bar.select_next()
        self.selected_command = command_bar.selected_command
        status_bar.set_active_command(self.selected_command)

    def select_previous_command(self) -> None:
        """Select the previous command (wraps around)."""
        command_bar = self.query_one(CommandBar)
        status_bar = self.query_one(StatusBar)

        command_bar.select_previous()
        self.selected_command = command_bar.selected_command
        status_bar.set_active_command(self.selected_command)

    async def execute_selected_command(self) -> None:
        """Execute the currently selected command."""
        # Get command metadata
        cmd = next(c for c in COMMANDS if c.type == self.selected_command)

        # Check if switch selection is required
        if cmd.requires_selection:
            selected_switch = self.get_selected_switch()
            if not selected_switch:
                # No switch selected - do nothing
                return

        # Execute based on command type
        if self.selected_command == CommandType.SSH:
            await self.execute_ssh_command()
        elif self.selected_command == CommandType.PING:
            await self.execute_ping_command()
        elif self.selected_command == CommandType.TRACEROUTE:
            await self.execute_traceroute_command()
        elif self.selected_command == CommandType.BATCH_PING:
            await self.execute_batch_ping_command()
        elif self.selected_command == CommandType.TMUX:
            await self.execute_tmux_command()
        elif self.selected_command == CommandType.DETAILS:
            await self.execute_details_command()
        elif self.selected_command == CommandType.HELP:
            await self.execute_help_command()
        elif self.selected_command == CommandType.EXIT:
            await self.execute_exit_command()

    async def execute_ssh_command(self) -> None:
        """Execute SSH command - open terminal to selected switch."""
        selected_switch = self.get_selected_switch()
        if not selected_switch:
            return

        status_bar = self.query_one(StatusBar)

        # Validate IP address
        if not validate_ip(selected_switch.ip):
            modal = OutputModal(
                title="Invalid IP Address",
                content=f"The IP address '{selected_switch.ip}' is not valid.\n\n"
                        f"SSH connection cannot be established."
            )
            await self.app.push_screen(modal)
            status_bar.set_last_result("✗ Invalid IP")
            return

        # Validate username from config
        if not self.config.sm_user:
            modal = OutputModal(
                title="Missing Username",
                content="SM_USER environment variable is not set.\n\n"
                        "Please set your SSH username:\n"
                        "export SM_USER=your_username"
            )
            await self.app.push_screen(modal)
            status_bar.set_last_result("✗ No username")
            return

        if not validate_username(self.config.sm_user):
            modal = OutputModal(
                title="Invalid Username",
                content=f"The username '{self.config.sm_user}' contains invalid characters.\n\n"
                        f"Username can only contain: letters, numbers, dots, dashes, underscores"
            )
            await self.app.push_screen(modal)
            status_bar.set_last_result("✗ Invalid username")
            return

        # Spawn SSH terminal
        success = spawn_ssh_terminal(self.config.sm_user, selected_switch.ip)

        if success:
            status_bar.set_last_result(f"✓ SSH opened to {selected_switch.name}")
        else:
            platform = get_platform_name()
            modal = OutputModal(
                title="Terminal Not Available",
                content=f"Could not open terminal on {platform}.\n\n"
                        f"Please ensure you have a terminal emulator installed."
            )
            await self.app.push_screen(modal)
            status_bar.set_last_result("✗ Terminal failed")

    async def execute_ping_command(self) -> None:
        """Execute ping command - show streaming output."""
        selected_switch = self.get_selected_switch()
        if not selected_switch:
            return

        status_bar = self.query_one(StatusBar)

        # Validate IP address
        if not validate_ip(selected_switch.ip):
            modal = OutputModal(
                title="Invalid IP Address",
                content=f"The IP address '{selected_switch.ip}' is not valid."
            )
            await self.app.push_screen(modal)
            status_bar.set_last_result("✗ Invalid IP")
            return

        # Create streaming modal
        title = f"Ping: {selected_switch.name} ({selected_switch.ip})"
        command = ["ping", "-c", "4", selected_switch.ip]

        modal = StreamingModal(title, command)
        await self.app.push_screen(modal)
        status_bar.set_last_result(f"✓ Pinged {selected_switch.name}")

    async def execute_traceroute_command(self) -> None:
        """Execute traceroute command - show streaming output."""
        selected_switch = self.get_selected_switch()
        if not selected_switch:
            return

        status_bar = self.query_one(StatusBar)

        # Validate IP address
        if not validate_ip(selected_switch.ip):
            modal = OutputModal(
                title="Invalid IP Address",
                content=f"The IP address '{selected_switch.ip}' is not valid."
            )
            await self.app.push_screen(modal)
            status_bar.set_last_result("✗ Invalid IP")
            return

        # Create streaming modal
        title = f"Traceroute: {selected_switch.name} ({selected_switch.ip})"
        command = ["traceroute", selected_switch.ip]

        modal = StreamingModal(title, command)
        await self.app.push_screen(modal)
        status_bar.set_last_result(f"✓ Traceroute to {selected_switch.name}")

    async def execute_batch_ping_command(self) -> None:
        """Execute batch ping on selected switches (or all filtered if none selected)."""
        status_bar = self.query_one(StatusBar)

        # Get switches to ping - either selected or all filtered
        switches_to_ping = self.get_selected_switches()

        if not switches_to_ping:
            # No switches selected, use all filtered switches
            switches_to_ping = self.manager.filtered_switches

        if not switches_to_ping:
            # No switches at all
            modal = OutputModal(
                title="No Switches",
                content="No switches available to ping.\n\n"
                        "Please load switches or adjust your filter."
            )
            await self.app.push_screen(modal)
            status_bar.set_last_result("✗ No switches to ping")
            return

        # Validate all IP addresses before showing confirmation
        invalid_ips = []
        for switch in switches_to_ping:
            if not validate_ip(switch.ip):
                invalid_ips.append(f"{switch.name} ({switch.ip})")

        if invalid_ips:
            modal = OutputModal(
                title="Invalid IP Addresses",
                content=f"The following switches have invalid IP addresses:\n\n"
                        f"{chr(10).join(invalid_ips)}\n\n"
                        f"Batch ping cannot proceed."
            )
            await self.app.push_screen(modal)
            status_bar.set_last_result("✗ Invalid IPs")
            return

        # Show confirmation dialog
        count = len(switches_to_ping)
        selection_msg = f"{count} selected switch{'es' if count != 1 else ''}" if self.get_selected_switches() else f"all {count} filtered switch{'es' if count != 1 else ''}"

        confirmation = ConfirmationModal(
            title="Batch Ping Confirmation",
            message=f"Ping {selection_msg}?",
            warning=f"This will run {count} ping command{'s' if count != 1 else ''} in parallel"
        )

        # Use callback pattern instead of push_screen_wait to avoid worker context issues
        def handle_confirmation(result):
            if result:
                # User confirmed - execute batch ping
                async def run_ping():
                    modal = BatchPingModal(switches_to_ping)
                    await self.app.push_screen(modal)
                    status_bar.set_last_result(f"✓ Batch ping completed ({count} switches)")

                self.app.call_later(lambda: self.run_worker(run_ping))
            else:
                # User cancelled
                status_bar.set_last_result("Batch ping cancelled")

        await self.app.push_screen(confirmation, callback=handle_confirmation)

    async def execute_tmux_command(self) -> None:
        """Execute TMUX command - open synchronized session for selected switches."""
        status_bar = self.query_one(StatusBar)

        # Check if TMUX is available
        if not is_tmux_available():
            modal = OutputModal(
                title="TMUX Not Available",
                content="TMUX is not installed or not available on this system.\n\n"
                        "Please install TMUX to use synchronized sessions:\n"
                        "  macOS:   brew install tmux\n"
                        "  Linux:   apt install tmux / yum install tmux\n"
                        "  Windows: Use WSL with tmux installed"
            )
            await self.app.push_screen(modal)
            status_bar.set_last_result("✗ TMUX not available")
            return

        # Validate username from config
        if not self.config.sm_user:
            modal = OutputModal(
                title="Missing Username",
                content="SM_USER environment variable is not set.\n\n"
                        "Please set your SSH username:\n"
                        "export SM_USER=your_username"
            )
            await self.app.push_screen(modal)
            status_bar.set_last_result("✗ No username")
            return

        if not validate_username(self.config.sm_user):
            modal = OutputModal(
                title="Invalid Username",
                content=f"The username '{self.config.sm_user}' contains invalid characters.\n\n"
                        f"Username can only contain: letters, numbers, dots, dashes, underscores"
            )
            await self.app.push_screen(modal)
            status_bar.set_last_result("✗ Invalid username")
            return

        # Get switches - either selected or all filtered
        switches_for_tmux = self.get_selected_switches()

        if not switches_for_tmux:
            # No switches selected, use all filtered switches
            switches_for_tmux = self.manager.filtered_switches

        if not switches_for_tmux:
            # No switches at all
            modal = OutputModal(
                title="No Switches",
                content="No switches available for TMUX session.\n\n"
                        "Please load switches or adjust your filter."
            )
            await self.app.push_screen(modal)
            status_bar.set_last_result("✗ No switches for TMUX")
            return

        # Validate all IP addresses before showing confirmation
        invalid_ips = []
        for switch in switches_for_tmux:
            if not validate_ip(switch.ip):
                invalid_ips.append(f"{switch.name} ({switch.ip})")

        if invalid_ips:
            modal = OutputModal(
                title="Invalid IP Addresses",
                content=f"The following switches have invalid IP addresses:\n\n"
                        f"{chr(10).join(invalid_ips)}\n\n"
                        f"TMUX session cannot proceed."
            )
            await self.app.push_screen(modal)
            status_bar.set_last_result("✗ Invalid IPs")
            return

        # Show confirmation dialog
        count = len(switches_for_tmux)
        selection_msg = f"{count} selected switch{'es' if count != 1 else ''}" if self.get_selected_switches() else f"all {count} filtered switch{'es' if count != 1 else ''}"

        confirmation = ConfirmationModal(
            title="TMUX Synchronized Session",
            message=f"Launch TMUX session with {selection_msg}?",
            warning=f"Synchronized panes: Commands typed will affect ALL {count} switches!\n"
                    f"The application will exit after creating the TMUX session."
        )

        # Use callback pattern
        def handle_confirmation(result):
            if result:
                # User confirmed - create TMUX session
                success = create_tmux_session(
                    switches_for_tmux,
                    self.config.sm_user,
                    "switch-manager"
                )

                if success:
                    # Attach to the session - this will exit the app
                    attach_to_session("switch-manager")
                    # If we get here, attach failed
                    status_bar.set_last_result("✗ Failed to attach to TMUX")
                else:
                    # Failed to create session
                    async def show_error():
                        modal = OutputModal(
                            title="TMUX Session Failed",
                            content="Failed to create TMUX session.\n\n"
                                    "Please check that TMUX is installed correctly."
                        )
                        await self.app.push_screen(modal)
                        status_bar.set_last_result("✗ TMUX session failed")

                    self.app.call_later(lambda: self.run_worker(show_error))
            else:
                # User cancelled
                status_bar.set_last_result("TMUX session cancelled")

        await self.app.push_screen(confirmation, callback=handle_confirmation)

    async def execute_details_command(self) -> None:
        """Show details modal for selected switch."""
        selected_switch = self.get_selected_switch()
        if not selected_switch:
            return

        modal = DetailsModal(selected_switch)
        await self.app.push_screen(modal)

    async def execute_help_command(self) -> None:
        """Show help modal."""
        modal = HelpModal()
        await self.app.push_screen(modal)

    async def execute_exit_command(self) -> None:
        """Show exit confirmation and quit if confirmed."""
        modal = ConfirmationModal(
            title="Exit V-Li Switch Manager?",
            message="Are you sure you want to quit?",
            warning=""
        )

        # Use callback pattern instead of push_screen_wait to avoid worker context issues
        def handle_exit(result):
            if result:
                # User confirmed - exit
                self.app.exit()

        await self.app.push_screen(modal, callback=handle_exit)

    def get_selected_switch(self):
        """Get the currently selected switch.

        Returns:
            Switch object or None if no selection or no switches
        """
        if not self.manager.filtered_switches:
            return None

        if 0 <= self.table_cursor_row < len(self.manager.filtered_switches):
            return self.manager.filtered_switches[self.table_cursor_row]

        return None

    def get_selected_switches(self) -> list:
        """Get all switches that have been selected (checked) for batch operations.

        Returns:
            List of Switch objects that are selected. Empty list if none selected.
        """
        if not self.selected_rows:
            return []

        filtered = self.manager.filtered_switches
        return [filtered[idx] for idx in sorted(self.selected_rows) if idx < len(filtered)]

    def toggle_selection(self) -> None:
        """Toggle selection state of the currently highlighted row."""
        table = self.query_one("#switch-table", DataTable)

        if table.row_count == 0:
            return

        # Toggle selection for current row
        if self.table_cursor_row in self.selected_rows:
            self.selected_rows.remove(self.table_cursor_row)
        else:
            self.selected_rows.add(self.table_cursor_row)

        # Refresh the table to update selection indicators
        filtered = self.manager.filtered_switches
        self.refresh_table_preserving_selection(filtered)

        # Update status bar to show selection count
        status_bar = self.query_one(StatusBar)
        count = len(self.selected_rows)
        if count > 0:
            status_bar.set_last_result(f"✓ {count} switch{'es' if count != 1 else ''} selected")
        else:
            status_bar.set_last_result("")

    def refresh_table_preserving_selection(self, switches) -> None:
        """Refresh table without clearing selection.

        Args:
            switches: List of Switch objects to display
        """
        table = self.query_one("#switch-table", DataTable)
        current_row = self.table_cursor_row

        # Clear table
        table.clear()

        # Add rows with selection indicators
        for idx, switch in enumerate(switches):
            is_selected = idx in self.selected_rows
            name_display = f"{'☑' if is_selected else '☐'} {switch.name}"

            table.add_row(
                name_display,
                switch.ip,
                switch.subnet,
                switch.aliases,
                switch.comment,
                key=switch.name
            )

        # Restore cursor position
        if table.row_count > 0 and current_row < table.row_count:
            table.move_cursor(row=current_row)
        elif table.row_count > 0:
            table.move_cursor(row=0)
            self.table_cursor_row = 0
