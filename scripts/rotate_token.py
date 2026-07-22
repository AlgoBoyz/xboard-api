#!/usr/bin/env python3
"""Rotate the Xboard Admin API token.

Generates a new Sanctum token for the admin user and updates:
  - ~/.xboard_token (local file)
  - /etc/xboard-mcp.env (MCP server env)

Usage:
    python rotate_token.py [--dry-run]
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

TOKEN_FILE = Path.home() / ".xboard_token"
ENV_FILE = Path("/etc/xboard-mcp.env")
XBOARD_DIR = Path("/var/www/xboard")


def run_ssh(cmd: str) -> str:
    """Run command via local SSH or directly on the Xboard server."""
    r = subprocess.run(
        ["bash", "-c", cmd],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        raise RuntimeError(f"Command failed: {r.stderr.strip()}")
    return r.stdout.strip()


def generate_token() -> str:
    """Generate a new Sanctum token via PHP artisan tinker."""
    php = (
        "php artisan tinker --execute=\""
        "$user = \\App\\Models\\User::where('is_admin', 1)->first(); "
        "$token = $user->createToken('admin-api')->plainTextToken; "
        "echo $token;"
        "\""
    )
    result = run_ssh(f"cd {XBOARD_DIR} && {php}")
    token = result.strip().split("\n")[-1].strip()
    if not token or "|" not in token:
        raise RuntimeError(f"Failed to parse token from: {result[:100]}")
    return token


def update_token_file(token: str, dry_run: bool = False):
    """Write token to file with chmod 600."""
    if dry_run:
        print(f"  [DRY-RUN] Would write token to {TOKEN_FILE}")
        return
    TOKEN_FILE.write_text(token + "\n")
    TOKEN_FILE.chmod(0o600)


def update_env(token: str, dry_run: bool = False):
    """Update XBOARD_API_KEY in /etc/xboard-mcp.env."""
    if not ENV_FILE.exists():
        print(f"  [WARN] {ENV_FILE} not found — skipping env update")
        return
    content = ENV_FILE.read_text()
    new_content = []
    found = False
    for line in content.splitlines():
        if line.startswith("XBOARD_API_KEY="):
            new_content.append(f"XBOARD_API_KEY={token}")
            found = True
        else:
            new_content.append(line)
    if not found:
        new_content.append(f"XBOARD_API_KEY={token}")
    if dry_run:
        print(f"  [DRY-RUN] Would update {ENV_FILE}")
    else:
        ENV_FILE.write_text("\n".join(new_content) + "\n")
        ENV_FILE.chmod(0o600)


def main():
    dry_run = "--dry-run" in sys.argv
    print(f"[{datetime.now().isoformat()}] Token rotation {'(dry-run)' if dry_run else ''}")

    token = generate_token()
    print(f"  Token: {token[:12]}...{token[-4:]}")

    update_token_file(token, dry_run)
    update_env(token, dry_run)

    if not dry_run:
        # Restart MCP service
        subprocess.run(["sudo", "systemctl", "restart", "xboard-mcp"], capture_output=True)
        print("  Service restarted")

    print("  Done.")


if __name__ == "__main__":
    main()
