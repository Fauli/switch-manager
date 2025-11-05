# V-Li Switch Manager - Architecture Document

## Executive Summary

This document outlines the recommended architecture for building the V-Li Switch Manager TUI application in Python. The architecture leverages modern Python patterns with a focus on maintainability, performance, and user experience.

## Technology Stack

### Core Framework: Textual

**Textual** is the recommended TUI framework for this application.

**Why Textual?**
- **Async-first design**: Native `asyncio` support perfect for streaming operations (ping, traceroute) and batch commands
- **Built-in widgets**: DataTable, Input, Modal screens, containers - exactly what we need
- **Superior focus management**: Critical for the modal-heavy workflow; handles focus restoration automatically
- **Reactive CSS-like styling**: Clean separation of appearance and logic
- **Rich text rendering**: Built on the Rich library for beautiful terminal output
- **Active development**: Modern codebase with excellent documentation
- **Event system**: Sophisticated keyboard binding and event handling

**Installation**: `pip install textual`

### Data Handling

**Python csv module + dataclasses**
- Standard library `csv` module is sufficient for parsing CSV files
- `dataclasses` for type-safe, immutable switch records
- No need for Pandas (would add unnecessary dependency for simple tabular data)

### Command Execution

**asyncio.subprocess**
- Non-blocking subprocess execution
- Perfect for streaming command output line-by-line
- Enables parallel batch operations
- Integrates seamlessly with Textual's async architecture

### TMUX Integration

**libtmux library**
- Pythonic API for TMUX control
- Programmatic session, window, and pane management
- Superior to shell command execution for complex TMUX operations
- Type-safe interface

**Installation**: `pip install libtmux`

### Additional Dependencies

- **ipaddress** (stdlib): IP address validation
- **re** (stdlib): Username and pattern validation
- **shlex** (stdlib): Safe command argument escaping
- **platform** (stdlib): OS detection for platform-specific terminal spawning

## Architecture Pattern

### Screen-Based Architecture

Textual uses a screen-based architecture where each major view is a `Screen` object. Screens can be pushed onto a stack (for modals) or swapped (for main views).

```
SwitchManagerApp (App)
│
├── MainScreen (Screen) ──────────────────┐
│   │                                      │
│   ├── Header (Static widget)            │ Main Interface
│   ├── CommandBar (Custom widget)        │ (Always visible base)
│   ├── SearchHelpBar (Static widget)     │
│   ├── SearchInput (Input widget)        │
│   ├── ResultCounter (Static widget)     │
│   ├── SwitchTable (DataTable widget)    │
│   ├── ShortcutsBar (Static widget)      │
│   └── StatusBar (Custom widget)         │
│                                          │
└── Modal Screens ─────────────────────────┘
    │
    ├── OutputModal (base class)
    │   ├── DetailsModal
    │   └── HelpModal
    │
    ├── StreamingModal (base class)
    │   ├── PingModal
    │   ├── TracerouteModal
    │   └── BatchPingModal
    │
    └── ConfirmationModal (base class)
        ├── ExitConfirmation
        ├── BatchPingConfirmation
        └── TmuxConfirmation
```

### Component Hierarchy

**Application Layer**
- `SwitchManagerApp`: Main app class, orchestrates screens and global state
- Manages app-level keybindings
- Handles environment variable configuration

**Screen Layer**
- `MainScreen`: Primary interface with all core widgets
- Modal screens: Temporary overlays that take focus

**Widget Layer**
- Custom widgets: CommandBar, StatusBar
- Built-in widgets: DataTable, Input, Static

**Business Logic Layer**
- `SwitchManager`: Manages switch data, filtering, sorting
- `CommandExecutor`: Handles command execution and validation
- Data models: `Switch`, `Command`, `SearchMode`

## Core Components

### 1. Data Models

```python
# models.py

from dataclasses import dataclass
from enum import Enum
from typing import Optional

@dataclass(frozen=True)
class Switch:
    """Immutable switch record from CSV."""
    name: str
    ip: str
    subnet: str
    aliases: str
    comment: str

    def matches_term(self, term: str) -> bool:
        """Case-insensitive search across all fields."""
        term_lower = term.lower()
        return any(
            term_lower in field.lower()
            for field in [self.name, self.ip, self.subnet,
                         self.aliases, self.comment]
        )

class SearchMode(Enum):
    """Search mode enumeration."""
    OR = "OR"
    AND = "AND"

class CommandType(Enum):
    """Available commands."""
    SSH = 1
    PING = 2
    TRACEROUTE = 3
    BATCH_PING = 4
    TMUX = 5
    DETAILS = 6
    HELP = 7
    EXIT = 8

@dataclass
class Command:
    """Command metadata."""
    type: CommandType
    number: int
    name: str
    category: str  # "NETWORK" or "SYSTEM"
    requires_confirmation: bool
    requires_selection: bool
```

### 2. State Management

**SwitchManager** (Singleton or passed via dependency injection)

```python
# manager.py

class SwitchManager:
    """Manages switch data and filtering logic."""

    def __init__(self):
        self._all_switches: list[Switch] = []
        self._filtered_switches: list[Switch] = []
        self._search_history: list[str] = []
        self._search_mode: SearchMode = SearchMode.OR
        self._current_sort: Optional[tuple[str, bool]] = None  # (column, ascending)

    def load_csv(self, filepath: str, delimiter: str) -> None:
        """Load switches from CSV file."""
        # Parse CSV, create Switch objects
        # Update _all_switches and _filtered_switches

    def filter(self, search_terms: list[str]) -> list[Switch]:
        """Filter switches based on search terms and mode."""
        if not search_terms:
            return self._all_switches

        if self._search_mode == SearchMode.OR:
            return [s for s in self._all_switches
                   if any(s.matches_term(term) for term in search_terms)]
        else:  # AND mode
            return [s for s in self._all_switches
                   if all(s.matches_term(term) for term in search_terms)]

    def sort(self, column: str, ascending: bool = True) -> list[Switch]:
        """Sort filtered switches by column."""
        # Sort _filtered_switches by specified column

    def add_to_history(self, search_term: str) -> None:
        """Add search term to history (max 20 items)."""
        # Append to _search_history, maintain max size
```

**Advantages of this approach:**
- Single source of truth for switch data
- Separation of business logic from UI
- Easy to test without UI components
- Reactive: UI observes state changes and re-renders

### 3. Main Screen

**MainScreen** contains all primary UI elements and orchestrates user interactions.

```python
# screens/main_screen.py

from textual.screen import Screen
from textual.widgets import DataTable, Input, Static
from textual.reactive import reactive

class MainScreen(Screen):
    """Main application screen."""

    # Reactive properties - auto-update UI when changed
    filtered_switches = reactive(list)
    selected_command = reactive(CommandType.SSH)
    search_text = reactive("")

    def compose(self):
        """Build the UI layout."""
        yield Static("V-Li: Switch Manager", id="title")
        yield CommandBar()
        yield Static("🔍 Search [OR mode] - Ctrl+L: Toggle | Ctrl+H: History | ESC: Clear",
                    id="search-help")
        yield Input(placeholder="Search... (OR mode)", id="search-input")
        yield Static(id="result-counter")
        yield DataTable(id="switch-table")
        yield Static("F1-F5:Sort | 1-8:Cmd | ↑↓:Nav | ←→:Cmd | Enter:Exec | Ctrl+L:Mode | ?:Help",
                    id="shortcuts")
        yield StatusBar()

    def on_mount(self):
        """Initialize after mounting."""
        self.setup_table()
        self.load_data()

    async def load_data(self):
        """Async CSV loading."""
        # Show loading message
        await self.manager.load_csv_async(...)
        self.refresh_table()

    def on_key(self, event):
        """Global keyboard handler."""
        # Handle F1-F5 for sorting
        # Handle 1-8 for command selection
        # Handle arrow keys for navigation
        # etc.

    def on_input_changed(self, event):
        """Search input changed - filter in real-time."""
        terms = event.value.split()
        self.filtered_switches = self.manager.filter(terms)
        self.refresh_table()
```

**Key features:**
- Uses Textual's reactive properties for automatic UI updates
- `compose()` method defines widget hierarchy
- `on_mount()` for async initialization
- Event handlers for keyboard and widget events

### 4. Modal System

**Base Modal Classes**

```python
# screens/modals.py

class BaseModal(Screen):
    """Base class for all modals."""

    def on_mount(self):
        """Take focus when modal opens."""
        # Textual handles focus automatically

    def close(self):
        """Close modal and return focus to main screen."""
        self.app.pop_screen()

class OutputModal(BaseModal):
    """Modal for displaying static output."""

    def __init__(self, title: str, content: str):
        super().__init__()
        self.title = title
        self.content = content

    def compose(self):
        yield Static(self.title, id="modal-title")
        yield Static(self.content, id="modal-content")

    def on_key(self, event):
        if event.key == "escape":
            self.close()

class StreamingModal(BaseModal):
    """Modal for displaying live command output."""

    def __init__(self, command: str, args: list[str]):
        super().__init__()
        self.command = command
        self.args = args

    async def on_mount(self):
        """Start streaming command output."""
        output_widget = self.query_one("#output")

        # Start subprocess
        process = await asyncio.create_subprocess_exec(
            self.command, *self.args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        # Stream output line by line
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            output_widget.update(output_widget.renderable + line.decode())

        await process.wait()
```

**Modal Lifecycle:**
1. User triggers command → `app.push_screen(ModalScreen())`
2. Modal takes focus (automatic)
3. User interacts with modal (ESC, y/n, etc.)
4. Modal closes → `app.pop_screen()`
5. Focus returns to MainScreen (automatic)

### 5. Command Execution System

**CommandExecutor** handles validation and execution of all commands.

```python
# commands/executor.py

class CommandExecutor:
    """Executes commands with validation."""

    def __init__(self, app, config):
        self.app = app
        self.config = config

    async def execute(self, command: CommandType, switch: Switch = None,
                     switches: list[Switch] = None):
        """Execute a command with proper validation."""

        # Validate inputs
        if command in [CommandType.SSH, CommandType.PING, CommandType.TRACEROUTE]:
            if not switch:
                return  # No switch selected
            if not self._validate_ip(switch.ip):
                await self._show_error("Invalid IP address")
                return

        # Route to appropriate handler
        if command == CommandType.SSH:
            await self._execute_ssh(switch)
        elif command == CommandType.PING:
            await self._execute_ping(switch)
        elif command == CommandType.BATCH_PING:
            await self._execute_batch_ping(switches)
        # ... etc

    async def _execute_ssh(self, switch: Switch):
        """Open SSH in new terminal."""
        username = self.config.sm_user
        if not self._validate_username(username):
            await self._show_error("Invalid username")
            return

        # Platform-specific terminal spawning
        if sys.platform == "darwin":
            cmd = ["open", "-a", "Terminal.app",
                  f"ssh {username}@{switch.ip}"]
        elif sys.platform == "linux":
            cmd = ["xterm", "-e", f"ssh {username}@{switch.ip}"]
        # ... etc

        subprocess.Popen(cmd)  # Non-blocking
        self.app.update_status("✓ SSH opened")

    async def _execute_ping(self, switch: Switch):
        """Show streaming ping modal."""
        modal = PingModal(switch.ip)
        await self.app.push_screen(modal)

    @staticmethod
    def _validate_ip(ip: str) -> bool:
        """Validate IP address using ipaddress module."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def _validate_username(username: str) -> bool:
        """Validate username contains only safe characters."""
        return bool(re.match(r'^[a-zA-Z0-9._-]+$', username))
```

**Security considerations:**
- IP validation using `ipaddress` module (prevents injection)
- Username validation using regex (alphanumeric + dot/dash/underscore only)
- Command execution uses argument lists, never shell strings
- `shlex.quote()` for any user-provided strings in commands

### 6. TMUX Integration

```python
# commands/tmux_handler.py

import libtmux

class TmuxHandler:
    """Handles TMUX session creation."""

    def __init__(self, config):
        self.config = config
        self.server = libtmux.Server()

    def create_sync_session(self, switches: list[Switch]) -> None:
        """Create synchronized TMUX session for multiple switches."""

        # Create new session
        session = self.server.new_session(
            session_name="vli-switches",
            kill_session=True,  # Kill existing if present
            attach=False
        )

        # Get first window
        window = session.attached_window
        window.rename_window("ssh")

        # Create panes for each switch
        panes = [window.attached_pane]  # First pane already exists

        for switch in switches[1:]:
            pane = window.split_window()
            panes.append(pane)

        # SSH into each switch
        username = self.config.sm_user
        for pane, switch in zip(panes, switches):
            pane.send_keys(f"ssh {username}@{switch.ip}")

        # Enable synchronized panes
        window.select_layout("tiled")
        window.set_window_option("synchronize-panes", "on")

        # Attach to session (will exit Python app)
        session.attach_session()
```

## Data Flow

### Application Startup

```
1. Load environment variables (SM_CSV_DATA, SM_DELIMITER, SM_USER)
2. Initialize SwitchManagerApp
3. Push MainScreen onto screen stack
4. MainScreen.on_mount():
   a. Display "Loading..." message
   b. Async load CSV file
   c. Populate SwitchManager with data
   d. Render table with all switches
   e. Focus on DataTable
5. Ready for user input
```

### Search Flow

```
User types 'c' → 'o' → 'r' → 'e'
    ↓
MainScreen.on_key() detects printable char
    ↓
Focus moves to SearchInput (if not already focused)
    ↓
SearchInput.on_changed() fires
    ↓
Extract search terms: ['core']
    ↓
SwitchManager.filter(terms) → filtered list
    ↓
MainScreen.refresh_table() → Update DataTable
    ↓
Update result counter: "Showing 12 of 56 switches"
```

### Command Execution Flow

```
User presses '2' (ping command)
    ↓
MainScreen.on_key() detects '2'
    ↓
Update selected_command to PING
    ↓
CommandBar re-renders with PING highlighted
    ↓
StatusBar updates: [ping]
    ↓
User presses ENTER
    ↓
MainScreen.on_key() detects 'enter'
    ↓
Get currently selected switch from DataTable
    ↓
CommandExecutor.execute(PING, switch)
    ↓
Create PingModal(switch.ip)
    ↓
app.push_screen(modal) → Modal takes focus
    ↓
PingModal.on_mount() → Start subprocess
    ↓
Stream output to modal widget
    ↓
User presses ESC
    ↓
Modal.close() → app.pop_screen()
    ↓
Focus returns to MainScreen DataTable
```

### Modal Lifecycle

```
MainScreen active, user has focus
    ↓
Command requires modal (e.g., ping)
    ↓
app.push_screen(PingModal)
    ↓
Screen stack: [MainScreen, PingModal]
    ↓
Textual automatically:
    - Blurs MainScreen
    - Focuses PingModal
    - Renders modal on top
    ↓
User interacts with modal only
    ↓
Modal closes: app.pop_screen()
    ↓
Screen stack: [MainScreen]
    ↓
Textual automatically:
    - Focuses MainScreen
    - Removes modal rendering
    - MainScreen becomes interactive
```

## Implementation Strategy

### Phase 1: Foundation (Week 1)

**Goal**: Basic UI and data loading

- [ ] Project setup (poetry/pip, directory structure)
- [ ] Data models (Switch, Command, SearchMode)
- [ ] Config loading (environment variables)
- [ ] SwitchManager (load CSV, basic filtering)
- [ ] MainScreen layout (header, table, status bar)
- [ ] DataTable population from CSV
- [ ] Basic keyboard navigation (↑↓)

**Deliverable**: App that loads CSV and displays switches in a table

### Phase 2: Search and Sort (Week 2)

**Goal**: Interactive filtering and sorting

- [ ] SearchInput integration
- [ ] Real-time filtering (OR mode)
- [ ] AND mode toggle (Ctrl+L)
- [ ] Result counter updates
- [ ] Column sorting (F1-F5)
- [ ] Sort indicators (↑↓)
- [ ] Search history storage
- [ ] Search history modal (Ctrl+H)

**Deliverable**: Fully functional search and sort system

### Phase 3: Basic Commands (Week 3)

**Goal**: Simple command execution

- [ ] Command selection (1-8, ←→)
- [ ] CommandBar widget with highlighting
- [ ] Details modal (static output)
- [ ] Help modal (static output)
- [ ] Exit confirmation modal
- [ ] Modal lifecycle working correctly
- [ ] Focus management validation

**Deliverable**: Non-network commands working

### Phase 4: Network Commands (Week 4)

**Goal**: SSH and streaming commands

- [ ] SSH validation (IP, username)
- [ ] Platform-specific terminal spawning
- [ ] Ping modal with streaming output
- [ ] Traceroute modal with streaming output
- [ ] CommandExecutor with validation
- [ ] Error handling and status updates

**Deliverable**: Individual network commands working

### Phase 5: Batch Operations (Week 5)

**Goal**: Multi-switch operations

- [ ] Batch ping confirmation dialog
- [ ] Parallel ping execution
- [ ] Aggregated results display
- [ ] TMUX session creation (libtmux)
- [ ] Synchronized panes setup
- [ ] TMUX confirmation dialog

**Deliverable**: All commands implemented

### Phase 6: Polish and Testing (Week 6)

**Goal**: Production-ready quality

- [ ] Comprehensive input validation
- [ ] Error handling for all edge cases
- [ ] Status bar updates for all operations
- [ ] Performance testing (10k+ rows)
- [ ] Unit tests for business logic
- [ ] Integration tests for commands
- [ ] Documentation and README
- [ ] Command injection security audit

**Deliverable**: Production-ready application

## Security Considerations

### Input Validation

**IP Address Validation**
```python
import ipaddress

def validate_ip(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False
```

**Username Validation**
```python
import re

def validate_username(username: str) -> bool:
    # Only allow: alphanumeric, dot, dash, underscore
    return bool(re.match(r'^[a-zA-Z0-9._-]+$', username))
```

### Command Injection Prevention

**NEVER use shell=True:**
```python
# ❌ VULNERABLE - DO NOT DO THIS
subprocess.run(f"ping {ip}", shell=True)

# ✅ SAFE - Use argument list
subprocess.run(["ping", "-c", "4", ip])
```

**Use shlex.quote() for complex commands:**
```python
import shlex

# ✅ SAFE - Quote user input
username = shlex.quote(config.sm_user)
ip = shlex.quote(switch.ip)
cmd = ["ssh", f"{username}@{ip}"]
```

### Environment Variable Handling

```python
# config.py

import os
from dataclasses import dataclass

@dataclass
class Config:
    sm_user: str
    sm_csv_data: str = "data.csv"
    sm_delimiter: str = ";"
    sm_debug: bool = False

    @classmethod
    def from_env(cls):
        sm_user = os.getenv("SM_USER")
        if not sm_user:
            raise ValueError("SM_USER environment variable is required")

        return cls(
            sm_user=sm_user,
            sm_csv_data=os.getenv("SM_CSV_DATA", "data.csv"),
            sm_delimiter=os.getenv("SM_DELIMITER", ";"),
            sm_debug=os.getenv("SM_DEBUG", "false").lower() == "true"
        )
```

### CSV Injection Prevention

While the app is read-only for CSV, be aware of CSV injection if future versions support editing:
- Sanitize cells starting with `=`, `+`, `@`, `-`
- Warn users about untrusted CSV sources

## File Structure

```
switch-manager/
├── README.md
├── pyproject.toml           # Poetry dependencies
├── requirements.txt         # Pip dependencies
├── .env.example            # Example environment variables
│
├── switch_manager/
│   ├── __init__.py
│   ├── __main__.py         # Entry point: python -m switch_manager
│   │
│   ├── app.py              # SwitchManagerApp (main app class)
│   ├── config.py           # Configuration from environment
│   ├── models.py           # Data models (Switch, Command, etc.)
│   ├── manager.py          # SwitchManager (business logic)
│   │
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── main_screen.py      # MainScreen (primary interface)
│   │   └── modals.py           # All modal screens
│   │
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── command_bar.py      # Command selection bar
│   │   ├── status_bar.py       # Status bar at bottom
│   │   └── search_bar.py       # Search help text
│   │
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── executor.py         # CommandExecutor (main orchestrator)
│   │   ├── network.py          # Network command handlers
│   │   ├── system.py           # System command handlers
│   │   └── tmux_handler.py     # TMUX session management
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validation.py       # IP and username validation
│       └── terminal.py         # Platform-specific terminal spawning
│
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_manager.py
│   ├── test_validation.py
│   └── test_commands.py
│
├── data.csv                # Sample data file
└── docs/
    ├── PLAN.md
    └── ARCHITECTURE.md
```

## Testing Approach

### Unit Tests

**Test business logic in isolation:**

```python
# tests/test_manager.py

def test_filter_or_mode():
    manager = SwitchManager()
    manager.load_csv("test_data.csv", ";")

    results = manager.filter(["sw001", "prod"])

    # Should match switches with either "sw001" OR "prod"
    assert len(results) > 0
    assert any("sw001" in s.name for s in results)
    assert any("prod" in s.comment.lower() for s in results)

def test_filter_and_mode():
    manager = SwitchManager()
    manager.set_search_mode(SearchMode.AND)
    manager.load_csv("test_data.csv", ";")

    results = manager.filter(["sw001", "prod"])

    # Should only match switches with both "sw001" AND "prod"
    for switch in results:
        assert "sw001" in switch.name
        assert "prod" in switch.comment.lower()
```

### Integration Tests

**Test command execution (mocked):**

```python
# tests/test_commands.py

@pytest.mark.asyncio
async def test_ssh_command_validation():
    executor = CommandExecutor(mock_app, mock_config)

    invalid_switch = Switch("test", "999.999.999.999", "", "", "")

    # Should not execute with invalid IP
    await executor.execute(CommandType.SSH, invalid_switch)

    # Verify error was shown
    assert mock_app.show_error_called
```

### TUI Testing

**Use Textual's Pilot API for basic UI tests:**

```python
# tests/test_ui.py

from textual.pilot import Pilot

async def test_search_updates_table():
    app = SwitchManagerApp()

    async with app.run_test() as pilot:
        # Type into search
        await pilot.press("c", "o", "r", "e")

        # Verify table updated
        table = app.query_one(DataTable)
        assert table.row_count < original_count
```

**Manual testing required for:**
- Complex keyboard interactions
- Focus management across modals
- Terminal spawning
- TMUX integration

### Performance Testing

**Test with large datasets:**

```python
# tests/test_performance.py

def test_large_csv_loading():
    manager = SwitchManager()

    start = time.time()
    manager.load_csv("10k_switches.csv", ";")
    elapsed = time.time() - start

    assert elapsed < 1.0  # Should load in < 1 second

def test_real_time_filtering():
    manager = SwitchManager()
    manager.load_csv("10k_switches.csv", ";")

    start = time.time()
    results = manager.filter(["core", "switch"])
    elapsed = time.time() - start

    assert elapsed < 0.1  # Should filter in < 100ms
```

## Alternative Approaches Considered

### Urwid

**Pros:**
- Very mature and stable
- Well-tested over many years
- Lots of examples available

**Cons:**
- Callback-based (not async)
- More boilerplate for complex UIs
- Focus management is manual and error-prone
- Modal implementation requires significant custom code
- Older design patterns

**Verdict:** Textual is superior for this modern, async-heavy application

### py_cui

**Pros:**
- Very simple API
- Quick to prototype

**Cons:**
- Limited widget set
- Poor performance with large datasets
- Minimal documentation
- Not suitable for production apps

**Verdict:** Too limited for our requirements

### Rich (without Textual)

**Pros:**
- Beautiful terminal output
- Live rendering capabilities

**Cons:**
- Not a TUI framework
- Would require building entire event system from scratch
- No built-in widgets or layout management
- No focus management

**Verdict:** Textual is built on Rich and provides the TUI layer we need

## Performance Considerations

### CSV Loading

**Async loading to prevent UI freeze:**
```python
async def load_csv_async(self, filepath: str):
    # Show loading indicator
    self.show_loading()

    # Offload to thread pool for CPU-bound work
    switches = await asyncio.to_thread(self._parse_csv, filepath)

    # Update UI on main thread
    self._all_switches = switches
    self.refresh()
```

### Search Filtering

**For datasets > 10,000 rows, consider:**
- Debouncing: Wait 100ms after last keystroke before filtering
- Web Workers equivalent: `asyncio.to_thread()` for CPU-intensive filtering
- Incremental rendering: Only render visible rows (Textual's DataTable does this automatically)

### Table Rendering

Textual's `DataTable` widget:
- Virtual scrolling (only renders visible rows)
- Efficient updates (only re-renders changed cells)
- No action needed from developer

## Deployment

### Package Distribution

**Using Poetry:**
```bash
poetry build
poetry publish
```

**Using pip:**
```bash
pip install switch-manager
```

### Standalone Binary

**Using PyInstaller:**
```bash
pyinstaller --onefile switch_manager/__main__.py
```

Creates single executable for distribution without Python installed.

### Docker Container

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

ENV SM_USER=admin
ENV SM_CSV_DATA=/data/switches.csv

ENTRYPOINT ["python", "-m", "switch_manager"]
```

## Future Enhancements

### Phase 2 Features (Post-MVP)

1. **Custom Commands**: User-defined scripts in config file
2. **Switch Groups**: Save filter presets
3. **Connection History**: Log all SSH/ping/traceroute operations
4. **Export Results**: Filtered results to new CSV
5. **SSH Connection Pooling**: Reuse connections
6. **Auto-refresh**: Periodic connectivity checks
7. **Status Indicators**: Color-coded online/offline status
8. **Multiple CSV Sources**: Merge data from multiple files
9. **Configuration File**: YAML config for commands, colors, etc.
10. **Plugin System**: User-provided Python modules for custom commands

### Technical Debt to Address

- Comprehensive error logging (not just debug mode)
- Internationalization (i18n) support
- Accessibility improvements (screen reader support)
- Mouse support (optional, keyboard remains primary)
- Theme customization (dark/light modes, color schemes)

## Conclusion

This architecture provides a solid foundation for building a maintainable, performant, and user-friendly TUI application. The choice of Textual as the framework, combined with a clear separation of concerns and security-first design, ensures the application will be robust and extensible.

Key success factors:
- ✅ Modern async Python patterns
- ✅ Textual's excellent focus and event management
- ✅ Clear component boundaries
- ✅ Security by design (validation, safe command execution)
- ✅ Testable business logic
- ✅ Phased implementation plan

The architecture supports all requirements from the functional specification while remaining flexible for future enhancements.
