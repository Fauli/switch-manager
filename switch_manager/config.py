"""Configuration management for V-Li Switch Manager.

Loads and validates environment variables for application configuration.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration from environment variables.

    Attributes:
        sm_user: SSH username (required for SSH/TMUX commands)
        sm_csv_data: Path to CSV data file
        sm_delimiter: CSV delimiter character
        sm_debug: Enable debug logging
    """
    sm_user: Optional[str]
    sm_csv_data: str
    sm_delimiter: str
    sm_debug: bool

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.

        Environment Variables:
            SM_USER: SSH username (optional, but required for SSH/TMUX operations)
            SM_CSV_DATA: Path to CSV file (default: data.csv)
            SM_DELIMITER: CSV delimiter (default: ;)
            SM_DEBUG: Enable debug logging (default: false)

        Returns:
            Config instance with loaded values

        Note:
            SM_USER is optional at startup but will cause an error when
            attempting SSH or TMUX commands if not set.
        """
        sm_user = os.getenv("SM_USER")
        sm_csv_data = os.getenv("SM_CSV_DATA", "data.csv")
        sm_delimiter = os.getenv("SM_DELIMITER", ";")
        sm_debug = os.getenv("SM_DEBUG", "false").lower() in ("true", "1", "yes")

        return cls(
            sm_user=sm_user,
            sm_csv_data=sm_csv_data,
            sm_delimiter=sm_delimiter,
            sm_debug=sm_debug,
        )

    def validate_for_ssh(self) -> None:
        """Validate that SSH username is configured.

        Raises:
            ValueError: If SM_USER is not set
        """
        if not self.sm_user:
            raise ValueError(
                "SM_USER environment variable is required for SSH operations. "
                "Please set it to your SSH username."
            )

    def __repr__(self) -> str:
        """Return string representation with sensitive data masked."""
        return (
            f"Config("
            f"sm_user={'***' if self.sm_user else None}, "
            f"sm_csv_data={self.sm_csv_data!r}, "
            f"sm_delimiter={self.sm_delimiter!r}, "
            f"sm_debug={self.sm_debug})"
        )
