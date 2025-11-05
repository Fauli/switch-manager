"""Business logic for managing switch data and operations."""

import csv
from pathlib import Path
from typing import Optional

from switch_manager.models import SearchMode, SortState, Switch


class SwitchManager:
    """Manages switch data, filtering, sorting, and search history.

    This class handles all business logic for switch operations including:
    - Loading switches from CSV files
    - Filtering switches based on search terms
    - Sorting switches by column
    - Managing search history
    """

    def __init__(self) -> None:
        """Initialize the SwitchManager with empty data."""
        self._all_switches: list[Switch] = []
        self._filtered_switches: list[Switch] = []
        self._search_history: list[str] = []
        self._search_mode: SearchMode = SearchMode.OR
        self._sort_state: SortState = SortState()

    @property
    def all_switches(self) -> list[Switch]:
        """Get all switches loaded from CSV."""
        return self._all_switches

    @property
    def filtered_switches(self) -> list[Switch]:
        """Get currently filtered switches."""
        return self._filtered_switches

    @property
    def search_mode(self) -> SearchMode:
        """Get current search mode (OR/AND)."""
        return self._search_mode

    @property
    def sort_state(self) -> SortState:
        """Get current sort state."""
        return self._sort_state

    @property
    def search_history(self) -> list[str]:
        """Get search history (last 20 searches)."""
        return self._search_history.copy()

    def load_csv(self, filepath: str, delimiter: str = ";") -> None:
        """Load switches from a CSV file.

        Expected CSV format:
            Name;IP;subnet;aliases;comment
            sw001;192.168.1.1;main;Core 1;Production

        Args:
            filepath: Path to CSV file
            delimiter: CSV delimiter character (default: ;)

        Note:
            - First row is treated as headers (case-insensitive)
            - Only first 5 columns are used (Name, IP, subnet, aliases, comment)
            - Additional columns are ignored
            - If file doesn't exist, switches remain empty
        """
        path = Path(filepath)

        # If file doesn't exist, leave switches empty (not an error)
        if not path.exists():
            self._all_switches = []
            self._filtered_switches = []
            return

        switches = []

        try:
            with path.open("r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=delimiter)

                # Read header row
                headers = next(reader, None)
                if not headers:
                    # Empty file
                    self._all_switches = []
                    self._filtered_switches = []
                    return

                # Normalize headers to lowercase for case-insensitive matching
                headers_lower = [h.lower().strip() for h in headers]

                # Find column indices (case-insensitive)
                try:
                    name_idx = headers_lower.index("name")
                    ip_idx = headers_lower.index("ip")
                    subnet_idx = headers_lower.index("subnet")
                    aliases_idx = headers_lower.index("aliases")
                    comment_idx = headers_lower.index("comment")
                except ValueError as e:
                    raise ValueError(
                        f"CSV file missing required column: {e}. "
                        "Expected: Name, IP, subnet, aliases, comment"
                    )

                # Read data rows
                for row_num, row in enumerate(reader, start=2):
                    if not row or len(row) < max(name_idx, ip_idx, subnet_idx,
                                                  aliases_idx, comment_idx) + 1:
                        # Skip empty or incomplete rows
                        continue

                    switch = Switch(
                        name=row[name_idx].strip(),
                        ip=row[ip_idx].strip(),
                        subnet=row[subnet_idx].strip(),
                        aliases=row[aliases_idx].strip(),
                        comment=row[comment_idx].strip(),
                    )
                    switches.append(switch)

        except Exception as e:
            raise ValueError(f"Error loading CSV file: {e}")

        self._all_switches = switches
        self._filtered_switches = switches.copy()

    def toggle_search_mode(self) -> SearchMode:
        """Toggle between OR and AND search modes.

        Returns:
            New search mode after toggle
        """
        if self._search_mode == SearchMode.OR:
            self._search_mode = SearchMode.AND
        else:
            self._search_mode = SearchMode.OR
        return self._search_mode

    def filter(self, search_terms: list[str]) -> list[Switch]:
        """Filter switches based on search terms and current search mode.

        Args:
            search_terms: List of search terms (tokenized by spaces)

        Returns:
            Filtered list of switches matching the criteria

        Search Modes:
            OR: Match if ANY term appears in ANY field
            AND: Match only if ALL terms appear (each can be in different field)
        """
        if not search_terms:
            # No search terms = show all switches
            self._filtered_switches = self._all_switches.copy()
            return self._filtered_switches

        if self._search_mode == SearchMode.OR:
            # OR mode: match if ANY term is in ANY field
            filtered = [
                switch for switch in self._all_switches
                if any(switch.matches_term(term) for term in search_terms)
            ]
        else:
            # AND mode: match only if ALL terms are found
            filtered = [
                switch for switch in self._all_switches
                if all(switch.matches_term(term) for term in search_terms)
            ]

        self._filtered_switches = filtered

        # Apply current sort if active
        if self._sort_state.column:
            self._filtered_switches = self._sort_switches(
                self._filtered_switches,
                self._sort_state.column,
                self._sort_state.ascending
            )

        return self._filtered_switches

    def sort(self, column: str, toggle: bool = True) -> list[Switch]:
        """Sort filtered switches by specified column.

        Args:
            column: Column name to sort by (name, ip, subnet, aliases, comment)
            toggle: If True and same column, toggle ascending/descending

        Returns:
            Sorted list of switches
        """
        # If same column and toggle enabled, flip the sort order
        if toggle and self._sort_state.column == column:
            self._sort_state.ascending = not self._sort_state.ascending
        else:
            # New column or toggle disabled
            self._sort_state.column = column
            self._sort_state.ascending = True

        self._filtered_switches = self._sort_switches(
            self._filtered_switches,
            column,
            self._sort_state.ascending
        )

        return self._filtered_switches

    def _sort_switches(
        self, switches: list[Switch], column: str, ascending: bool
    ) -> list[Switch]:
        """Internal method to sort a list of switches.

        Args:
            switches: List of switches to sort
            column: Column name to sort by
            ascending: Sort direction

        Returns:
            New sorted list of switches
        """
        # Map column names to Switch attributes
        column_map = {
            "name": lambda s: s.name.lower(),
            "ip": lambda s: s.ip,
            "subnet": lambda s: s.subnet.lower(),
            "aliases": lambda s: s.aliases.lower(),
            "comment": lambda s: s.comment.lower(),
        }

        if column not in column_map:
            return switches

        key_func = column_map[column]
        return sorted(switches, key=key_func, reverse=not ascending)

    def clear_sort(self) -> None:
        """Clear the current sort state."""
        self._sort_state = SortState()

    def add_to_history(self, search_text: str) -> None:
        """Add a search term to history.

        Args:
            search_text: Search string to add to history

        Note:
            - Maintains maximum of 20 items
            - Skips empty strings
            - Skips duplicate consecutive entries
        """
        if not search_text.strip():
            return

        # Don't add if it's the same as the last search
        if self._search_history and self._search_history[-1] == search_text:
            return

        self._search_history.append(search_text)

        # Keep only last 20 searches
        if len(self._search_history) > 20:
            self._search_history = self._search_history[-20:]

    def get_recent_history(self, limit: int = 10) -> list[str]:
        """Get recent search history in reverse chronological order.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of recent searches (newest first)
        """
        return list(reversed(self._search_history[-limit:]))
