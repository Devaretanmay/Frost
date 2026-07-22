"""Project detection utilities — detect build and test commands from project files.

Used by the orchestrator and core to auto-detect executable commands
when the user provides a natural language task.
"""

from __future__ import annotations

import os


def _detect_build_commands(workdir: str) -> list[str]:
    """Detect available build commands from project files."""
    commands = []

    if os.path.exists(os.path.join(workdir, "Cargo.toml")):
        commands.append("cargo check")
    if os.path.exists(os.path.join(workdir, "package.json")):
        commands.append("npm run build --if-present")
    if os.path.exists(os.path.join(workdir, "pyproject.toml")):
        commands.append("python -m py_compile setup.py 2>/dev/null || true")
    if os.path.exists(os.path.join(workdir, "Makefile")):
        commands.append("make -n build 2>/dev/null && make build || true")
    if os.path.exists(os.path.join(workdir, "go.mod")):
        commands.append("go build ./...")

    return commands


def _detect_test_commands(workdir: str) -> list[str]:
    """Detect available test commands from project files."""
    commands = []

    if os.path.exists(os.path.join(workdir, "Cargo.toml")):
        commands.append("cargo test")
    if os.path.exists(os.path.join(workdir, "package.json")):
        commands.append("npm test --if-present")
    if os.path.exists(os.path.join(workdir, "pyproject.toml")) or os.path.exists(os.path.join(workdir, "pytest.ini")):
        commands.append("python -m pytest --tb=short -q")
    if os.path.exists(os.path.join(workdir, "go.mod")):
        commands.append("go test ./...")

    return commands
