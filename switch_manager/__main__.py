"""Entry point for V-Li Switch Manager.

Run with: python -m switch_manager
"""

import sys
from switch_manager.app import SwitchManagerApp


def main() -> None:
    """Main entry point for the application."""
    try:
        app = SwitchManagerApp()
        app.run()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nExiting V-Li Switch Manager...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting application: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
