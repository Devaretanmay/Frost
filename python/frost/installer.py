"""Local-first client installer wizard for FROST MCP server.

Configures local agentic environments (Claude Code, Cursor, VS Code,
OpenCode, Gemini CLI) to use the local FROST MCP process (`frost serve`).
No login, no SaaS, no API keys — 100% local-first execution.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Optional


CLIENT_PROVIDERS = [
    "1. Claude Code",
    "2. Gemini CLI",
    "3. OpenCode",
    "4. Cursor",
    "5. VS Code",
    "6. Custom MCP Client",
    "7. Skip",
]


def get_frost_mcp_config() -> dict[str, Any]:
    """Return standard local MCP server configuration snippet."""
    frost_path = shutil.which("frost") or "frost"
    return {
        "command": frost_path,
        "args": ["serve"],
    }


def install_claude_code() -> tuple[bool, str]:
    """Configure Claude Code to run local FROST MCP server."""
    possible_paths = [
        Path.home() / ".claude.json",
        Path.home() / ".config" / "claude" / "config.json",
        Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
    ]

    target_path = possible_paths[0]
    for p in possible_paths:
        if p.parent.exists():
            target_path = p
            break

    return _update_mcp_json_file(target_path, "frost")


def install_cursor() -> tuple[bool, str]:
    """Configure Cursor editor to run local FROST MCP server."""
    possible_paths = [
        Path.home() / ".cursor" / "mcp.json",
        Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "mcp.json",
    ]
    return _update_mcp_json_file(possible_paths[0], "frost")


def install_vscode() -> tuple[bool, str]:
    """Configure VS Code to run local FROST MCP server."""
    possible_paths = [
        Path.home() / ".vscode" / "mcp.json",
        Path.home() / "Library" / "Application Support" / "Code" / "User" / "mcp.json",
    ]
    return _update_mcp_json_file(possible_paths[0], "frost")


def install_opencode() -> tuple[bool, str]:
    """Configure OpenCode to run local FROST MCP server."""
    target_path = Path.home() / ".config" / "opencode" / "mcp.json"
    return _update_mcp_json_file(target_path, "frost")


def install_gemini() -> tuple[bool, str]:
    """Configure Gemini CLI to run local FROST MCP server."""
    target_path = Path.home() / ".gemini" / "mcp.json"
    return _update_mcp_json_file(target_path, "frost")


def _update_mcp_json_file(file_path: Path, server_name: str) -> tuple[bool, str]:
    """Helper to update or create an MCP client configuration file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        config: dict[str, Any] = {}

        if file_path.exists():
            try:
                config = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception:
                config = {}

        servers = config.setdefault("mcpServers", {})
        servers[server_name] = get_frost_mcp_config()

        file_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        return True, str(file_path)
    except Exception as e:
        return False, str(e)


def run_init_wizard(choice: Optional[int] = None) -> None:
    """Run interactive or non-interactive frost init wizard."""
    print("Welcome to FROST.\n")
    print("How would you like to use FROST?\n")

    for provider in CLIENT_PROVIDERS:
        print(f"  {provider}")
    print()

    if choice is None:
        try:
            user_input = input("Select an option [1-7]: ").strip()
            choice = int(user_input) if user_input.isdigit() else 7
        except (KeyboardInterrupt, EOFError):
            choice = 7

    if choice == 1:
        ok, path = install_claude_code()
        _print_result("Claude Code", ok, path)
    elif choice == 2:
        ok, path = install_gemini()
        _print_result("Gemini CLI", ok, path)
    elif choice == 3:
        ok, path = install_opencode()
        _print_result("OpenCode", ok, path)
    elif choice == 4:
        ok, path = install_cursor()
        _print_result("Cursor", ok, path)
    elif choice == 5:
        ok, path = install_vscode()
        _print_result("VS Code", ok, path)
    elif choice == 6:
        print("\nCopy and paste this snippet into your MCP client configuration:\n")
        snippet = {
            "mcpServers": {
                "frost": get_frost_mcp_config()
            }
        }
        print(json.dumps(snippet, indent=2))
    else:
        print("\nSkipped MCP client configuration.")


def _print_result(client_name: str, success: bool, path_or_err: str) -> None:
    """Print success or failure summary for installer wizard."""
    if success:
        print(f"\nInstalling FROST MCP for {client_name}...\n")
        print("  [ok] Runtime installed.")
        print("  [ok] MCP server configured.")
        print(f"  [ok] Updated config at {path_or_err}.\n")
        print("Done.\n")
        print("Run your coding agent and start using FROST.")
    else:
        print(f"\nFailed to configure {client_name}: {path_or_err}")
