"""Platform-specific terminal spawning utilities."""

import subprocess
import sys
import shlex


def spawn_ssh_terminal(username: str, ip: str) -> bool:
    """Spawn a new terminal window with SSH connection.

    Opens a platform-specific terminal window and initiates SSH connection.
    The original application continues running.

    Args:
        username: SSH username (must be pre-validated)
        ip: IP address (must be pre-validated)

    Returns:
        True if terminal spawned successfully, False otherwise

    Security:
        - username and ip MUST be validated before calling this function
        - Uses argument lists (not shell strings) to prevent injection
        - Never uses shell=True
    """
    try:
        if sys.platform == "darwin":
            # macOS: Use Terminal.app
            # Use osascript to open Terminal with SSH command
            script = f'tell application "Terminal" to do script "ssh {username}@{ip}"'
            subprocess.Popen(
                ["osascript", "-e", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True

        elif sys.platform.startswith("linux"):
            # Linux: Try common terminal emulators in order of preference
            terminals = [
                ["gnome-terminal", "--", "ssh", f"{username}@{ip}"],
                ["konsole", "-e", "ssh", f"{username}@{ip}"],
                ["xterm", "-e", "ssh", f"{username}@{ip}"],
                ["x-terminal-emulator", "-e", "ssh", f"{username}@{ip}"],
            ]

            for terminal_cmd in terminals:
                try:
                    subprocess.Popen(
                        terminal_cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return True
                except FileNotFoundError:
                    continue

            # No terminal found
            return False

        elif sys.platform == "win32":
            # Windows: Use cmd or PowerShell
            # Try Windows Terminal first, then cmd
            try:
                # Windows Terminal (modern)
                subprocess.Popen(
                    ["wt", "ssh", f"{username}@{ip}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return True
            except FileNotFoundError:
                # Fall back to cmd
                subprocess.Popen(
                    ["cmd", "/c", "start", "cmd", "/k", "ssh", f"{username}@{ip}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return True

        else:
            # Unsupported platform
            return False

    except Exception:
        return False


def get_platform_name() -> str:
    """Get human-readable platform name.

    Returns:
        Platform name string
    """
    if sys.platform == "darwin":
        return "macOS"
    elif sys.platform.startswith("linux"):
        return "Linux"
    elif sys.platform == "win32":
        return "Windows"
    else:
        return sys.platform
