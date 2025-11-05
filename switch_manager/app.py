"""Main application class for V-Li Switch Manager."""

from textual.app import App

from switch_manager.config import Config
from switch_manager.manager import SwitchManager


class SwitchManagerApp(App):
    """V-Li Switch Manager TUI Application.

    A keyboard-first terminal interface for managing network switches.
    """

    CSS = """
    Screen {
        background: $surface;
    }

    Vertical {
        width: 100%;
        height: 100%;
    }

    #title {
        height: 1;
        background: $primary;
        color: $text;
        content-align: center middle;
        text-style: bold;
    }

    #command-bar {
        height: 1;
        background: $panel;
        color: $text;
        padding: 0 1;
    }

    #search-help {
        height: 1;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
    }

    #search-input {
        height: 3;
        border: solid $accent;
        background: $surface;
        margin: 0 1;
    }

    #result-counter {
        height: 1;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
    }

    #switch-table {
        height: 1fr;
        margin: 0 1;
    }

    #shortcuts {
        height: 1;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
    }

    #status-bar {
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        """Initialize the application."""
        super().__init__()
        self.title = "V-Li Switch Manager"
        self.config = Config.from_env()
        self.manager = SwitchManager()

    def on_mount(self) -> None:
        """Called when app is mounted. Load configuration and data."""
        # Import here to avoid circular imports
        from switch_manager.screens.main_screen import MainScreen

        # Push the main screen
        self.push_screen(MainScreen(self.config, self.manager))
