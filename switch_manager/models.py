"""Data models for V-Li Switch Manager."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass(frozen=True)
class Switch:
    """Immutable switch record from CSV.

    Attributes:
        name: Switch hostname/identifier
        ip: IP address (IPv4 or IPv6)
        subnet: Network subnet identifier
        aliases: Alternative names/aliases
        comment: Notes or description
    """
    name: str
    ip: str
    subnet: str
    aliases: str
    comment: str

    def matches_term(self, term: str) -> bool:
        """Check if this switch matches a search term.

        Performs case-insensitive search across all fields.

        Args:
            term: Search term to match

        Returns:
            True if term is found in any field, False otherwise
        """
        term_lower = term.lower()
        return any(
            term_lower in field.lower()
            for field in [self.name, self.ip, self.subnet, self.aliases, self.comment]
        )


class SearchMode(Enum):
    """Search mode for filtering switches.

    OR: Match if ANY search term appears in ANY field
    AND: Match only if ALL search terms appear (each can be in different field)
    """
    OR = "OR"
    AND = "AND"


class CommandType(Enum):
    """Available commands in the application.

    Network commands (1-5):
        SSH: SSH to individual switch
        PING: Ping individual switch
        TRACEROUTE: Traceroute to individual switch
        BATCH_PING: Ping all filtered switches
        TMUX: Open synchronized TMUX session

    System commands (6-8):
        DETAILS: Show all switch details
        HELP: Show help screen
        EXIT: Quit application
    """
    SSH = 1
    PING = 2
    TRACEROUTE = 3
    BATCH_PING = 4
    TMUX = 5
    DETAILS = 6
    HELP = 7
    EXIT = 8


@dataclass(frozen=True)
class Command:
    """Command metadata and configuration.

    Attributes:
        type: CommandType enum value
        number: Command number (1-8)
        name: Display name
        category: "NETWORK" or "SYSTEM"
        requires_confirmation: Whether to show confirmation dialog
        requires_selection: Whether a switch must be selected
    """
    type: CommandType
    number: int
    name: str
    category: str
    requires_confirmation: bool
    requires_selection: bool


# Command definitions
COMMANDS: list[Command] = [
    # Network commands
    Command(CommandType.SSH, 1, "ssh", "NETWORK", False, True),
    Command(CommandType.PING, 2, "ping", "NETWORK", False, True),
    Command(CommandType.TRACEROUTE, 3, "traceroute", "NETWORK", False, True),
    Command(CommandType.BATCH_PING, 4, "batch ping", "NETWORK", True, False),
    Command(CommandType.TMUX, 5, "tmux", "NETWORK", True, False),
    # System commands
    Command(CommandType.DETAILS, 6, "details", "SYSTEM", False, True),
    Command(CommandType.HELP, 7, "help", "SYSTEM", False, False),
    Command(CommandType.EXIT, 8, "exit", "SYSTEM", True, False),
]


@dataclass
class SortState:
    """Current sorting state.

    Attributes:
        column: Column name being sorted (name, ip, subnet, aliases, comment)
        ascending: True for ascending (A→Z), False for descending (Z→A)
    """
    column: Optional[str] = None
    ascending: bool = True
