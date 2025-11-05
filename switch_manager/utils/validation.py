"""Input validation utilities for security and correctness."""

import ipaddress
import re


def validate_ip(ip: str) -> bool:
    """Validate an IP address (IPv4 or IPv6).

    Args:
        ip: IP address string to validate

    Returns:
        True if valid IP address, False otherwise

    Security:
        Uses ipaddress module to prevent command injection
    """
    if not ip or not ip.strip():
        return False

    try:
        ipaddress.ip_address(ip.strip())
        return True
    except ValueError:
        return False


def validate_username(username: str) -> bool:
    """Validate a username for SSH operations.

    Only allows alphanumeric characters, dots, dashes, and underscores.
    This prevents command injection attacks.

    Args:
        username: Username string to validate

    Returns:
        True if valid username, False otherwise

    Security:
        Rejects any characters that could be used for command injection
        (spaces, semicolons, pipes, backticks, etc.)
    """
    if not username or not username.strip():
        return False

    # Only allow: letters, numbers, dots, dashes, underscores
    pattern = r'^[a-zA-Z0-9._-]+$'
    return bool(re.match(pattern, username.strip()))


def sanitize_for_display(text: str, max_length: int = 100) -> str:
    """Sanitize text for safe display in UI.

    Args:
        text: Text to sanitize
        max_length: Maximum length before truncation

    Returns:
        Sanitized text safe for display
    """
    if not text:
        return ""

    # Remove control characters except newline and tab
    sanitized = ''.join(
        char for char in text
        if char.isprintable() or char in ('\n', '\t')
    )

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    return sanitized
