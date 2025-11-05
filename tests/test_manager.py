"""Unit tests for SwitchManager business logic."""

import csv
import tempfile
from pathlib import Path

import pytest

from switch_manager.manager import SwitchManager
from switch_manager.models import SearchMode, Switch


class TestSwitchManagerInit:
    """Test SwitchManager initialization."""

    def test_init_empty(self) -> None:
        """Test SwitchManager initializes with empty data."""
        manager = SwitchManager()
        assert manager.all_switches == []
        assert manager.filtered_switches == []
        assert manager.search_mode == SearchMode.OR
        assert manager.search_history == []
        assert manager.sort_state.column is None
        assert manager.sort_state.ascending is True


class TestLoadCSV:
    """Test CSV loading functionality."""

    @pytest.fixture
    def temp_csv(self) -> Path:
        """Create a temporary CSV file for testing."""
        content = """Name;IP;subnet;aliases;comment
sw001-lx-prod;192.168.10.1;rum;Main switch;Production core switch
sw002-lx-test;192.168.10.17;bas;Edge switch;Test environment
sw003-lx-backup;10.0.1.3;rum;Backup switch;Backup core switch
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            path = Path(f.name)

        yield path
        path.unlink()  # Cleanup

    def test_load_csv_basic(self, temp_csv: Path) -> None:
        """Test loading a basic CSV file."""
        manager = SwitchManager()
        manager.load_csv(str(temp_csv))

        assert len(manager.all_switches) == 3
        assert len(manager.filtered_switches) == 3

        # Check first switch
        sw = manager.all_switches[0]
        assert sw.name == "sw001-lx-prod"
        assert sw.ip == "192.168.10.1"
        assert sw.subnet == "rum"
        assert sw.aliases == "Main switch"
        assert sw.comment == "Production core switch"

    def test_load_csv_with_comma_delimiter(self) -> None:
        """Test loading CSV with comma delimiter."""
        content = """Name,IP,subnet,aliases,comment
sw001,192.168.1.1,main,Core,Production
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            path = Path(f.name)

        try:
            manager = SwitchManager()
            manager.load_csv(str(path), delimiter=",")

            assert len(manager.all_switches) == 1
            assert manager.all_switches[0].name == "sw001"
            assert manager.all_switches[0].ip == "192.168.1.1"
        finally:
            path.unlink()

    def test_load_csv_case_insensitive_headers(self) -> None:
        """Test CSV loading with mixed-case headers."""
        content = """NAME;ip;SUBNET;Aliases;CoMmEnT
sw001;192.168.1.1;main;Core;Production
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            path = Path(f.name)

        try:
            manager = SwitchManager()
            manager.load_csv(str(path))

            assert len(manager.all_switches) == 1
            assert manager.all_switches[0].name == "sw001"
        finally:
            path.unlink()

    def test_load_csv_nonexistent_file(self) -> None:
        """Test loading a nonexistent CSV file."""
        manager = SwitchManager()
        manager.load_csv("/nonexistent/file.csv")

        # Should not raise error, just leave switches empty
        assert manager.all_switches == []
        assert manager.filtered_switches == []

    def test_load_csv_empty_file(self) -> None:
        """Test loading an empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            path = Path(f.name)

        try:
            manager = SwitchManager()
            manager.load_csv(str(path))

            assert manager.all_switches == []
            assert manager.filtered_switches == []
        finally:
            path.unlink()

    def test_load_csv_missing_columns(self) -> None:
        """Test loading CSV with missing required columns."""
        content = """Name;IP;subnet
sw001;192.168.1.1;main
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            path = Path(f.name)

        try:
            manager = SwitchManager()
            with pytest.raises(ValueError, match="missing required column"):
                manager.load_csv(str(path))
        finally:
            path.unlink()

    def test_load_csv_with_extra_columns(self) -> None:
        """Test loading CSV with extra columns (should be ignored)."""
        content = """Name;IP;subnet;aliases;comment;extra1;extra2
sw001;192.168.1.1;main;Core;Production;ignored1;ignored2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            path = Path(f.name)

        try:
            manager = SwitchManager()
            manager.load_csv(str(path))

            assert len(manager.all_switches) == 1
            # Only first 5 columns are used
            assert manager.all_switches[0].name == "sw001"
            assert manager.all_switches[0].comment == "Production"
        finally:
            path.unlink()

    def test_load_csv_strips_whitespace(self) -> None:
        """Test that CSV loading strips whitespace from fields."""
        content = """Name;IP;subnet;aliases;comment
  sw001  ;  192.168.1.1  ;  main  ;  Core  ;  Production
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            path = Path(f.name)

        try:
            manager = SwitchManager()
            manager.load_csv(str(path))

            sw = manager.all_switches[0]
            assert sw.name == "sw001"
            assert sw.ip == "192.168.1.1"
            assert sw.subnet == "main"
            assert sw.aliases == "Core"
            assert sw.comment == "Production"
        finally:
            path.unlink()


class TestFilter:
    """Test filtering functionality."""

    @pytest.fixture
    def manager_with_data(self) -> SwitchManager:
        """Create a SwitchManager with test data."""
        content = """Name;IP;subnet;aliases;comment
sw001-lx-prod;192.168.10.1;rum;Main switch,Core;Production core switch
sw002-lx-test;192.168.10.17;bas;Edge switch;Test environment
sw003-lx-backup;10.0.1.3;rum;Backup switch;Backup core switch
sw004-ny-prod;172.16.0.5;rum;NYC switch;Production NYC switch
sw005-ny-test;172.16.0.6;bas;NYC test;Test NYC environment
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            path = Path(f.name)

        manager = SwitchManager()
        manager.load_csv(str(path))
        path.unlink()
        return manager

    def test_filter_empty_terms(self, manager_with_data: SwitchManager) -> None:
        """Test filtering with empty search terms returns all switches."""
        result = manager_with_data.filter([])
        assert len(result) == 5
        assert result == manager_with_data.all_switches

    def test_filter_or_mode_single_term(self, manager_with_data: SwitchManager) -> None:
        """Test OR mode filtering with single term."""
        result = manager_with_data.filter(["prod"])
        assert len(result) == 2  # sw001, sw004 (both have "prod" in name or comment)
        names = [sw.name for sw in result]
        assert "sw001-lx-prod" in names
        assert "sw003-lx-backup" not in names
        assert "sw004-ny-prod" in names

    def test_filter_or_mode_multiple_terms(self, manager_with_data: SwitchManager) -> None:
        """Test OR mode: match ANY term."""
        # Should match switches with "rum" OR "test"
        result = manager_with_data.filter(["rum", "test"])

        # rum: sw001, sw003, sw004 (3 switches)
        # test: sw002, sw005 (2 switches)
        # Total: 5 switches (all have either rum or test)
        assert len(result) == 5

    def test_filter_and_mode_single_term(self, manager_with_data: SwitchManager) -> None:
        """Test AND mode filtering with single term."""
        manager_with_data._search_mode = SearchMode.AND
        result = manager_with_data.filter(["prod"])
        assert len(result) == 2  # sw001, sw004 have "prod"

    def test_filter_and_mode_multiple_terms(self, manager_with_data: SwitchManager) -> None:
        """Test AND mode: match ALL terms."""
        manager_with_data._search_mode = SearchMode.AND

        # Should match switches with "rum" AND "prod"
        result = manager_with_data.filter(["rum", "prod"])

        # Only sw001 and sw004 have both "rum" subnet AND "prod" in name
        assert len(result) == 2
        names = [sw.name for sw in result]
        assert "sw001-lx-prod" in names
        assert "sw004-ny-prod" in names

    def test_filter_and_mode_no_matches(self, manager_with_data: SwitchManager) -> None:
        """Test AND mode with terms that don't appear together."""
        manager_with_data._search_mode = SearchMode.AND
        result = manager_with_data.filter(["test", "prod"])

        # No switch has both "test" and "prod"
        assert len(result) == 0

    def test_filter_by_ip(self, manager_with_data: SwitchManager) -> None:
        """Test filtering by IP address."""
        result = manager_with_data.filter(["192.168"])
        assert len(result) == 2  # sw001 and sw002

    def test_filter_by_subnet(self, manager_with_data: SwitchManager) -> None:
        """Test filtering by subnet."""
        result = manager_with_data.filter(["rum"])
        assert len(result) == 3  # sw001, sw003, sw004

    def test_filter_case_insensitive(self, manager_with_data: SwitchManager) -> None:
        """Test filtering is case-insensitive."""
        result1 = manager_with_data.filter(["PROD"])
        result2 = manager_with_data.filter(["prod"])
        result3 = manager_with_data.filter(["PrOd"])

        assert len(result1) == len(result2) == len(result3)
        assert set(sw.name for sw in result1) == set(sw.name for sw in result2)


class TestSort:
    """Test sorting functionality."""

    @pytest.fixture
    def manager_with_data(self) -> SwitchManager:
        """Create a SwitchManager with test data for sorting."""
        content = """Name;IP;subnet;aliases;comment
sw003;192.168.1.3;bas;Switch 3;Comment C
sw001;192.168.1.1;rum;Switch 1;Comment A
sw002;192.168.1.2;bas;Switch 2;Comment B
sw004;10.0.0.1;rum;Switch 4;Comment D
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            path = Path(f.name)

        manager = SwitchManager()
        manager.load_csv(str(path))
        path.unlink()
        return manager

    def test_sort_by_name_ascending(self, manager_with_data: SwitchManager) -> None:
        """Test sorting by name in ascending order."""
        result = manager_with_data.sort("name")
        names = [sw.name for sw in result]
        assert names == ["sw001", "sw002", "sw003", "sw004"]
        assert manager_with_data.sort_state.column == "name"
        assert manager_with_data.sort_state.ascending is True

    def test_sort_by_name_toggle(self, manager_with_data: SwitchManager) -> None:
        """Test toggling sort order on same column."""
        # First sort: ascending
        manager_with_data.sort("name")
        assert manager_with_data.sort_state.ascending is True

        # Second sort: descending (toggle)
        result = manager_with_data.sort("name", toggle=True)
        names = [sw.name for sw in result]
        assert names == ["sw004", "sw003", "sw002", "sw001"]
        assert manager_with_data.sort_state.ascending is False

        # Third sort: ascending again (toggle)
        result = manager_with_data.sort("name", toggle=True)
        names = [sw.name for sw in result]
        assert names == ["sw001", "sw002", "sw003", "sw004"]
        assert manager_with_data.sort_state.ascending is True

    def test_sort_by_ip(self, manager_with_data: SwitchManager) -> None:
        """Test sorting by IP address."""
        result = manager_with_data.sort("ip")
        ips = [sw.ip for sw in result]
        # Note: IP sorting is lexicographic, not numeric
        assert ips == ["10.0.0.1", "192.168.1.1", "192.168.1.2", "192.168.1.3"]

    def test_sort_by_subnet(self, manager_with_data: SwitchManager) -> None:
        """Test sorting by subnet."""
        result = manager_with_data.sort("subnet")
        subnets = [sw.subnet for sw in result]
        # bas appears twice, rum appears twice
        assert subnets[0] == "bas"
        assert subnets[-1] == "rum"

    def test_sort_by_comment(self, manager_with_data: SwitchManager) -> None:
        """Test sorting by comment."""
        result = manager_with_data.sort("comment")
        comments = [sw.comment for sw in result]
        assert comments == ["Comment A", "Comment B", "Comment C", "Comment D"]

    def test_sort_case_insensitive(self) -> None:
        """Test that sorting is case-insensitive."""
        content = """Name;IP;subnet;aliases;comment
Charlie;192.168.1.1;main;C;C
alice;192.168.1.2;main;A;A
Bob;192.168.1.3;main;B;B
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            path = Path(f.name)

        manager = SwitchManager()
        manager.load_csv(str(path))
        path.unlink()

        result = manager.sort("name")
        names = [sw.name for sw in result]
        assert names == ["alice", "Bob", "Charlie"]

    def test_sort_different_column_resets_ascending(self, manager_with_data: SwitchManager) -> None:
        """Test that sorting a different column resets to ascending."""
        # Sort by name descending
        manager_with_data.sort("name")
        manager_with_data.sort("name", toggle=True)
        assert manager_with_data.sort_state.ascending is False

        # Sort by different column should reset to ascending
        manager_with_data.sort("ip")
        assert manager_with_data.sort_state.column == "ip"
        assert manager_with_data.sort_state.ascending is True

    def test_sort_invalid_column(self, manager_with_data: SwitchManager) -> None:
        """Test sorting by invalid column name (should return unchanged)."""
        original = manager_with_data.filtered_switches.copy()
        result = manager_with_data.sort("invalid_column")
        assert result == original

    def test_filter_preserves_sort(self, manager_with_data: SwitchManager) -> None:
        """Test that filtering preserves the current sort order."""
        # First sort by name
        manager_with_data.sort("name")

        # Then filter
        result = manager_with_data.filter(["bas"])

        # Should still be sorted by name
        names = [sw.name for sw in result]
        assert names == sorted(names)


class TestSearchHistory:
    """Test search history functionality."""

    def test_add_to_history(self) -> None:
        """Test adding searches to history."""
        manager = SwitchManager()

        manager.add_to_history("prod")
        assert manager.search_history == ["prod"]

        manager.add_to_history("test")
        assert manager.search_history == ["prod", "test"]

    def test_add_empty_string_ignored(self) -> None:
        """Test that empty strings are not added to history."""
        manager = SwitchManager()

        manager.add_to_history("")
        assert manager.search_history == []

        manager.add_to_history("   ")
        assert manager.search_history == []

    def test_duplicate_consecutive_ignored(self) -> None:
        """Test that duplicate consecutive searches are ignored."""
        manager = SwitchManager()

        manager.add_to_history("prod")
        manager.add_to_history("prod")
        assert manager.search_history == ["prod"]

        manager.add_to_history("test")
        manager.add_to_history("prod")  # Different from last, should be added
        assert manager.search_history == ["prod", "test", "prod"]

    def test_history_max_20_items(self) -> None:
        """Test that history maintains maximum of 20 items."""
        manager = SwitchManager()

        # Add 25 searches
        for i in range(25):
            manager.add_to_history(f"search{i}")

        # Should only keep last 20
        assert len(manager.search_history) == 20
        assert manager.search_history[0] == "search5"
        assert manager.search_history[-1] == "search24"

    def test_get_recent_history(self) -> None:
        """Test getting recent history in reverse chronological order."""
        manager = SwitchManager()

        manager.add_to_history("first")
        manager.add_to_history("second")
        manager.add_to_history("third")

        recent = manager.get_recent_history(limit=2)
        assert recent == ["third", "second"]  # Newest first

    def test_get_recent_history_more_than_available(self) -> None:
        """Test getting more history items than available."""
        manager = SwitchManager()

        manager.add_to_history("first")
        manager.add_to_history("second")

        recent = manager.get_recent_history(limit=10)
        assert recent == ["second", "first"]


class TestSearchMode:
    """Test search mode toggling."""

    def test_toggle_search_mode(self) -> None:
        """Test toggling search mode."""
        manager = SwitchManager()

        assert manager.search_mode == SearchMode.OR

        mode = manager.toggle_search_mode()
        assert mode == SearchMode.AND
        assert manager.search_mode == SearchMode.AND

        mode = manager.toggle_search_mode()
        assert mode == SearchMode.OR
        assert manager.search_mode == SearchMode.OR
