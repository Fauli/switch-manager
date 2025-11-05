# V-Li Switch Manager - Functional Specification

## Purpose

A terminal user interface (TUI) application for managing network switches. The tool loads switch data from a CSV file and provides quick access to common network operations (SSH, ping, traceroute) with powerful filtering and batch operation capabilities.

## Target Users

Network administrators and power users who need to:
- Quickly SSH into switches
- Monitor switch connectivity
- Perform batch operations on multiple switches
- Filter large switch inventories efficiently

## Core Philosophy

1. **Keyboard-first**: All operations accessible via keyboard shortcuts
2. **Visual feedback**: Rich status indicators showing current state
3. **Safety**: Confirmations for destructive or batch operations
4. **Speed**: Minimal keystrokes to common operations
5. **Power user focus**: Multiple ways to do things (direct shortcuts + navigation)

---

## Application Layout

The screen is divided into sections from top to bottom:

```
┌─────────────────────────────────────────────────────┐
│                V-Li: Switch Manager                 │
├─────────────────────────────────────────────────────┤
│ NETWORK: [1]ssh [2]ping [3]traceroute [4]batch ping [5]tmux | SYSTEM: [6]details [7]help [8]exit │
├─────────────────────────────────────────────────────┤
│ 🔍 Search [OR mode] - Ctrl+L: Toggle | Ctrl+H: History | ESC: Clear │
│ [ Search input box ]                                │
│ Showing 12 of 56 switches (filtered by: "core sw")  │
├─────────────────────────────────────────────────────┤
│ Name ↑    │ IP           │ subnet │ Alias  │ comment│
│ sw001     │ 192.168.1.1  │ main   │ Core 1 │ Prod   │
│ sw002     │ 192.168.1.2  │ backup │ Core 2 │ Test   │
│ ...                                                  │
├─────────────────────────────────────────────────────┤
│ F1-F5:Sort | 1-8:Cmd | ↑↓:Nav | ←→:Cmd | Enter:Exec | Ctrl+L:Mode | ?:Help │
├─────────────────────────────────────────────────────┤
│ [56 switches]  ↑ Name  [ssh]  ✓ SSH opened          │
└─────────────────────────────────────────────────────┘
```

### 1. Title Bar
- Shows "V-Li: Switch Manager"
- Always visible

### 2. Command Bar
Two groups of commands:

**NETWORK commands** (blue border):
- `[1]ssh` - SSH to selected switch
- `[2]ping` - Ping selected switch
- `[3]traceroute` - Traceroute to selected switch
- `[4]batch ping` - Ping all filtered switches
- `[5]ssh` - Open synchronized ssh session with all filtered switches

**SYSTEM commands** (gray border):
- `[6]details` - Show all CSV fields for selected switch
- `[7]help` - Show help screen
- `[8]exit` - Quit application

**Visual States**:
- Active command: Bold, underlined, highlighted background
- Inactive commands: Normal styling
- Separator `|` between groups

### 3. Search Help Bar
Shows current search mode and keyboard shortcuts:
- Format: `🔍 Search [OR mode] - Ctrl+L: Toggle AND/OR | Ctrl+H: History | ESC: Clear`
- Updates dynamically when search mode changes

### 4. Search Input
- Placeholder text: `Search... (OR mode)` or `Search... (AND mode)`
- Auto-focuses when you type any printable character (unless modal is open)
- Updates table in real-time as you type

### 5. Result Counter
Shows filtering status above the table:
- All switches shown: `Showing all 56 switches`
- Filtered without search text: `Showing 12 of 56 switches`
- Filtered with search text: `Showing 12 of 56 switches (filtered by: "core sw")`

### 6. Data Table
Displays switch inventory with 5 columns:
- **Name**: Switch name/hostname
- **IP**: IP address
- **subnet**: Network subnet identifier
- **Alias**: Alternative names/aliases
- **comment**: Notes/description

**Visual Elements**:
- Column headers show sort indicators: `Name ↑` or `IP ↓`
- Currently selected row is highlighted
- Scrollable if content exceeds screen height

### 7. Keyboard Shortcuts Bar
Shows all available keyboard shortcuts:
`F1-F5:Sort | 1-8:Cmd | ↑↓:Nav | ←→:Cmd | Enter:Exec | Ctrl+L:Mode | Ctrl+H:History | ?:Help`

### 8. Status Bar
Real-time status display with 4 components:
1. **Filter count**: `[12/56 switches]` or `[56 switches]`
2. **Sort indicator**: `↑ Name` or `↓ IP` (only shown when sorted)
3. **Active command**: `[ssh]` or `[ping]`
4. **Last operation result**: `✓ SSH opened` or `✗ Connection failed`

---

## Features

### Feature 1: CSV Data Loading

**Behavior**:
- On startup, loads CSV file from path specified in `SM_CSV_DATA` environment variable (default: `data.csv`)
- CSV delimiter configured via `SM_DELIMITER` environment variable (default: `;`)
- Displays loading message while reading file: `V-Li is collecting all the data for you... Please be patient...`
- After loading, displays all rows in the table

**CSV Format**:
- First row: headers (Name, IP, subnet, aliases, comment)
- Field names are case-insensitive
- All subsequent rows: switch data

**Error Handling**:
- If file doesn't exist: display empty table

### Feature 2: Table Navigation

**Keyboard Controls**:
- `↑` (Up Arrow): Move selection up one row
- `↓` (Down Arrow): Move selection down one row
- Navigation wraps: top row + up = bottom row, bottom row + down = top row

**Visual Feedback**:
- Currently selected row is highlighted
- Selection is preserved when filtering/sorting

### Feature 3: Command Selection

**Three ways to select a command**:

1. **Direct number keys** (`1-8`):
   - Press number to immediately select that command
   - Command bar highlights the selected command
   - Does NOT execute automatically
   - Exception: If search box has focus, numbers go to search instead

2. **Arrow navigation** (`←` `→`):
   - `←` (Left Arrow): Previous command
   - `→` (Right Arrow): Next command
   - Wraps around: first + left = last, last + right = first

3. **Help shortcut** (`?`):
   - Immediately selects and executes the help command
   - Only works when search box does NOT have focus

**Visual Feedback**:
- Active command shown in command bar with special styling
- Status bar shows active command in brackets: `[ssh]`

### Feature 4: Command Execution

**Trigger**: Press `ENTER` key

**Behavior varies by command**:

#### Command: `ssh` (opens SSH session)
1. Reads `SM_USER` environment variable for username
2. Opens NEW terminal window with SSH connection to selected switch's IP
3. Original app remains running
4. Status bar updates: `✓ SSH opened`

**Platform-specific behavior**:
- macOS: Opens Terminal.app
- Linux: Opens xterm
- Windows: Opens cmd

**Validation**:
- IP address must be valid IPv4 or IPv6
- Username must contain only safe characters (alphanumeric, dots, dashes, underscores)
- If validation fails: show error

#### Command: `ping` (streaming ping)
1. Opens modal window showing live ping output
2. Executes `ping -c 4 <IP>` command
3. Output streams in real-time (line by line as received)
4. Modal header: `Press ESC to close`
5. Press `ESC` to close modal and return to main screen

#### Command: `traceroute` (streaming traceroute)
1. Opens modal window showing live traceroute output
2. Executes `traceroute <IP>` command
3. Output streams in real-time
4. Modal header: `Press ESC to close`
5. Press `ESC` to close modal and return to main screen

#### Command: `batch ping` (batch operation)
1. **Shows confirmation dialog** with message:
   ```
   Batch ping will affect 12 switches.

   This will ping all filtered switches in parallel.

   Continue?

   [y] Yes   [n] No   [ESC] Cancel
   ```
2. If user presses `y` or `Y`:
   - Opens modal showing: `Running batch ping, please wait...`
   - Pings ALL filtered switches in parallel (not just selected one)
   - Each ping runs `ping -c 1 <IP>`
   - When all complete, modal updates with combined results:
     ```
     >> sw001 (192.168.1.1):
     [ping output]

     >> sw002 (192.168.1.2):
     [ping output]
     ```
   - Press `ESC` to close results and return to main screen
3. If user presses `n`, `N`, or `ESC`: Cancel operation, return to main screen

#### Command: `ssh` (synchronized SSH session)
1. **Shows confirmation dialog** with message:
   ```
   Launch SSH (maybe TMUX) session with 12 panes?

   ⚠ This will launch a synchronized remote session for all selected hosts.

   All filtered switches will be opened in split panes.
   Commands typed will be sent to ALL switches simultaneously.

   Continue?

   [y] Yes   [n] No   [ESC] Cancel
   ```
2. If user presses `y` or `Y`:
   - Creates remote session with split panes (one per filtered switch)
   - Each pane connects via SSH to one switch
   - Enables synchronized input: typing in one pane sends to ALL panes
   - Window name: `ssh`
   - Visual indicator in remote: `[SYNC]` shown in window status
   - Layout: tiled (evenly distributed panes)
3. If user presses `n`, `N`, or `ESC`: Cancel operation, return to main screen

#### Command: `details` (show full row data)
1. Opens modal window showing all CSV fields for selected switch
2. Format:
   ```
   Name: sw001
   IP: 192.168.1.1
   subnet: main
   aliases: Core Switch 1
   comment: Production environment
   ```
3. Modal header: `Press ESC to close`
4. Press `ESC` to close modal and return to main screen

#### Command: `help` (show help screen)
1. Opens modal with comprehensive help text
2. Shows ASCII art logo
3. Lists all features, keyboard shortcuts, and usage tips
4. Modal header: `Press ESC to close`
5. Press `ESC` to close modal and return to main screen

#### Command: `exit` (quit application)
1. **Shows confirmation dialog** with message:
   ```
   Quit V-Li Switch Manager?

   [y] Yes   [n] No   [ESC] Cancel
   ```
2. If user presses `y` or `Y`: Application exits
3. If user presses `n`, `N`, or `ESC`: Cancel, return to main screen

### Feature 5: Search and Filtering

**Activation**: Type any printable character (unless search box already has focus or modal is open)

**Two Search Modes**:

#### OR Mode (default)
- Matches if ANY search term appears in ANY field
- Example: Search `"sw001 prod"` matches:
  - Row with Name=`sw001` (matches first term)
  - Row with comment=`Production` (matches second term)
  - Row with Name=`sw001` AND comment=`Production` (matches both)

#### AND Mode
- Matches only if ALL search terms appear (each can be in different fields)
- Example: Search `"sw001 prod"` matches:
  - Row with Name=`sw001` AND comment=`Production` ✓
  - Row with Name=`sw001` AND comment=`Testing` ✗ (missing "prod")

**Search Behavior**:
- Case-insensitive
- Searches across all 5 columns: Name, IP, subnet, aliases, comment
- Tokenized by spaces: `"core switch"` = two terms: `"core"` and `"switch"`
- Real-time: table updates as you type
- Empty search = show all rows
- As soon as the user types something, this will be added to the search

**Toggle Search Mode**:
- Press `Ctrl+L` to toggle between OR and AND
- Search help bar updates: `[OR mode]` or `[AND mode]`
- Search input placeholder updates: `Search... (OR mode)` or `Search... (AND mode)`
- Automatically re-runs current search with new mode

**Clear Search**:
- Press `ESC` when search box has focus
- Only works if search box is not empty
- Clears search text, shows all rows

**Search History**:
- Tracks last 20 search terms
- Press `Ctrl+H` to view history modal
- Shows last 10 searches in reverse chronological order
- Format:
  ```
  Recent Searches:

  1. core switch
  2. prod
  3. 192.168
  ...

  Press ESC to close.
  ```
- If no history: shows message `No search history yet.`

**Result Counter Updates**:
- Shows how many switches match current search
- Shows search terms if filtering is active

### Feature 6: Column Sorting

**Activation**: Press `F1` through `F5` to sort by column:
- `F1`: Sort by Name
- `F2`: Sort by IP
- `F3`: Sort by subnet
- `F4`: Sort by Alias
- `F5`: Sort by comment

**Behavior**:
- First press: Sort ascending (A→Z, 0→9)
- Second press on same column: Sort descending (Z→A, 9→0)
- Press different column: Sort that column ascending
- Case-insensitive sorting

**Visual Feedback**:
1. **Column header** shows arrow:
   - Ascending: `Name ↑`
   - Descending: `Name ↓`
2. **Status bar** shows sort indicator:
   - Ascending: `↑ Name`
   - Descending: `↓ Name`

**Interaction with Search**:
- Sorting applies to filtered results
- Sort order is preserved when searching

### Feature 7: Modal Dialogs

**Three Types of Modals**:

1. **Output Screen**: Displays static text (details, help)
2. **Streaming Output Screen**: Displays live command output (ping, traceroute)
3. **Confirmation Screen**: Asks yes/no question (exit, batch ping, ssh)

**Common Modal Behaviors**:
- Appear centered on screen
- Dim/overlay the main table
- Modal has focus (not main table)
- Main table not accessible while modal is open
- Search box should not auto-focus when modal is open

**Closing Modals**:
- Output/Streaming: Press `ESC`
- Confirmation: Press `y`/`n`/`ESC`
- After closing: Focus returns to main table
- Table should remain interactive

**Modal Structure**:
```
┌─────────────────────────────────────┐
│ [Modal Header - instruction]        │
├─────────────────────────────────────┤
│                                      │
│ [Modal content - text/output]       │
│                                      │
└─────────────────────────────────────┘
```

### Feature 8: Status Updates

**Status Bar Components** (updated in real-time):

1. **Filter count**:
   - All showing: `[56 switches]`
   - Some filtered: `[12/56 switches]`

2. **Sort indicator** (only when sorting active):
   - Format: `↑ Name` or `↓ IP`
   - Shows arrow + column name

3. **Active command**:
   - Format: `[ssh]` or `[batch ping]`
   - Always shows currently selected command

4. **Last operation result** (transient):
   - Success: `✓ SSH opened`
   - Failure: `✗ Connection failed`
   - Clears on next operation

---

## Input Validation and Security

### IP Address Validation
- Must be valid IPv4 or IPv6 address
- Reject: empty strings, invalid formats, command injection attempts
- Used for: ssh, ping, traceroute, batch ping, tmux

### Username Validation
- Allowed: alphanumeric, dots (.), dashes (-), underscores (_)
- Reject: spaces, semicolons, pipes, backticks, special characters
- Used for: ssh, tmux

### Command Execution
- All external commands use argument lists (not shell strings)
- No user input passed through shell interpolation
- Prevents command injection attacks

---

## Environment Variables

### Required
- `SM_USER`: SSH username for connections
  - No default value
  - Application will error if not set when using ssh/tmux

### Optional
- `SM_CSV_DATA`: Path to CSV file
  - Default: `data.csv`

- `SM_DELIMITER`: CSV delimiter character
  - Default: `;`

- `SM_DEBUG`: Enable debug logging
  - Values: `true` or `false`
  - Default: `false`
  - When enabled: logs to `switch-manager.log`

---

## Keyboard Shortcuts Reference

### Navigation
- `↑` / `↓`: Move table selection up/down
- `←` / `→`: Switch between commands

### Commands
- `1-8`: Directly select command (if search not focused)
- `ENTER`: Execute selected command
- `?`: Show help (if search not focused)

### Sorting
- `F1`: Sort by Name
- `F2`: Sort by IP
- `F3`: Sort by subnet
- `F4`: Sort by Alias
- `F5`: Sort by comment

### Search
- Any printable character: Auto-focus search (if no modal open)
- `Ctrl+L`: Toggle OR/AND search mode
- `Ctrl+H`: Show search history
- `ESC`: Clear search (when search focused and not empty)

### Modals
- `ESC`: Close output/streaming modal
- `y` / `Y`: Confirm in confirmation dialog
- `n` / `N`: Cancel in confirmation dialog
- `ESC`: Cancel in confirmation dialog

---

## User Workflows

### Workflow 1: Quick SSH to a Switch
1. Application starts, showing all switches
2. Use `↑`/`↓` to navigate to desired switch
3. Press `1` (or ensure ssh is selected and press `ENTER`)
4. New terminal window opens with SSH connection
5. Application remains running

### Workflow 2: Find and Ping Production Switches
1. Type `prod` - search box auto-focuses
2. Table filters to show only switches with "prod" in any field
3. Result counter shows: `Showing 8 of 56 switches (filtered by: "prod")`
4. Navigate to desired switch with `↑`/`↓`
5. Press `2` to select ping command
6. Press `ENTER`
7. Modal shows live ping output
8. Press `ESC` to close modal

### Workflow 3: Batch Ping All Core Switches
1. Type `core` to filter
2. Review filtered count: `Showing 12 of 56 switches`
3. Press `4` to select batch ping
4. Press `ENTER`
5. Confirmation dialog appears: `Batch ping will affect 12 switches...`
6. Press `y` to confirm
7. Wait for results (modal shows progress)
8. Review combined output
9. Press `ESC` to close

### Workflow 4: Synchronized TMUX Session for Maintenance
1. Type `subnet:main` to filter switches in main subnet
2. Result: `Showing 6 of 56 switches`
3. Press `5` to select tmux command
4. Press `ENTER`
5. Confirmation dialog warns about exiting app
6. Press `y` to confirm
7. Application exits
8. TMUX session launches with 6 split panes
9. Type commands once, sent to all 6 switches simultaneously

### Workflow 5: Sort and Search Combined
1. Press `F2` to sort by IP address (ascending)
2. Column header shows: `IP ↑`
3. Type `192.168.1` to filter to specific subnet
4. Table shows sorted, filtered results
5. Sort indicator in status bar: `↑ IP`
6. Filter counter: `Showing 24 of 56 switches (filtered by: "192.168.1")`

### Workflow 6: AND Search for Specific Switch
1. Press `Ctrl+L` to switch to AND mode
2. Search help bar updates: `[AND mode]`
3. Type `sw001 prod`
4. Only switches matching BOTH "sw001" AND "prod" shown
5. Press `Ctrl+L` again to return to OR mode if needed

---

## Error Cases and Edge Behaviors

### No Row Selected
- Commands requiring a selected row should do nothing
- No error message needed

### Empty Filtered Results
- Table shows no rows
- Result counter: `Showing 0 of 56 switches (filtered by: "xyz")`
- Commands still accessible but won't do anything useful

### CSV File Missing
- Application starts with empty table
- No error dialog
- All features work (on empty dataset)

### Invalid IP Address
- SSH/ping/traceroute/batch ping should validate before executing
- Show error if validation fails
- Don't attempt to execute command

### Missing SM_USER Environment Variable
- SSH and TMUX commands should error
- Show error message indicating missing environment variable

### Modal Already Open
- Number keys should NOT execute commands while modal is open
- Printable characters should NOT auto-focus search
- Only modal controls should work

### Focus Management
- When modal closes, focus must return to main table
- Table must be interactive immediately after modal closes
- No freeze or hang states
- User should be able to navigate table with arrow keys immediately

---

## Design Principles for Implementation

### Focus Management Rules
1. On startup: Focus goes to data table
2. User types printable character (no modal open): Focus goes to search input
3. User presses ESC in search: Focus goes back to data table
4. Command pushes modal: Modal takes focus, table loses focus
5. Modal closes: Focus MUST return to data table
6. **Critical**: There must always be a focused widget. Never allow focus to be `None`

### Modal Lifecycle
1. Modal opens: Push screen, modal takes focus
2. Modal displays content: User interacts with modal only
3. Modal closes: Pop screen, restore focus to data table
4. **Critical**: Focus restoration must happen AFTER screen is popped, not during unmount

### Event Handling
1. Event handlers should call `event.stop()` to prevent propagation
2. Call `event.stop()` BEFORE async operations like `pop_screen()`
3. Callbacks should execute AFTER screen management completes

### State Consistency
1. Command bar should always show one active command
2. Status bar should always reflect current state
3. Result counter should update immediately on search/filter changes
4. Sort indicators should be visible in both column headers and status bar

---

## Non-Functional Requirements

### Performance
- CSV loading should be fast (< 1 second for 10,000 rows)
- Search filtering should be real-time (< 100ms delay)
- Table updates should be smooth (no flickering)
- Batch operations should run in parallel (not sequential)

### Usability
- Keyboard shortcuts should be discoverable (always visible)
- Visual feedback for all actions (status bar, highlights)
- No hidden states (everything visible on screen)
- Consistent key bindings (ESC always closes/cancels)

### Reliability
- Application should never freeze or hang
- Ctrl+C should always work to force quit
- Modals should always be closeable
- Invalid input should be handled gracefully

### Accessibility
- All features accessible via keyboard
- No mouse required
- Clear visual indicators for current state
- High contrast text (readable in terminal)

---

## Out of Scope

The following features are explicitly NOT part of this application:

1. CSV editing (read-only)
2. Mouse support (keyboard only)
3. Multi-selection in table
4. Clipboard operations
5. Undo/redo
6. Configuration file support
7. Plugin system
8. Themes/color schemes
9. Window resizing/maximizing
10. Background tasks while modal is open
11. Logging visible to user (debug logging separate)

---

## Success Criteria

The application is considered successful if:

1. ✅ User can load CSV with thousands of switches
2. ✅ User can find any switch in < 5 seconds using search
3. ✅ User can SSH to a switch in < 3 keystrokes
4. ✅ User can batch ping 100+ switches without manual iteration
5. ✅ User can launch synchronized TMUX session for maintenance
6. ✅ Application never freezes or hangs
7. ✅ All keyboard shortcuts work reliably
8. ✅ Modals always close properly
9. ✅ Focus always returns to table after modal closes
10. ✅ Status bar always shows accurate information

---

## Future Enhancements (Not in Current Scope)

Potential features for future versions:

1. Custom commands (user-defined scripts)
2. Switch groups (saved filter presets)
3. Connection history logging
4. Export filtered results to new CSV
5. SSH connection pooling
6. Parallel command execution on multiple switches
7. Integration with network monitoring tools
8. Auto-refresh switch status
9. Color-coded status indicators (online/offline)
10. Multiple CSV file support
