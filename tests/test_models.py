"""Unit tests for Switch data model."""

import pytest

from switch_manager.models import Switch, SearchMode, CommandType, COMMANDS


class TestSwitch:
    """Test the Switch dataclass and its methods."""

    @pytest.fixture
    def sample_switch(self) -> Switch:
        """Create a sample switch for testing."""
        return Switch(
            name="sw001-lx-prod",
            ip="192.168.10.1",
            subnet="rum",
            aliases="Main switch,Core",
            comment="Production core switch"
        )

    def test_switch_creation(self, sample_switch: Switch) -> None:
        """Test creating a Switch instance."""
        assert sample_switch.name == "sw001-lx-prod"
        assert sample_switch.ip == "192.168.10.1"
        assert sample_switch.subnet == "rum"
        assert sample_switch.aliases == "Main switch,Core"
        assert sample_switch.comment == "Production core switch"

    def test_switch_is_frozen(self, sample_switch: Switch) -> None:
        """Test that Switch is immutable (frozen dataclass)."""
        with pytest.raises(AttributeError):
            sample_switch.name = "new-name"  # type: ignore

    def test_matches_term_exact_name(self, sample_switch: Switch) -> None:
        """Test exact match in name field."""
        assert sample_switch.matches_term("sw001-lx-prod")

    def test_matches_term_partial_name(self, sample_switch: Switch) -> None:
        """Test partial match in name field."""
        assert sample_switch.matches_term("sw001")
        assert sample_switch.matches_term("lx-prod")
        assert sample_switch.matches_term("001")

    def test_matches_term_ip_address(self, sample_switch: Switch) -> None:
        """Test matching IP address."""
        assert sample_switch.matches_term("192.168.10.1")
        assert sample_switch.matches_term("192.168")
        assert sample_switch.matches_term("10.1")

    def test_matches_term_subnet(self, sample_switch: Switch) -> None:
        """Test matching subnet field."""
        assert sample_switch.matches_term("rum")

    def test_matches_term_aliases(self, sample_switch: Switch) -> None:
        """Test matching aliases field."""
        assert sample_switch.matches_term("Main switch")
        assert sample_switch.matches_term("Core")
        assert sample_switch.matches_term("Main")

    def test_matches_term_comment(self, sample_switch: Switch) -> None:
        """Test matching comment field."""
        assert sample_switch.matches_term("Production")
        assert sample_switch.matches_term("core switch")
        assert sample_switch.matches_term("Production core")

    def test_matches_term_case_insensitive(self, sample_switch: Switch) -> None:
        """Test that matching is case-insensitive."""
        assert sample_switch.matches_term("SW001")
        assert sample_switch.matches_term("PROD")
        assert sample_switch.matches_term("RUM")
        assert sample_switch.matches_term("CORE")
        assert sample_switch.matches_term("production CORE switch")

    def test_matches_term_no_match(self, sample_switch: Switch) -> None:
        """Test terms that should not match."""
        assert not sample_switch.matches_term("sw002")
        assert not sample_switch.matches_term("test")
        assert not sample_switch.matches_term("backup")
        assert not sample_switch.matches_term("nonexistent")

    def test_matches_term_empty_string(self, sample_switch: Switch) -> None:
        """Test matching empty string (should match as empty is in all strings)."""
        assert sample_switch.matches_term("")

    def test_matches_term_whitespace(self, sample_switch: Switch) -> None:
        """Test matching whitespace."""
        # Space is present in "Main switch" and other fields
        assert sample_switch.matches_term(" ")

    def test_matches_term_special_characters(self) -> None:
        """Test matching terms with special characters."""
        switch = Switch(
            name="sw-001",
            ip="10.0.0.1",
            subnet="net-1",
            aliases="test_alias",
            comment="Switch #1"
        )
        assert switch.matches_term("-001")
        assert switch.matches_term("test_")
        assert switch.matches_term("#1")

    def test_switch_with_empty_fields(self) -> None:
        """Test switch with empty fields."""
        switch = Switch(
            name="sw001",
            ip="192.168.1.1",
            subnet="",
            aliases="",
            comment=""
        )
        assert switch.matches_term("sw001")
        assert switch.matches_term("192.168.1.1")
        assert not switch.matches_term("test")  # No match in empty fields


class TestSearchMode:
    """Test SearchMode enum."""

    def test_search_mode_values(self) -> None:
        """Test SearchMode enum values."""
        assert SearchMode.OR.value == "OR"
        assert SearchMode.AND.value == "AND"

    def test_search_mode_members(self) -> None:
        """Test SearchMode has exactly two members."""
        assert len(SearchMode) == 2
        assert SearchMode.OR in SearchMode
        assert SearchMode.AND in SearchMode


class TestCommandType:
    """Test CommandType enum."""

    def test_command_type_values(self) -> None:
        """Test CommandType enum values."""
        assert CommandType.SSH.value == 1
        assert CommandType.PING.value == 2
        assert CommandType.TRACEROUTE.value == 3
        assert CommandType.BATCH_PING.value == 4
        assert CommandType.TMUX.value == 5
        assert CommandType.DETAILS.value == 6
        assert CommandType.HELP.value == 7
        assert CommandType.EXIT.value == 8

    def test_command_type_members(self) -> None:
        """Test CommandType has exactly eight members."""
        assert len(CommandType) == 8


class TestCommands:
    """Test COMMANDS list and Command dataclass."""

    def test_commands_list_length(self) -> None:
        """Test COMMANDS list has 8 commands."""
        assert len(COMMANDS) == 8

    def test_commands_sequential_numbers(self) -> None:
        """Test commands have sequential numbers 1-8."""
        numbers = [cmd.number for cmd in COMMANDS]
        assert numbers == list(range(1, 9))

    def test_commands_unique_types(self) -> None:
        """Test each command has unique type."""
        types = [cmd.type for cmd in COMMANDS]
        assert len(types) == len(set(types))

    def test_network_commands(self) -> None:
        """Test network commands category."""
        network_cmds = [cmd for cmd in COMMANDS if cmd.category == "NETWORK"]
        assert len(network_cmds) == 5
        assert all(cmd.number <= 5 for cmd in network_cmds)

    def test_system_commands(self) -> None:
        """Test system commands category."""
        system_cmds = [cmd for cmd in COMMANDS if cmd.category == "SYSTEM"]
        assert len(system_cmds) == 3
        assert all(cmd.number >= 6 for cmd in system_cmds)

    def test_commands_requiring_confirmation(self) -> None:
        """Test commands that require confirmation."""
        confirmed = [cmd for cmd in COMMANDS if cmd.requires_confirmation]
        # Batch ping, TMUX, and Exit require confirmation
        assert len(confirmed) == 3
        assert CommandType.BATCH_PING in [cmd.type for cmd in confirmed]
        assert CommandType.TMUX in [cmd.type for cmd in confirmed]
        assert CommandType.EXIT in [cmd.type for cmd in confirmed]

    def test_commands_requiring_selection(self) -> None:
        """Test commands that require switch selection."""
        requires_selection = [cmd for cmd in COMMANDS if cmd.requires_selection]
        # SSH, Ping, Traceroute, Details require selection
        assert len(requires_selection) == 4
        assert CommandType.SSH in [cmd.type for cmd in requires_selection]
        assert CommandType.PING in [cmd.type for cmd in requires_selection]
        assert CommandType.TRACEROUTE in [cmd.type for cmd in requires_selection]
        assert CommandType.DETAILS in [cmd.type for cmd in requires_selection]
