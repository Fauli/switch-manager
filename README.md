# V-Li: Switch Manager

<p align="center">
    <img src="images/switch-manager-logo.png" alt="Switch Manager Image" width="300" height="300">
    <br/>
    Master Your Network Magic!
</p>

## Introduction

V-Li Switch Manager is a **keyboard-first terminal user interface (TUI)** for managing network switches. Built with [Textual](https://textual.textualize.io/), it provides network administrators with fast, efficient access to common network operations.

### Philosophy: "Vim for Network Operations"

- **Keyboard-first**: All operations accessible via keyboard shortcuts
- **Visual feedback**: Rich status indicators showing current state
- **Safety**: Confirmations for destructive or batch operations
- **Speed**: Minimal keystrokes to common operations
- **Power user focus**: Multiple ways to accomplish tasks

## Features

### Core Operations
- **SSH**: Open terminal sessions to switches (individual or synchronized multi-pane)
- **Ping**: Real-time streaming ping output
- **Traceroute**: Live traceroute diagnostics
- **Batch Operations**: Execute commands on multiple switches in parallel

### Data Management
- **CSV Loading**: Load switch inventory from CSV files
- **Search & Filter**: Real-time search with OR/AND modes
- **Column Sorting**: Sort by any column (F1-F5)
- **Search History**: Track and recall previous searches

### Advanced Features
- **TMUX Integration**: Synchronized sessions across multiple switches
- **Streaming Output**: Real-time command output in modals
- **Input Validation**: Secure command execution with validation

## Installation

### Prerequisites
- Python 3.11 or higher
- Terminal with true color support
- TMUX (optional, for synchronized sessions)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd switch-manager

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e ".[dev]"
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required: SSH username for connections
export SM_USER="your_username"

# Optional: Path to CSV data file (default: data.csv)
export SM_CSV_DATA="data.csv"

# Optional: CSV delimiter character (default: ;)
export SM_DELIMITER=";"

# Optional: Enable debug logging (default: false)
export SM_DEBUG="false"
```

### CSV Data Format

The application expects a CSV file with the following columns:

```csv
Name;IP;subnet;aliases;comment
sw001-lx-prod;192.168.10.1;rum;Main switch;Production core switch
sw002-lx-test;192.168.10.17;bas;Edge switch;Test environment
sw003-lx-backup;10.0.1.3;rum;Backup switch;Backup core switch
```

**Note**: Only the first 5 columns (Name, IP, subnet, aliases, comment) are used. Additional columns are ignored but preserved.

## Usage

### Running the Application

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run the application
python -m switch_manager

# Or if installed as package
switch-manager
```

### Keyboard Shortcuts

#### Navigation
- `↑` / `↓` - Move table selection up/down
- `←` / `→` - Switch between commands
- `F1-F5` - Sort by column (Name, IP, subnet, Alias, comment)

#### Commands
- `1` - SSH to selected switch
- `2` - Ping selected switch
- `3` - Traceroute to selected switch
- `4` - Batch ping all filtered switches
- `5` - Open TMUX synchronized session
- `6` - Show switch details
- `7` - Show help
- `8` - Exit application
- `ENTER` - Execute selected command

#### Search
- Type any character - Auto-focus search box
- `Ctrl+L` - Toggle OR/AND search mode
- `Ctrl+H` - Show search history
- `ESC` - Clear search (when search focused)

#### Modals
- `ESC` - Close modal
- `y`/`n` - Confirm/Cancel in dialogs

## Project Structure

```
switch-manager/
├── switch_manager/         # Main application package
│   ├── __init__.py
│   ├── __main__.py        # Entry point
│   ├── app.py             # Main app class
│   ├── config.py          # Configuration management
│   ├── models.py          # Data models
│   ├── manager.py         # Business logic
│   ├── screens/           # Screen components
│   ├── widgets/           # Custom widgets
│   ├── commands/          # Command execution
│   └── utils/             # Utility functions
├── tests/                 # Test suite
├── docs/                  # Documentation
│   ├── PLAN.md           # Functional specification
│   └── ARCHITECTURE.md   # Technical architecture
├── data.csv              # Sample switch data
├── requirements.txt      # Python dependencies
└── pyproject.toml        # Package configuration
```

## Documentation

- **[PLAN.md](docs/PLAN.md)** - Complete functional specification
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical architecture and design patterns
- **[CLAUDE.md](CLAUDE.md)** - AI collaboration guide

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=switch_manager
```

### Code Quality

```bash
# Format code
black switch_manager tests

# Lint code
ruff check switch_manager tests

# Type checking
mypy switch_manager
```

## Security

The application implements strict security measures:
- **IP Validation**: All IP addresses validated using `ipaddress` module
- **Username Validation**: Only alphanumeric, dots, dashes, underscores allowed
- **Safe Command Execution**: No shell interpolation, argument lists only
- **Input Sanitization**: All user input validated before execution

## Screenshots

<p align="center">
    <img src="images/switch-manager-screenshot.png" alt="Switch Manager Screenshot">
</p>

<p align="center">
    <img src="images/switch-manager-screenshot-2.png" alt="Switch Manager Screenshot">
</p>

## Contributing

Contributions are welcome! Please read the documentation in `docs/` before contributing.

## License

MIT License - See LICENSE file for details

## Roadmap

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for planned features and enhancements.

