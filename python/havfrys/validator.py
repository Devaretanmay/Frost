"""Project detection utilities — detect build and test commands from project files.

Used by the orchestrator and core to auto-detect executable commands
when the user provides a natural language task.
"""

from __future__ import annotations

import os


def _detect_build_commands(workdir: str) -> list[str]:
    """Detect available build commands dynamically across project manifests."""
    commands = []

    manifest_map = [
        ("Cargo.toml", "cargo check"),
        ("package.json", "npm run build --if-present"),
        ("pyproject.toml", "python -m py_compile setup.py 2>/dev/null || true"),
        ("Makefile", "make -n build 2>/dev/null && make build || make"),
        ("go.mod", "go build ./..."),
        ("pom.xml", "mvn compile -q 2>/dev/null || true"),
        ("build.gradle", "./gradlew build 2>/dev/null || gradle build 2>/dev/null || true"),
        ("CMakeLists.txt", "cmake -B build && cmake --build build"),
    ]

    for manifest, cmd in manifest_map:
        if os.path.exists(os.path.join(workdir, manifest)):
            commands.append(cmd)

    return commands


def _detect_test_commands(workdir: str) -> list[str]:
    """Detect available test commands dynamically across project manifests."""
    commands = []

    test_map = [
        ("Cargo.toml", "cargo test"),
        ("package.json", "npm test --if-present"),
        ("pyproject.toml", "python -m pytest --tb=short -q"),
        ("pytest.ini", "python -m pytest --tb=short -q"),
        ("setup.cfg", "python -m pytest --tb=short -q"),
        ("go.mod", "go test ./..."),
        ("pom.xml", "mvn test -q"),
        ("build.gradle", "./gradlew test 2>/dev/null || gradle test"),
    ]

    for manifest, cmd in test_map:
        if os.path.exists(os.path.join(workdir, manifest)) and cmd not in commands:
            commands.append(cmd)

    return commands


def extract_semantic_failures(output: str) -> str:
    """Extract top failing test/build lines dynamically to pin at the head of compressed log output."""
    if not output:
        return ""

    max_lines = int(os.environ.get("HAVFRYS_FAILURE_LINES", "5"))
    failing_lines = []
    keywords = ["FAILED ", "FAIL ", "error[E", "ModuleNotFoundError:", "ImportError:", "SyntaxError:", "ERR!", "FATAL", "Exception:"]

    for line in output.splitlines():
        line_clean = line.strip()
        if any(kw in line_clean for kw in keywords):
            failing_lines.append(line_clean)
            if len(failing_lines) >= max_lines:
                break

    if not failing_lines:
        return ""

    summary_header = "[HAVFRYS Failure Analysis]\n" + "\n".join(f"• {l}" for l in failing_lines) + "\n\n"
    return summary_header
