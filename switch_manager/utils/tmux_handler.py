"""TMUX session management for synchronized multi-switch access."""

import subprocess
import sys
from typing import List


def is_tmux_available() -> bool:
    """Check if tmux is installed and available.

    Returns:
        True if tmux is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["tmux", "-V"],
            capture_output=True,
            timeout=2
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def create_tmux_session(switches: List, username: str, session_name: str = "switch-manager") -> bool:
    """Create a TMUX session with synchronized panes for multiple switches.

    Creates a new TMUX session with one pane per switch, all synchronized.
    Each pane will SSH into its respective switch.

    Args:
        switches: List of Switch objects to connect to
        username: SSH username (must be pre-validated)
        session_name: Name for the TMUX session (default: "switch-manager")

    Returns:
        True if session was created successfully, False otherwise

    Security:
        - username and switch IPs MUST be validated before calling
        - Uses argument lists to prevent command injection
        - Never uses shell=True
    """
    if not switches:
        return False

    if not is_tmux_available():
        return False

    try:
        # Kill any existing session with the same name
        subprocess.run(
            ["tmux", "kill-session", "-t", session_name],
            capture_output=True,
            timeout=2
        )
    except Exception:
        # Session didn't exist, that's fine
        pass

    try:
        # Create new session with first switch
        first_switch = switches[0]
        subprocess.run(
            ["tmux", "new-session", "-d", "-s", session_name,
             "ssh", f"{username}@{first_switch.ip}"],
            check=True,
            timeout=5
        )

        # Split window for remaining switches
        for i, switch in enumerate(switches[1:], start=1):
            # Split the window
            subprocess.run(
                ["tmux", "split-window", "-t", session_name,
                 "ssh", f"{username}@{switch.ip}"],
                check=True,
                timeout=5
            )

            # Rebalance the layout after each split for better distribution
            subprocess.run(
                ["tmux", "select-layout", "-t", session_name, "tiled"],
                check=True,
                timeout=2
            )

        # Enable synchronized panes
        subprocess.run(
            ["tmux", "set-window-option", "-t", session_name,
             "synchronize-panes", "on"],
            check=True,
            timeout=2
        )

        # Add a status message to the session
        subprocess.run(
            ["tmux", "display-message", "-t", session_name,
             f"V-Li Switch Manager: {len(switches)} switches synchronized"],
            timeout=2
        )

        return True

    except subprocess.TimeoutExpired:
        return False
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False


def attach_to_session(session_name: str = "switch-manager") -> bool:
    """Attach to an existing TMUX session.

    This will replace the current process with the TMUX attach command,
    effectively exiting the application.

    Args:
        session_name: Name of the TMUX session to attach to

    Returns:
        True if attach succeeded, False otherwise
    """
    try:
        # Use execvp to replace current process with tmux attach
        # This exits the Python application and gives full control to tmux
        import os
        os.execvp("tmux", ["tmux", "attach-session", "-t", session_name])
        # This line is never reached if successful
        return True
    except Exception:
        return False


def get_session_info(session_name: str = "switch-manager") -> dict:
    """Get information about a TMUX session.

    Args:
        session_name: Name of the TMUX session

    Returns:
        Dictionary with session info, or empty dict if session doesn't exist
    """
    try:
        result = subprocess.run(
            ["tmux", "list-sessions", "-F", "#{session_name}"],
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode == 0:
            sessions = result.stdout.strip().split('\n')
            if session_name in sessions:
                return {"exists": True, "name": session_name}

        return {"exists": False}

    except Exception:
        return {"exists": False}
