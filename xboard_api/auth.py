"""Token generation and management for Xboard Admin API.

Token is stored in ~/.xboard_token (one token per line, latest first).
"""

import os
from pathlib import Path

DEFAULT_TOKEN_FILE = Path.home() / ".xboard_token"


def load_token(token_file: str | Path | None = None) -> str | None:
    """Load the most recent token from file.

    Returns None if the file doesn't exist or is empty.
    """
    fp = Path(token_file) if token_file else DEFAULT_TOKEN_FILE
    if not fp.exists():
        return None
    content = fp.read_text().strip()
    if not content:
        return None
    return content


def save_token(token: str, token_file: str | Path | None = None) -> None:
    """Save a Bearer token to file."""
    fp = Path(token_file) if token_file else DEFAULT_TOKEN_FILE
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(token.strip() + "\n")
