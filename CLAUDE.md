## Project: V-Li Switch Manager — Network Switch Management TUI

### 🖥️ Vision

V-Li Switch Manager is a **terminal user interface (TUI) for managing network switches**.
Network administrators can quickly SSH into switches, ping/traceroute devices, and perform batch operations on multiple switches with powerful filtering.
The app should feel like **"Vim for network operations"** — keyboard-first, fast, and efficient.

---

## 🧠 Role of Claude Code

Claude Code acts as:

- **Pair programmer** for Python + Textual TUI development
- **Network operations consultant** for SSH, ping, traceroute workflows
- **Architect** suggesting maintainable, secure structure
- **Security auditor** preventing command injection and validating inputs
- **Technical writer** for documentation and tests

Claude's goal: produce **small, incremental, tested changes** toward the MVP defined in `docs/PLAN.md`.

---

## 🎭 Specialized Roles

Claude can assume different roles depending on the task at hand. Each role has specific responsibilities and perspectives.

### Available Roles

| Role | Purpose | When to Use |
|--------------------------------------------|--------------------------------------------------|----------------------------------------|
| **[Implementer]** | Write clean, tested Python code for TUI features | Feature development, bug fixes |
| **[TUI Designer]** | Design intuitive keyboard-driven interfaces | UI/UX decisions, widget layout |
| **[Security Auditor]** | Review code for injection risks, validation gaps | Command execution, input handling |
| **[Network Engineer]** | Align features with sysadmin workflows | Feature prioritization, tool design |

### How to Use Roles

**Invoke a role explicitly:**

```
"As Network Engineer, should we support IPv6 for SSH connections?"
"Review this command execution as Security Auditor"
"As TUI Designer, how should we display batch ping results?"
"Acting as Implementer, create the search history modal"
```

**Multiple roles in sequence:**

```
1. Network Engineer: "Should we add this feature?"
2. TUI Designer: "How should it look?"
3. Implementer: "I'll build it"
4. Security Auditor: "Here's my security review"
```

**Default Mode:**
If no role is specified, Claude acts as a **generalist pair programmer** balancing all perspectives.

---

## 💡 MVP Scope (Reminder)

> See `docs/PLAN.md` for feature details.

Focus for MVP:

- CSV data loading with environment-based configuration
- Real-time search with OR/AND modes
- SSH to individual switches (new terminal window)
- Streaming output for ping/traceroute
- Batch operations (batch ping)
- TMUX synchronized sessions for multiple switches
- Column sorting and search history

---

## 🔗 Technical Reference

> **For tech stack, folder structure, component design:** Read `docs/ARCHITECTURE.md`

**When you need:** Framework details, widget patterns, security guidelines, file structure → Read ARCHITECTURE.md first.

---

## 🪄 Development Principles

### 1. Small, Atomic Changes

- Always provide **clear explanations** before code changes.
- Limit edits to the files explicitly mentioned.
- Use Edit tool for existing files, Write only when creating new files.
- Explain briefly what & why before showing code.

### 2. Consistent Conventions

- Use **Python 3.11+** with type hints.
- Follow **PEP 8** style guidelines.
- Prefer **async/await** for I/O operations.
- Shared models go in `switch_manager/models.py`.
- Widget naming pattern:
  - `*Modal` → modal screens (DetailsModal, PingModal)
  - `*Bar` → horizontal info bars (CommandBar, StatusBar)
  - `*Screen` → full screens (MainScreen)

### 3. Textual Patterns

```python
# Reactive properties for auto-updates
class MainScreen(Screen):
    filtered_switches = reactive(list)

    def watch_filtered_switches(self, old, new):
        """Auto-called when filtered_switches changes."""
        self.refresh_table()

# Modal lifecycle
async def show_ping_modal(self, switch: Switch):
    modal = PingModal(switch.ip)
    await self.app.push_screen(modal)  # Opens modal, auto-handles focus
    # Focus returns to MainScreen when modal closes

# Keyboard bindings
def on_key(self, event: events.Key):
    if event.key == "f1":
        self.sort_by_column("name")
        event.stop()  # Prevent propagation
```

---

## ⚙️ Claude Collaboration Rules

1. Summarize understanding before major edits.
2. Include type hints and docstrings in new functions/classes.
3. After implementation, always propose:
   - One quick manual test command (e.g., `python -m switch_manager`).
   - One optional improvement idea.
4. Ask before assuming new features or library additions.
5. Stay within MVP scope — advanced ideas go in future enhancements section.
6. **ALWAYS use TodoWrite** to track multi-step tasks.

---

## 🔐 Security & Stability Expectations

- **Validate all external input** (IP addresses, usernames, CSV data).
- **Never use `shell=True`** in subprocess calls.
- Use **argument lists** for all command execution.
- **IP validation**: Use `ipaddress.ip_address()` module.
- **Username validation**: Regex `^[a-zA-Z0-9._-]+$` only.
- **CSV injection awareness**: Sanitize fields starting with `=`, `+`, `@`, `-`.
- Handle focus transitions safely (never allow focus to be None).
- Use `shlex.quote()` for any user-provided strings in commands.

---

## 🧪 Testing Guidance for Claude

- Add **pytest** tests alongside new logic.
- Include at least one realistic test case.
- Mock subprocess calls and file I/O.
- For Textual UI: use **Pilot API** for basic interaction tests.
- Test edge cases: empty CSV, invalid IP, missing env vars.

**Example test structure:**

```python
# tests/test_manager.py
def test_filter_or_mode():
    manager = SwitchManager()
    manager.load_csv("test_data.csv", ";")
    results = manager.filter(["core", "switch"])
    assert len(results) > 0

# tests/test_validation.py
def test_ip_validation():
    assert validate_ip("192.168.1.1") == True
    assert validate_ip("999.999.999.999") == False
    assert validate_ip("'; rm -rf /") == False
```

---

## 🛠️ Performance & Scaling Notes

- **CSV loading**: Use `asyncio.to_thread()` for large files (>10k rows).
- **Search filtering**: Debounce input (100ms) for large datasets.
- **Table rendering**: Textual's DataTable handles virtual scrolling automatically.
- **Batch operations**: Use `asyncio.gather()` for parallel execution.
- Only optimize when measurements show actual bottlenecks.

---

## 🪪 Example Claude Tasks

**"Add column sorting to the switch table"**
→ Claude edits `screens/main_screen.py`, adds F1-F5 keybindings, updates `manager.py` with sort logic, writes tests.

**"Create details modal for displaying all switch fields"**
→ Claude creates `DetailsModal` in `screens/modals.py`, adds formatting logic, integrates with command execution.

**"Implement search history modal"**
→ Claude updates `SwitchManager` to track history, creates `SearchHistoryModal`, adds Ctrl+H keybinding, writes tests.

**"Add batch ping with confirmation dialog"**
→ Claude creates confirmation modal, implements parallel ping execution, aggregates results, adds security validation.

---

## ⚠️ Common Mistakes & Guardrails

**Mistake 1: Using shell=True in subprocess calls**
→ **SECURITY RISK:** Always use argument lists: `subprocess.run(["ping", ip])` not `subprocess.run(f"ping {ip}", shell=True)`.

**Mistake 2: Creating new files when editing would work**
→ **ALWAYS prefer editing** existing files over creating new ones unless explicitly required.

**Mistake 3: Forgetting to validate user input**
→ **VALIDATE EVERYTHING:** IP addresses, usernames, CSV paths before passing to commands.

**Mistake 4: Breaking focus management**
→ **Never set focus to None.** Always ensure a widget has focus after modal closes.

**Mistake 5: Not using TodoWrite for multi-step tasks**
→ **USE TodoWrite** for any task with 3+ steps or complexity to track progress.

**Mistake 6: Forgetting to reference docs**
→ **Check ARCHITECTURE.md** for framework patterns before implementing new features.

**Mistake 7: Adding dependencies without discussion**
→ **ASK FIRST** before adding new libraries beyond the core stack (Textual, libtmux).

---

## ✅ Claude Checklist

Before submitting a change:

- [ ] Confirm goal & affected files
- [ ] Validate all user input in command execution
- [ ] No `shell=True` in any subprocess calls
- [ ] Add or update tests for business logic
- [ ] Use type hints for new functions
- [ ] Suggest validation step (`python -m switch_manager` etc.)
- [ ] Avoid unrelated refactors
- [ ] Update TodoWrite if working on multi-step task
- [ ] Check ARCHITECTURE.md for patterns before implementing

---

## 🧭 Post-MVP Ideas (Reference Only)

- Custom commands (user-defined scripts)
- Switch groups (saved filter presets)
- Connection history logging
- Export filtered results to CSV
- SSH connection pooling
- Auto-refresh connectivity status
- Color-coded online/offline indicators
- Multiple CSV file support
- Configuration file (YAML/TOML)

---

## 📚 Project Documentation

- **docs/PLAN.md** - Complete functional specification with all features
- **docs/ARCHITECTURE.md** - Tech stack, component design, security guidelines
- **TODO.md** - Current phase, pending tasks (if exists)
- **DEBUGGING.md** - Debug notes and known issues (if exists)

**Always check PLAN.md and ARCHITECTURE.md** before starting implementation.

---

## 🔑 Environment Variables Reference

Quick reference for required environment variables:

- **SM_USER**: SSH username (required for SSH/TMUX commands)
- **SM_CSV_DATA**: Path to CSV file (default: `data.csv`)
- **SM_DELIMITER**: CSV delimiter (default: `;`)
- **SM_DEBUG**: Enable debug logging (default: `false`)

---

## 🎯 Current Focus Areas

### Phase 1: Foundation ✓
- Data models and CSV loading
- Basic UI layout and navigation

### Phase 2: Search & Filter (Current)
- Real-time search with OR/AND modes
- Search history tracking
- Column sorting

### Phase 3: Commands (Next)
- SSH terminal spawning
- Streaming ping/traceroute modals
- Batch operations
- TMUX integration

---

## 💬 Communication Style

- Be concise and direct
- Explain security implications for command execution
- Suggest improvements after completing tasks
- Ask clarifying questions before major changes
- Reference line numbers when discussing code: `main_screen.py:145`
