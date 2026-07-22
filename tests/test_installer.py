"""Tests for local-first frost init wizard and client installer module."""

import json
import os
from pathlib import Path
import pytest

from frost.installer import (
    get_frost_mcp_config,
    install_claude_code,
    install_cursor,
    install_vscode,
    install_opencode,
    install_gemini,
    install_windsurf,
    install_cline,
    install_continue,
    install_zed,
    run_init_wizard,
)


class TestInstallerWizard:

    def test_get_frost_mcp_config_structure(self):
        cfg = get_frost_mcp_config()
        assert "command" in cfg
        assert cfg["args"] == ["serve"]

    def test_install_claude_code(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        ok, path = install_claude_code()
        assert ok
        assert os.path.exists(path)

        data = json.loads(Path(path).read_text())
        assert "mcpServers" in data
        assert "frost" in data["mcpServers"]
        assert data["mcpServers"]["frost"]["args"] == ["serve"]

    def test_install_cursor(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        ok, path = install_cursor()
        assert ok
        data = json.loads(Path(path).read_text())
        assert "frost" in data["mcpServers"]

    def test_install_vscode(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        ok, path = install_vscode()
        assert ok
        data = json.loads(Path(path).read_text())
        assert "frost" in data["mcpServers"]

    def test_install_windsurf(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        ok, path = install_windsurf()
        assert ok
        data = json.loads(Path(path).read_text())
        assert "frost" in data["mcpServers"]

    def test_install_cline(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        ok, path = install_cline()
        assert ok
        data = json.loads(Path(path).read_text())
        assert "frost" in data["mcpServers"]

    def test_run_init_wizard_select_claude(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        run_init_wizard(choice=1)
        out = capsys.readouterr().out
        assert "Installing FROST MCP for Claude Code" in out
        assert "Runtime installed." in out
        assert "MCP server configured." in out

    def test_run_init_wizard_custom_json(self, capsys):
        run_init_wizard(choice=10)
        out = capsys.readouterr().out
        assert "mcpServers" in out
        assert "frost" in out

    def test_run_init_wizard_skip(self, capsys):
        run_init_wizard(choice=11)
        out = capsys.readouterr().out
        assert "Skipped MCP client configuration." in out
