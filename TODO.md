# V-Li Switch Manager - Development TODO

## Current Status

**Current Phase**: Phase 6 - Polish and Testing
**Last Updated**: 2025-11-05

**Completed Phases:**
- ✅ **Phase 1**: Foundation (CSV loading, table, navigation)
- ✅ **Phase 2**: Search and Sort (OR/AND search, column sorting)
- ✅ **Phase 3**: Basic Commands (Details, Help, Exit modals)
- ✅ **Phase 4**: Network Commands (SSH, Ping, Traceroute)
- ✅ **Phase 5**: Batch Operations (Batch Ping, TMUX synchronized sessions)

**Next Up:**
- 🔄 **Phase 6**: Polish and Testing

---

## ✅ Phase 1: Foundation - COMPLETED

**Deliverable**: App loads CSV and displays switches in navigable table

### What Was Built:
- [x] `models.py` - Switch, SearchMode, CommandType, Command dataclasses
- [x] `config.py` - Environment variable configuration (SM_USER, SM_CSV_DATA, etc.)
- [x] `manager.py` - SwitchManager with CSV loading, filtering, sorting
- [x] `app.py` - Main SwitchManagerApp class
- [x] `screens/main_screen.py` - Main screen with DataTable
- [x] `__main__.py` - Entry point with error handling
- [x] DataTable with 5 columns (Name, IP, subnet, aliases, comment)
- [x] Arrow key navigation (↑↓) with wrapping
- [x] CSV loading with 56 switches from data.csv
- [x] Loading message during CSV load
- [x] Vertical container layout

---

## ✅ Phase 2: Search and Sort - COMPLETED

**Deliverable**: Real-time search with OR/AND modes, column sorting, search history

### What Was Built:
- [x] SearchInput widget with auto-focus on typing
- [x] Real-time filtering as user types
- [x] OR mode: match ANY term in ANY field
- [x] AND mode: match ALL terms across fields
- [x] Ctrl+L to toggle OR/AND search mode
- [x] ESC to clear search
- [x] F1-F5 column sorting (Name, IP, subnet, Alias, comment)
- [x] Sort indicators in column headers (↑↓)
- [x] Sort indicator in status bar
- [x] Result counter: "Showing X of Y switches (filtered by: 'text')"
- [x] Search history tracking (last 20 searches)
- [x] Enter returns focus to table
- [x] Case-insensitive search and sort

---

## ✅ Phase 3: Basic Commands - COMPLETED

**Deliverable**: Command selection, modals, details/help/exit working

### What Was Built:
- [x] `widgets/command_bar.py` - Interactive CommandBar with highlighting
- [x] `widgets/status_bar.py` - StatusBar showing counts, command, sort state
- [x] `screens/modals.py` - Base modal classes
- [x] Command selection with 1-8 keys
- [x] Command selection with ←→ arrows
- [x] Active command highlighted in command bar (bold/reverse)
- [x] DetailsModal - Shows all switch fields
- [x] HelpModal - Comprehensive help with keyboard shortcuts
- [x] ConfirmationModal - Yes/no dialogs
- [x] Exit confirmation (Command 8, or 'q')
- [x] ? shortcut for instant help
- [x] Proper focus management (modals → table)
- [x] Status bar shows active command

---

## ✅ Phase 4: Network Commands - COMPLETED

**Deliverable**: SSH terminal spawning, streaming ping/traceroute modals working

### What Was Built:
- [x] `utils/validation.py` - IP and username validation
  - [x] validate_ip() using ipaddress module
  - [x] validate_username() with regex (alphanumeric, dots, dashes, underscores only)
  - [x] Security: prevents command injection
- [x] `utils/terminal.py` - Platform-specific terminal spawning
  - [x] macOS: Terminal.app via osascript
  - [x] Linux: gnome-terminal, konsole, xterm (tries in order)
  - [x] Windows: Windows Terminal or cmd
- [x] SSH Command (Command 1)
  - [x] Opens new terminal window
  - [x] App keeps running
  - [x] Validates IP and username
  - [x] Shows error modal if SM_USER not set
  - [x] Status: "✓ SSH opened to sw001"
- [x] StreamingModal - Real-time command output
  - [x] Byte-by-byte streaming with timeout
  - [x] Background async task
  - [x] Auto-scrolling output
  - [x] ESC to close and terminate process
  - [x] Success/error status at end
- [x] Ping Command (Command 2)
  - [x] Live streaming output (ping -c 4)
  - [x] Real-time display (no buffering delay)
  - [x] IP validation
- [x] Traceroute Command (Command 3)
  - [x] Live streaming output
  - [x] Real-time display
  - [x] IP validation
- [x] Error handling modals for all validation failures

**Security Features:**
- No shell=True anywhere
- All subprocess calls use argument lists
- IP addresses validated before use
- Usernames validated (no special characters)

---

## ✅ Phase 5: Batch Operations - COMPLETED

**Deliverable**: Batch ping and TMUX synchronized sessions working

### What Was Built:

#### Multi-Selection System
- [x] Space bar to toggle selection on/off
- [x] Visual indicators (☐/☑) in table
- [x] Selection count in status bar
- [x] Works with batch operations

#### Batch Ping Command (Command 4)
- [x] Multi-selection support
- [x] Works on selected switches OR all filtered
- [x] Confirmation dialog with clear Y/N/ESC instructions
- [x] IP validation for all switches
- [x] Parallel execution using asyncio.gather()
- [x] Real-time progress display
- [x] BatchPingModal with color-coded results
- [x] ESC to close and cancel

#### TMUX Integration (Command 5)
- [x] `utils/tmux_handler.py` created
- [x] Native tmux commands (no external libraries needed)
- [x] Tiled layout with synchronized panes
- [x] Confirmation dialog with strong warnings
- [x] TMUX availability check with install instructions
- [x] Validates SM_USER and all IPs
- [x] Creates session with one pane per switch
- [x] SSH to each switch
- [x] Synchronized panes enabled
- [x] Attaches to session (exits app)

**Phase 5 Complete!** All batch operations working.

---

## ⏳ Phase 6: Polish and Testing - NOT STARTED

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

_No known critical issues_

### Minor Issues:
- Layout may need tweaking on very small terminal windows
- Search history modal not yet implemented (Ctrl+H placeholder)

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

## Quick Reference

### Run Application
```bash
source venv/bin/activate
export SM_USER=$(whoami)
python -m switch_manager
# Or: ./run.sh
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

## Achievements So Far 🎉

### Working Features:
1. ✅ CSV loading (56 switches from data.csv)
2. ✅ DataTable with 5 columns
3. ✅ Arrow key navigation (↑↓)
4. ✅ Real-time search (type to search)
5. ✅ OR/AND search modes (Ctrl+L to toggle)
6. ✅ Column sorting (F1-F5)
7. ✅ Sort indicators (arrows in headers)
8. ✅ Interactive command bar (1-8, ←→)
9. ✅ Details modal (Command 6)
10. ✅ Help modal (Command 7 or ?)
11. ✅ Exit confirmation (Command 8 or q)
12. ✅ SSH to switches (Command 1) - opens new terminal!
13. ✅ Ping with live streaming output (Command 2)
14. ✅ Traceroute with live streaming output (Command 3)
15. ✅ **Multi-selection (Space to toggle)** - NEW!
16. ✅ **Batch Ping (Command 4)** - Parallel ping on selected switches - NEW!
17. ✅ **TMUX synchronized sessions (Command 5)** - Control multiple switches at once - NEW!
18. ✅ Full input validation (IP, username)
19. ✅ Error modals for all validation failures
20. ✅ Platform-specific terminal spawning (macOS/Linux/Windows)
21. ✅ Secure command execution (no injection possible)
22. ✅ Color-coded batch ping results
23. ✅ TMUX availability detection

### Keyboard Shortcuts:
- **Search**: Type to search, Ctrl+L to toggle OR/AND, ESC to clear
- **Sort**: F1-F5 for columns
- **Navigate**: ↑↓ arrows, wraps around
- **Select**: Space to toggle selection (for batch operations)
- **Commands**: 1-8 or ←→, Enter to execute
- **Help**: ? for quick help
- **Exit**: q or ESC (with confirmation)

---

**Note**: This TODO is a living document. Update it as development progresses, new issues are discovered, or requirements change.
