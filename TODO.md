# V-Li Switch Manager - Development TODO

## Current Status

**Current Phase**: Phase 1 - Foundation
**Last Updated**: 2025-11-05

---

## Phase 1: Foundation (Core UI & Data Loading)

**Goal**: Basic UI and data loading working

### Data Models & Configuration
- [ ] Create `models.py` with data classes
  - [ ] `Switch` dataclass (name, ip, subnet, aliases, comment)
  - [ ] `SearchMode` enum (OR, AND)
  - [ ] `CommandType` enum (SSH, PING, etc.)
  - [ ] `Command` dataclass with metadata
- [ ] Create `config.py` for environment variables
  - [ ] Load SM_USER, SM_CSV_DATA, SM_DELIMITER, SM_DEBUG
  - [ ] Validate required variables (SM_USER)
  - [ ] Provide defaults for optional variables

### Business Logic
- [ ] Create `manager.py` (SwitchManager class)
  - [ ] `load_csv()` method to parse CSV files
  - [ ] `_all_switches` and `_filtered_switches` storage
  - [ ] Basic filter method (prepare for Phase 2)
  - [ ] Handle missing CSV gracefully (empty table)

### Main Application
- [ ] Create `app.py` (SwitchManagerApp class)
  - [ ] Inherit from `textual.app.App`
  - [ ] Initialize SwitchManager
  - [ ] Load configuration on startup
  - [ ] Set up basic app structure

### Main Screen Layout
- [ ] Create `screens/main_screen.py` (MainScreen class)
  - [ ] Header with title "V-Li: Switch Manager"
  - [ ] Placeholder CommandBar (simple Static widget for now)
  - [ ] DataTable widget for switches
  - [ ] Placeholder StatusBar (simple Static widget for now)
  - [ ] Basic CSS styling for layout

### Data Display
- [ ] Populate DataTable with switch data
  - [ ] 5 columns: Name, IP, subnet, aliases, comment
  - [ ] Column headers
  - [ ] Load data from CSV on mount
  - [ ] Show loading message during CSV load
  - [ ] Handle empty data gracefully

### Navigation
- [ ] Implement arrow key navigation
  - [ ] `ë` (Up) - Move selection up
  - [ ] `ì` (Down) - Move selection down
  - [ ] Navigation wraps around (top î bottom)
  - [ ] Visual highlight for selected row

### Entry Point
- [ ] Create `__main__.py` entry point
  - [ ] `main()` function to launch app
  - [ ] Handle Ctrl+C gracefully
  - [ ] Error handling for startup failures

### Testing & Validation
- [ ] Test with sample data.csv
- [ ] Test with missing CSV file
- [ ] Test with large CSV (1000+ rows)
- [ ] Test navigation wrapping
- [ ] Test on macOS terminal

**Phase 1 Deliverable**: App loads CSV and displays switches in navigable table

---

## Phase 2: Search and Sort (Interactive Filtering)

**Goal**: Fully functional search and sort system

### Search Infrastructure
- [ ] Create SearchInput widget integration
  - [ ] Auto-focus on printable character
  - [ ] Real-time filtering as user types
  - [ ] Placeholder text shows current mode
  - [ ] Clear visual indication of focus

### Search Logic
- [ ] Implement `SwitchManager.filter()` method
  - [ ] OR mode: match ANY term in ANY field
  - [ ] AND mode: match ALL terms (each can be in different field)
  - [ ] Case-insensitive search
  - [ ] Tokenize by spaces
  - [ ] Empty search = show all rows

### Search Mode Toggle
- [ ] Implement search mode toggle (Ctrl+L)
  - [ ] Switch between OR and AND modes
  - [ ] Update search help bar text
  - [ ] Update input placeholder
  - [ ] Re-run current search with new mode
  - [ ] Visual indicator of current mode

### Search Bar
- [ ] Create search help bar widget
  - [ ] Show current mode: `[OR mode]` or `[AND mode]`
  - [ ] Show keyboard shortcuts
  - [ ] Update dynamically on mode change

### Result Counter
- [ ] Implement result counter above table
  - [ ] All shown: "Showing all 56 switches"
  - [ ] Filtered: "Showing 12 of 56 switches"
  - [ ] With search: "Showing 12 of 56 switches (filtered by: 'core sw')"
  - [ ] Update in real-time

### Clear Search
- [ ] Implement ESC to clear search
  - [ ] Only when search input has focus
  - [ ] Only when search is not empty
  - [ ] Clear text and show all rows
  - [ ] Return focus to table

### Column Sorting
- [ ] Implement F1-F5 keybindings for sorting
  - [ ] F1: Sort by Name
  - [ ] F2: Sort by IP
  - [ ] F3: Sort by subnet
  - [ ] F4: Sort by Alias
  - [ ] F5: Sort by comment
- [ ] Sorting logic in SwitchManager
  - [ ] First press: ascending (AíZ, 0í9)
  - [ ] Second press: descending (ZíA, 9í0)
  - [ ] Case-insensitive
  - [ ] Track current sort state

### Sort Indicators
- [ ] Visual sort indicators
  - [ ] Column header arrows: `Name ë` or `Name ì`
  - [ ] Status bar indicator: `ë Name` or `ì IP`
  - [ ] Update on sort changes

### Interaction: Search + Sort
- [ ] Sorting applies to filtered results
- [ ] Sort order preserved when searching
- [ ] Selection preserved when filtering/sorting

### Search History
- [ ] Implement search history tracking
  - [ ] Store last 20 searches
  - [ ] Add to history on search execution
  - [ ] Don't duplicate consecutive searches
- [ ] Create SearchHistoryModal
  - [ ] Show last 10 searches
  - [ ] Reverse chronological order
  - [ ] "No history" message if empty
  - [ ] ESC to close
- [ ] Implement Ctrl+H keybinding
  - [ ] Open search history modal
  - [ ] Show searches with numbers

**Phase 2 Deliverable**: Real-time search with OR/AND modes, column sorting, search history

---

## Phase 3: Basic Commands (Simple Command Execution)

**Goal**: Non-network commands working with modal system

### Command Bar Widget
- [ ] Create `widgets/command_bar.py`
  - [ ] Display 8 commands with numbers
  - [ ] Two groups: NETWORK and SYSTEM
  - [ ] Visual separator between groups
  - [ ] Highlight active command
  - [ ] Update on command selection

### Command Selection
- [ ] Implement number key selection (1-8)
  - [ ] Only when search not focused
  - [ ] Highlight selected command
  - [ ] Update status bar
  - [ ] Don't execute automatically
- [ ] Implement arrow key navigation (êí)
  - [ ] Cycle through commands
  - [ ] Wraps around
  - [ ] Visual feedback
- [ ] Implement `?` shortcut
  - [ ] Immediately select and execute help
  - [ ] Only when search not focused

### Status Bar Widget
- [ ] Create `widgets/status_bar.py`
  - [ ] Filter count: `[12/56 switches]` or `[56 switches]`
  - [ ] Sort indicator: `ë Name` (when sorting active)
  - [ ] Active command: `[ssh]`
  - [ ] Last operation result: ` SSH opened` or ` Error`
  - [ ] Update in real-time

### Modal Base Classes
- [ ] Create `screens/modals.py`
  - [ ] `BaseModal` class (common modal behavior)
  - [ ] `OutputModal` class (static content)
  - [ ] `ConfirmationModal` class (yes/no dialogs)
  - [ ] Handle ESC to close
  - [ ] Handle y/n for confirmations
  - [ ] Dim background
  - [ ] Center on screen

### Details Command
- [ ] Implement Details modal (Command 6)
  - [ ] Show all 5 fields for selected switch
  - [ ] Format: "Name: value" per line
  - [ ] Title: "Switch Details"
  - [ ] ESC to close
  - [ ] Return focus to table

### Help Command
- [ ] Implement Help modal (Command 7)
  - [ ] Show ASCII art logo
  - [ ] List all features
  - [ ] List all keyboard shortcuts
  - [ ] Usage tips
  - [ ] ESC to close

### Exit Command
- [ ] Implement Exit confirmation (Command 8)
  - [ ] Show confirmation dialog
  - [ ] "Quit V-Li Switch Manager?"
  - [ ] [y] Yes, [n] No, [ESC] Cancel
  - [ ] Exit on 'y', cancel on 'n' or ESC
  - [ ] Clean shutdown

### Focus Management
- [ ] Validate focus transitions
  - [ ] Modal opens: focus goes to modal
  - [ ] Modal closes: focus returns to table
  - [ ] Never allow focus to be None
  - [ ] Test all modal lifecycle transitions

### Command Execution Infrastructure
- [ ] Create `commands/executor.py` (CommandExecutor)
  - [ ] Main execution orchestrator
  - [ ] Route commands to handlers
  - [ ] Error handling
  - [ ] Status updates

**Phase 3 Deliverable**: Command selection, modals, details/help/exit working

---

## Phase 4: Network Commands (SSH & Streaming)

**Goal**: Individual network commands functional

### Validation Utilities
- [ ] Create `utils/validation.py`
  - [ ] `validate_ip()` using ipaddress module
  - [ ] `validate_username()` using regex
  - [ ] Handle IPv4 and IPv6
  - [ ] Security: reject injection attempts

### Terminal Spawning
- [ ] Create `utils/terminal.py`
  - [ ] Platform detection (Darwin, Linux, Windows)
  - [ ] macOS: Open Terminal.app with SSH command
  - [ ] Linux: Open xterm with SSH command
  - [ ] Windows: Open cmd with SSH command
  - [ ] Non-blocking execution (subprocess.Popen)

### SSH Command
- [ ] Implement SSH command (Command 1)
  - [ ] Validate selected switch IP
  - [ ] Validate SM_USER environment variable
  - [ ] Validate username format
  - [ ] Spawn platform-specific terminal
  - [ ] Keep app running after SSH opens
  - [ ] Update status: " SSH opened"
  - [ ] Error handling: show error modal if validation fails

### Streaming Modal Base
- [ ] Extend BaseModal for streaming
  - [ ] `StreamingModal` class
  - [ ] Async subprocess execution
  - [ ] Line-by-line output streaming
  - [ ] Scrollable output area
  - [ ] Auto-scroll to bottom
  - [ ] Show "Press ESC to close" header
  - [ ] ESC to close (even while streaming)

### Ping Command
- [ ] Implement Ping modal (Command 2)
  - [ ] Validate IP address
  - [ ] Execute `ping -c 4 <IP>` (macOS/Linux)
  - [ ] Stream output line-by-line
  - [ ] Show in modal
  - [ ] ESC to close
  - [ ] Handle command failures gracefully

### Traceroute Command
- [ ] Implement Traceroute modal (Command 3)
  - [ ] Validate IP address
  - [ ] Execute `traceroute <IP>`
  - [ ] Stream output line-by-line
  - [ ] Show in modal
  - [ ] ESC to close
  - [ ] Handle command failures gracefully

### Error Handling
- [ ] Invalid IP error modal
- [ ] Missing SM_USER error modal
- [ ] Invalid username error modal
- [ ] Command execution errors
- [ ] Network unreachable errors

### Testing Network Commands
- [ ] Test SSH with valid/invalid IPs
- [ ] Test ping with reachable/unreachable hosts
- [ ] Test traceroute with various destinations
- [ ] Test without SM_USER set
- [ ] Test with malformed input

**Phase 4 Deliverable**: SSH terminal spawning, streaming ping/traceroute modals working

---

## Phase 5: Batch Operations (Multi-Switch Commands)

**Goal**: All batch commands implemented

### Batch Ping Command
- [ ] Implement batch ping confirmation (Command 4)
  - [ ] Show confirmation dialog
  - [ ] Display count: "Batch ping will affect 12 switches"
  - [ ] Warning about parallel execution
  - [ ] [y] Yes, [n] No, [ESC] Cancel
- [ ] Implement batch ping execution
  - [ ] Ping all filtered switches (not just selected)
  - [ ] Run in parallel using asyncio.gather()
  - [ ] Each ping: `ping -c 1 <IP>`
  - [ ] Show "Running batch ping, please wait..." modal
- [ ] Implement results display
  - [ ] Aggregate all ping outputs
  - [ ] Format: ">> sw001 (192.168.1.1):\n[output]\n\n"
  - [ ] Show in scrollable modal
  - [ ] ESC to close

### TMUX Integration
- [ ] Create `commands/tmux_handler.py`
  - [ ] Use libtmux library
  - [ ] Create new session with switch name
  - [ ] Split into panes (one per switch)
  - [ ] SSH into each switch
  - [ ] Enable synchronized panes
  - [ ] Tiled layout

### TMUX Command
- [ ] Implement TMUX confirmation (Command 5)
  - [ ] Show confirmation dialog
  - [ ] Display count: "Launch TMUX session with 12 panes?"
  - [ ] Warning about synchronized input
  - [ ] Warning that app will exit
  - [ ] [y] Yes, [n] No, [ESC] Cancel
- [ ] Implement TMUX execution
  - [ ] Validate all filtered switch IPs
  - [ ] Validate SM_USER
  - [ ] Create TMUX session
  - [ ] Create panes for all filtered switches
  - [ ] SSH to each switch
  - [ ] Enable synchronize-panes
  - [ ] Attach to session (exits app)

### Parallel Execution
- [ ] Test batch ping with 10+ switches
- [ ] Test batch ping with unreachable hosts
- [ ] Test TMUX with 2, 5, 10+ switches
- [ ] Verify proper error handling
- [ ] Verify status updates

**Phase 5 Deliverable**: Batch ping and TMUX synchronized sessions working

---

## Phase 6: Polish and Testing (Production Ready)

**Goal**: Production-quality application

### Comprehensive Input Validation
- [ ] Audit all user input points
- [ ] Test with malicious inputs
- [ ] Test with edge cases (empty, null, etc.)
- [ ] Verify no shell=True anywhere
- [ ] Security review of all subprocess calls

### Error Handling
- [ ] Handle all CSV parsing errors
- [ ] Handle missing environment variables
- [ ] Handle file permission errors
- [ ] Handle network errors
- [ ] Handle TMUX not installed
- [ ] User-friendly error messages

### Status Updates
- [ ] Verify status bar updates for all operations
- [ ] Test transient success/failure messages
- [ ] Test filter count accuracy
- [ ] Test sort indicator accuracy
- [ ] Test active command display

### Performance Testing
- [ ] Test with 1,000 switches
- [ ] Test with 10,000 switches
- [ ] Test search filtering speed (< 100ms)
- [ ] Test CSV loading speed (< 1 second for 10k rows)
- [ ] Test table rendering performance
- [ ] Optimize if bottlenecks found

### Unit Tests
- [ ] Test `Switch.matches_term()` method
- [ ] Test `SwitchManager.filter()` OR mode
- [ ] Test `SwitchManager.filter()` AND mode
- [ ] Test `SwitchManager.sort()` methods
- [ ] Test `validate_ip()` with valid/invalid IPs
- [ ] Test `validate_username()` with valid/invalid names
- [ ] Test CSV parsing with various formats
- [ ] Test search history management

### Integration Tests
- [ ] Test command execution (mocked)
- [ ] Test modal lifecycle
- [ ] Test focus management
- [ ] Test keyboard shortcuts
- [ ] Test search + sort interaction

### UI Testing
- [ ] Test with Textual Pilot API (basic)
- [ ] Manual testing of all features
- [ ] Test on different terminal emulators
- [ ] Test on different screen sizes
- [ ] Test color rendering

### Documentation
- [ ] Complete inline code documentation
- [ ] Verify README accuracy
- [ ] Update ARCHITECTURE.md if needed
- [ ] Add code examples for developers
- [ ] Document troubleshooting steps

### Final Validation
- [ ] All features from PLAN.md implemented
- [ ] All success criteria met
- [ ] No known critical bugs
- [ ] Performance targets met
- [ ] Security audit passed

**Phase 6 Deliverable**: Production-ready, tested, documented application

---

## Known Issues & Bugs

_No known issues yet - will be populated during development_

---

## Future Enhancements (Post-MVP)

These are explicitly out of scope for MVP but documented for future consideration:

### Phase 2 Features
- [ ] Custom commands (user-defined scripts)
- [ ] Switch groups (saved filter presets)
- [ ] Connection history logging
- [ ] Export filtered results to new CSV
- [ ] SSH connection pooling
- [ ] Parallel command execution with custom scripts
- [ ] Integration with network monitoring tools
- [ ] Auto-refresh switch status
- [ ] Color-coded status indicators (online/offline)
- [ ] Multiple CSV file support

### Advanced Features
- [ ] Configuration file (YAML/TOML) support
- [ ] Plugin system for custom commands
- [ ] Theme customization (dark/light modes)
- [ ] Mouse support (optional)
- [ ] Multi-selection in table
- [ ] Clipboard operations
- [ ] Undo/redo for operations
- [ ] Background tasks while modal is open
- [ ] Internationalization (i18n)

---

## Development Guidelines

### Before Starting Each Task
1. Read relevant sections in ARCHITECTURE.md
2. Check CLAUDE.md for patterns and conventions
3. Update this TODO with any new subtasks discovered
4. Use TodoWrite tool for multi-step tasks

### After Completing Each Task
- [ ] Test the feature manually
- [ ] Write unit tests if applicable
- [ ] Update documentation if needed
- [ ] Mark task as complete in TODO
- [ ] Commit changes with descriptive message

### Security Checklist (for every command execution)
- [ ] Validate all inputs (IP, username, paths)
- [ ] Use argument lists (no shell=True)
- [ ] Use shlex.quote() for user strings
- [ ] Test with malicious inputs
- [ ] Handle errors gracefully

---

## Quick Reference

### Run Application
```bash
source venv/bin/activate
export SM_USER=$(whoami)
python -m switch_manager
```

### Run Tests
```bash
pytest tests/
pytest --cov=switch_manager
```

### Code Quality
```bash
black switch_manager tests
ruff check switch_manager tests
mypy switch_manager
```

---

**Note**: This TODO is a living document. Update it as development progresses, new issues are discovered, or requirements change.
