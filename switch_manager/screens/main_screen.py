"""Main screen for the switch manager application."""

import asyncio
from textual import events
from textual.screen import Screen
from textual.widgets import DataTable, Static, Input, Header, Footer
from textual.containers import Container, Vertical
from textual.reactive import reactive

from switch_manager.config import Config
from switch_manager.manager import SwitchManager
from switch_manager.models import SearchMode


class MainScreen(Screen):
    """Main application screen with switch table and controls."""

    # Reactive properties
    search_text = reactive("")
    search_mode = reactive(SearchMode.OR)

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

    def compose(self):
        """Build the UI layout."""
        with Vertical():
            # Title bar
            yield Static("V-Li: Switch Manager", id="title")

            # Command bar
            yield Static(
                "NETWORK: (1)ssh (2)ping (3)traceroute (4)batch ping (5)tmux | "
                "SYSTEM: (6)details (7)help (8)exit",
                id="command-bar"
            )

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
                "F1-F5:Sort | 1-8:Cmd | ↑↓:Nav | ←→:Cmd | Enter:Exec | "
                "Ctrl+L:Mode | ?:Help",
                id="shortcuts"
            )

            # Status bar
            yield Static("0 switches | ssh", id="status-bar")

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
        status_bar = self.query_one("#status-bar", Static)

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
                for switch in switches:
                    table.add_row(
                        switch.name,
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
                status_bar.update(f"{count} switches | ssh")

                # Move cursor to first row
                if table.row_count > 0:
                    table.move_cursor(row=0)
                    self.table_cursor_row = 0
            else:
                # No data loaded
                result_counter.update("No switches found. Check CSV file.")
                status_bar.update("0 switches | ssh")

        except Exception as e:
            # Handle loading errors
            result_counter.update(f"Error loading CSV: {str(e)}")
            status_bar.update("0 switches | error")

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

        # Add rows
        for switch in switches:
            table.add_row(
                switch.name,
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
        status_bar = self.query_one("#status-bar", Static)

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

        # Update status bar
        sort_indicator = self.get_sort_indicator()
        status_bar.update(f"{filtered_count}/{total_count} switches | ssh{sort_indicator}")

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

    def on_key(self, event: events.Key) -> None:
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

        # 'q' to quit
        if event.key == "q" and not search_has_focus:
            self.app.exit()

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
