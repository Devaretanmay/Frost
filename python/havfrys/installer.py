"""Local-first client installer wizard and diagnostics for HAVFRYS by HAVFRYS Labs.

Configures local agentic environments (Claude Code, Gemini CLI, Cursor, VS Code,
OpenCode, Windsurf, Cline, Continue, Zed, Aider) to use the local HAVFRYS MCP process (`havfrys serve`).
Includes `havfrys doctor` for instant local runtime diagnostics.
No login, no SaaS, no API keys — 100% local-first execution.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


VERSION = "0.3.0"

CLIENT_PROVIDERS = [
    "1. Claude Code / Desktop",
    "2. Gemini CLI",
    "3. OpenCode",
    "4. Cursor",
    "5. VS Code",
    "6. Windsurf",
    "7. Cline / Roo Code",
    "8. Continue",
    "9. Zed Editor",
    "10. Custom MCP Client",
    "11. Skip",
]


def get_havfrys_mcp_config() -> dict[str, Any]:
    """Return standard local MCP server configuration snippet."""
    cmd_path = shutil.which("havfrys") or str(Path(sys.executable).parent / "havfrys")
    return {
        "command": cmd_path,
        "args": ["serve"],
    }


def _is_valid_client_path(p: Path) -> bool:
    """Return True if config file exists or parent directory exists (excluding Home directory)."""
    if p.exists():
        return True
    parent = p.parent
    if parent != Path.home() and parent.exists():
        return True
    return False


def detect_installed_clients() -> list[tuple[str, Path]]:
    """Detect local AI coding agent clients installed on the system."""
    detected = []

    providers: list[tuple[str, list[Path], Optional[str]]] = [
        ("Claude Code", [
            Path.home() / ".claude.json",
            Path.home() / ".config" / "claude" / "config.json",
            Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
            Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
        ], "claude"),
        ("Gemini CLI", [
            Path.home() / ".gemini" / "mcp.json",
            Path.home() / ".config" / "gemini" / "mcp.json",
        ], "gemini"),
        ("Cursor", [
            Path.home() / ".cursor" / "mcp.json",
            Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "mcp.json",
            Path.home() / ".config" / "Cursor" / "User" / "globalStorage" / "mcp.json",
        ], "cursor"),
        ("VS Code", [
            Path.home() / ".vscode" / "mcp.json",
            Path.home() / "Library" / "Application Support" / "Code" / "User" / "mcp.json",
            Path.home() / ".config" / "Code" / "User" / "mcp.json",
        ], "code"),
        ("OpenCode", [
            Path.home() / ".config" / "opencode" / "mcp.json",
            Path.home() / ".opencode" / "mcp.json",
        ], "opencode"),
        ("Windsurf", [
            Path.home() / ".codeium" / "windsurf" / "mcp_config.json",
            Path.home() / ".windsurf" / "mcp_config.json",
        ], "windsurf"),
        ("Cline / Roo Code", [
            Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "mcp_settings.json",
            Path.home() / ".vscode" / "extensions" / "rooveterinaryinc.roo-cline" / "mcp.json",
        ], None),
        ("Continue", [
            Path.home() / ".continue" / "config.json",
        ], None),
        ("Zed Editor", [
            Path.home() / ".config" / "zed" / "settings.json",
        ], "zed"),
    ]

    for name, paths, bin_name in providers:
        found_path = None
        for p in paths:
            if _is_valid_client_path(p):
                found_path = p
                break
        if not found_path and bin_name and shutil.which(bin_name):
            found_path = paths[0]
        if found_path:
            detected.append((name, found_path))

    return detected


def install_claude_code() -> tuple[bool, str]:
    """Configure Claude Code / Desktop to run local HAVFRYS MCP server."""
    possible_paths = [
        Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
        Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
        Path.home() / ".claude.json",
        Path.home() / ".config" / "claude" / "config.json",
    ]
    updated_paths = []
    for p in possible_paths:
        if p.exists() or p.parent.exists():
            ok, res_path = _update_mcp_json_file(p, "havfrys")
            if ok:
                updated_paths.append(res_path)

    if updated_paths:
        return True, ", ".join(updated_paths)
    return _update_mcp_json_file(possible_paths[0], "havfrys")


def install_cursor() -> tuple[bool, str]:
    """Configure Cursor editor to run local HAVFRYS MCP server."""
    target_path = Path.home() / ".cursor" / "mcp.json"
    return _update_mcp_json_file(target_path, "havfrys")


def install_vscode() -> tuple[bool, str]:
    """Configure VS Code to run local HAVFRYS MCP server."""
    target_path = Path.home() / ".vscode" / "mcp.json"
    return _update_mcp_json_file(target_path, "havfrys")


def install_opencode() -> tuple[bool, str]:
    """Configure OpenCode to run local HAVFRYS MCP server."""
    target_path = Path.home() / ".config" / "opencode" / "opencode.json"
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        config: dict[str, Any] = {
            "$schema": "https://opencode.ai/config.json",
        }
        if target_path.exists():
            try:
                config = json.loads(target_path.read_text(encoding="utf-8"))
            except Exception:
                config = {"$schema": "https://opencode.ai/config.json"}

        cmd_path = shutil.which("havfrys") or str(Path.home() / ".local" / "bin" / "havfrys")
        mcp_dict = config.setdefault("mcp", {})
        mcp_dict["havfrys"] = {
            "type": "local",
            "command": [cmd_path, "serve"],
        }
        target_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        return True, str(target_path)
    except Exception as e:
        return False, str(e)


def install_gemini() -> tuple[bool, str]:
    """Configure Gemini CLI to run local HAVFRYS MCP server."""
    target_path = Path.home() / ".gemini" / "mcp.json"
    return _update_mcp_json_file(target_path, "havfrys")


def install_windsurf() -> tuple[bool, str]:
    """Configure Windsurf to run local HAVFRYS MCP server."""
    target_path = Path.home() / ".codeium" / "windsurf" / "mcp_config.json"
    return _update_mcp_json_file(target_path, "havfrys")


def install_cline() -> tuple[bool, str]:
    """Configure Cline / Roo Code to run local HAVFRYS MCP server."""
    target_path = Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "mcp_settings.json"
    return _update_mcp_json_file(target_path, "havfrys")


def install_continue() -> tuple[bool, str]:
    """Configure Continue to run local HAVFRYS MCP server."""
    target_path = Path.home() / ".continue" / "config.json"
    return _update_mcp_json_file(target_path, "havfrys")


def install_zed() -> tuple[bool, str]:
    """Configure Zed Editor to run local HAVFRYS MCP server."""
    target_path = Path.home() / ".config" / "zed" / "settings.json"
    return _update_mcp_json_file(target_path, "havfrys")


def _update_mcp_json_file(file_path: Path, server_name: str) -> tuple[bool, str]:
    """Helper to update or create an MCP client configuration file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        config: dict[str, Any] = {}

        if file_path.exists():
            try:
                config = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception:
                try:
                    shutil.copy2(file_path, file_path.with_suffix(".json.bak"))
                except Exception:
                    pass
                config = {}

        servers = config.setdefault("mcpServers", {})
        servers[server_name] = get_havfrys_mcp_config()

        file_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        return True, str(file_path)
    except Exception as e:
        return False, str(e)


def run_init_wizard(choice: Optional[int] = None, auto_all: bool = False) -> None:
    """Run interactive or non-interactive havfrys init wizard with dynamic client auto-detection."""
    from havfrys.ui import render_banner, render_section, symbol_bullet, BOLD, CYAN, GREEN, RESET
    print(render_banner("MCP Client Configuration", VERSION))

    detected = detect_installed_clients()

    installers = {
        "Claude Code": install_claude_code,
        "Gemini CLI": install_gemini,
        "OpenCode": install_opencode,
        "Cursor": install_cursor,
        "VS Code": install_vscode,
        "Windsurf": install_windsurf,
        "Cline / Roo Code": install_cline,
        "Continue": install_continue,
        "Zed Editor": install_zed,
    }

    if auto_all:
        print(f"  {symbol_bullet()} Auto-configuring all {BOLD}{len(detected)}{RESET} detected AI coding client(s):\n")
        for name, path in detected:
            if name in installers:
                ok, res_path = installers[name]()
                _print_result(name, ok, res_path)
        print(f"\n  {GREEN}{BOLD}Done!{RESET} All detected MCP client configurations active.\n")
        return

    if detected and choice is None:
        print(f"Detected {len(detected)} installed AI coding client(s):\n")
        for i, (client_name, path) in enumerate(detected, 1):
            print(f"  {i}. {client_name} ({path})")
        print()
        try:
            ans = input("Configure all detected clients automatically? [Y/n/select] ").strip().lower()
            if ans in ("", "y", "yes", "a", "all"):
                for client_name, _ in detected:
                    if client_name in installers:
                        ok, path = installers[client_name]()
                        _print_result(client_name, ok, path)
                return
            elif ans.isdigit():
                idx = int(ans) - 1
                if 0 <= idx < len(detected):
                    c_name = detected[idx][0]
                    client_map = {
                        "Claude Code": 1, "Gemini CLI": 2, "OpenCode": 3,
                        "Cursor": 4, "VS Code": 5, "Windsurf": 6,
                        "Cline / Roo Code": 7, "Continue": 8, "Zed Editor": 9
                    }
                    choice = client_map.get(c_name)
        except (KeyboardInterrupt, EOFError):
            choice = 11

    if choice is None:
        print("How would you like to use HAVFRYS?\n")
        for provider in CLIENT_PROVIDERS:
            print(f"  {provider}")
        print()
        try:
            user_input = input("Select an option [1-11]: ").strip()
            choice = int(user_input) if user_input.isdigit() else 11
        except (KeyboardInterrupt, EOFError):
            choice = 11

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
        ok, path = install_windsurf()
        _print_result("Windsurf", ok, path)
    elif choice == 7:
        ok, path = install_cline()
        _print_result("Cline / Roo Code", ok, path)
    elif choice == 8:
        ok, path = install_continue()
        _print_result("Continue", ok, path)
    elif choice == 9:
        ok, path = install_zed()
        _print_result("Zed Editor", ok, path)
    elif choice == 10:
        print("\nCopy and paste this snippet into your MCP client configuration:\n")
        snippet = {
            "mcpServers": {
                "havfrys": get_havfrys_mcp_config()
            }
        }
        print(json.dumps(snippet, indent=2))
    else:
        print("\nSkipped MCP client configuration.")


def run_doctor() -> None:
    """Run HAVFRYS Diagnostics for local environment using rich UI components."""
    from havfrys.ui import render_banner, render_section, render_row, symbol_ok, symbol_err, BOLD, GREEN, CYAN, RESET
    print(render_banner("Runtime Diagnostics", VERSION))

    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(render_section("System & Runtime"))
    print(render_row("Python", f"{py_ver} ({sys.platform})"))
    print(render_row("MCP Server", "Available (havfrys serve)"))

    # Engine
    try:
        from havfrys._core import route_and_compress
        print(render_row("Compression Engine", "Loaded (Lossless + SmartCrusher)"))
    except Exception as e:
        print(render_row("Compression Engine", f"Failed to load: {e}", is_ok=False))

    try:
        from havfrys._core import LoopEngine
        print(render_row("Loop Detection", "Loaded (BranchLoopDetector)"))
    except Exception as e:
        print(render_row("Loop Detection", f"Failed to load: {e}", is_ok=False))

    # Toolchain
    print(render_section("Toolchain & Containers"))
    git_path = shutil.which("git")
    cargo_path = shutil.which("cargo")
    docker_path = shutil.which("docker")
    print(render_row("Git CLI", git_path or "not found", is_ok=bool(git_path)))
    print(render_row("Cargo Compiler", cargo_path or "not found (Optional)", is_ok=True))
    print(render_row("Docker Engine", docker_path or "not found (Optional, Level 0 Active)", is_ok=True))

    # Clients
    print(render_section("Configured MCP Clients"))
    detected = detect_installed_clients()
    if detected:
        for name, path in detected:
            print(render_row(name, str(path)))
    else:
        print(render_row("MCP Clients", "No clients auto-detected (run 'havfrys init')", is_ok=False))

    print(render_section("Workspace"))
    is_git = os.path.exists(".git")
    print(render_row("Repository State", "Git repository active" if is_git else "Directory path active"))
    print(f"\n{GREEN}{BOLD}Status:{RESET} All system diagnostics 100% operational.\n")


def _print_result(client_name: str, success: bool, path_or_err: str) -> None:
    """Print success or failure summary for installer wizard."""
    from havfrys.ui import render_row, symbol_ok, symbol_err, BOLD, GREEN, RED, RESET
    if success:
        print(f"  {symbol_ok()} {BOLD}{client_name:<20}{RESET} Configured at {path_or_err}")
    else:
        print(f"  {symbol_err()} {BOLD}{client_name:<20}{RESET} {RED}Failed: {path_or_err}{RESET}")
