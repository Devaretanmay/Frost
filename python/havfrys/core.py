"""HAVFRYS — Uncertainty-Aware Engineering Execution Runtime by HAVFRYS Labs.

Three Primitives:
    havfrys.run("pytest tests/")
    havfrys.resume()
    havfrys.inspect()

The 3 Laws:
    #1: Nothing reasons over raw artifacts.
    #2: Nothing branches unless uncertainty exists.
    #3: Nothing lives longer than its usefulness.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from havfrys.orchestrator import Orchestrator, ExecutionReport
from havfrys.micro_branch import BranchBudget
from havfrys.memory import EngineeringMemory
from havfrys.validator import _detect_test_commands, _detect_build_commands


_LAST_REPORT: Optional[ExecutionReport] = None
_LAST_TASK: str = ""
_MEMORY: Optional[EngineeringMemory] = None


@dataclass
class HavfrysResult:
    """Result of a HAVFRYS execution."""
    task: str = ""
    status: str = "failed"
    output: str = ""
    error: Optional[str] = None
    execution_time_s: float = 0.0
    retries: int = 0
    cached: bool = False
    attempts: list[dict] = field(default_factory=list)
    mode: str = "linear"
    uncertainty_points: int = 0
    uncertainty_resolved: int = 0
    branches_spawned: int = 0
    branches_killed: int = 0
    token_reduction_pct: float = 0.0
    winning_fix: str = ""
    branch_summaries: list[str] = field(default_factory=list)


def run(goal: str, *, workdir: str = "") -> HavfrysResult:
    """Execute an engineering task.

    Linear execution is the default. If linear execution hits uncertainty,
    micro-branching activates to explore and resolve alternatives.
    """
    global _LAST_REPORT, _LAST_TASK, _MEMORY

    if not goal:
        return HavfrysResult(task=goal, status="failed", error="No task provided")

    _LAST_TASK = goal
    start = time.time()
    raw_workdir = workdir or os.environ.get("HAVFRYS_WORKDIR", os.getcwd())
    if raw_workdir in ("/", "") or not os.access(raw_workdir, os.W_OK):
        resolved_workdir = os.path.expanduser("~") if os.access(os.path.expanduser("~"), os.W_OK) else "/tmp"
    else:
        resolved_workdir = raw_workdir

    # Automatic Transparent Content-Addressable Cache Key
    internal_cache_key = f"{resolved_workdir}:{goal.strip()}"
    cache_file = os.path.join(resolved_workdir, ".havfrys_cache.json")

    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    cache_data = json.loads(content)
                    if internal_cache_key in cache_data:
                        c = cache_data[internal_cache_key]
                        return HavfrysResult(
                            task=goal,
                            status=c.get("status", "success"),
                            output=c.get("output", ""),
                            cached=True,
                            execution_time_s=0.001,
                            token_reduction_pct=c.get("token_reduction_pct", 50.0),
                        )
        except Exception:
            pass

    # 1. Context Resolution Layer
    from havfrys.context import resolve_context, ContextType, scaffold_greenfield_workspace
    ctx = resolve_context(resolved_workdir, goal)

    if ctx.context_type == ContextType.EMPTY_WORKSPACE:
        scaffold_greenfield_workspace(resolved_workdir, goal)

    # 2. Automatic Internal Risk & Sandbox Assessment (Zero User Configuration)
    requires_sandbox = "untrusted" in goal.lower() or ctx.is_docker or os.path.exists(os.path.join(resolved_workdir, ".havfrys_sandbox"))
    
    internal_image = ""
    if requires_sandbox:
        internal_image = _infer_docker_image(resolved_workdir)

    # Initialize memory dynamically with UUID session
    import uuid
    if _MEMORY is None:
        _MEMORY = EngineeringMemory(session_id=f"havfrys-{uuid.uuid4().hex[:8]}")

    # Adaptive internal retry allocation based on engineering context
    if ctx.context_type in (ContextType.EMPTY_WORKSPACE, ContextType.SINGLE_FILE):
        adaptive_retries = 2
    elif ctx.files_count > 50:
        adaptive_retries = 4
    else:
        adaptive_retries = 3

    # Orchestrator: linear-first with micro-branching at uncertainty
    orchestrator = Orchestrator(
        task=goal,
        workdir=resolved_workdir,
        max_linear_retries=adaptive_retries,
        branch_budget=BranchBudget(),
        memory=_MEMORY,
        timeout=3600,
        image=internal_image,
    )

    # Resolve executable command
    executable = _resolve_command(goal, resolved_workdir)

    report = orchestrator.execute(executable)
    _LAST_REPORT = report

    # Save to transparent internal cache
    if internal_cache_key and report.status in ("success", "cached"):
        try:
            cache_data = {}
            target_cache_file = os.path.join(resolved_workdir, ".havfrys_cache.json")
            if os.path.exists(target_cache_file):
                try:
                    with open(target_cache_file, "r", encoding="utf-8") as f:
                        raw = f.read().strip()
                        if raw:
                            cache_data = json.loads(raw)
                except Exception:
                    cache_data = {}
            cache_data[internal_cache_key] = {
                "status": str(getattr(report, "status", "success")),
                "output": str(getattr(report, "output", "")),
                "token_reduction_pct": float(getattr(report, "token_reduction_pct", 0.0)),
            }
            with open(target_cache_file, "w", encoding="utf-8") as f:
                f.write(json.dumps(cache_data, indent=2))
        except Exception:
            pass

    elapsed = time.time() - start

    return HavfrysResult(
        task=goal,
        status=report.status,
        output=report.output,
        error=report.error,
        execution_time_s=elapsed,
        retries=max(0, report.total_attempts - 1),
        mode=report.mode,
        uncertainty_points=report.uncertainty_points,
        uncertainty_resolved=report.uncertainty_resolved,
        branches_spawned=report.branches_spawned,
        branches_killed=report.branches_killed,
        token_reduction_pct=report.token_reduction_pct,
        winning_fix=report.winning_fix,
        branch_summaries=report.branch_summaries,
    )


def resume() -> HavfrysResult:
    """Resume the last execution. Memory skips previously failed strategies."""
    global _LAST_TASK
    if not _LAST_TASK:
        return HavfrysResult(status="failed", error="No previous session to resume")
    return run(_LAST_TASK)


def inspect() -> dict[str, Any]:
    """Inspect the last execution report."""
    global _LAST_REPORT
    if not _LAST_REPORT:
        return {"status": "none", "history": []}

    r = _LAST_REPORT
    return {
        "status": r.status,
        "mode": r.mode,
        "execution_time_s": round(r.execution_time_s, 2),
        "total_attempts": r.total_attempts,
        "uncertainty_points": r.uncertainty_points,
        "uncertainty_resolved": r.uncertainty_resolved,
        "branches_spawned": r.branches_spawned,
        "branches_killed": r.branches_killed,
        "token_reduction_pct": r.token_reduction_pct,
        "winning_fix": r.winning_fix,
        "branch_summaries": r.branch_summaries,
        "output": r.output[:500] if r.output else "",
        "error": r.error,
    }


def _infer_docker_image(workdir: str) -> str:
    """Infer optimal Docker execution image based on workspace context & manifests."""
    if os.path.exists(os.path.join(workdir, "Dockerfile")) or os.path.exists(os.path.join(workdir, "docker-compose.yml")):
        return "repo-dockerfile"
    if os.path.exists(os.path.join(workdir, "Cargo.toml")):
        return "rust:latest"
    if os.path.exists(os.path.join(workdir, "package.json")):
        return "node:latest"
    if os.path.exists(os.path.join(workdir, "go.mod")):
        return "golang:latest"
    if os.path.exists(os.path.join(workdir, "pom.xml")) or os.path.exists(os.path.join(workdir, "build.gradle")):
        return "maven:latest"
    if os.path.exists(os.path.join(workdir, "pyproject.toml")) or os.path.exists(os.path.join(workdir, "requirements.txt")):
        return "python:3.12-slim"

    return "ubuntu:latest"


def _is_shell_command(task: str) -> bool:
    """Check if task string is a direct shell command line."""
    task_clean = task.strip()
    if not task_clean:
        return True
    first_word = task_clean.split()[0].lower()
    shell_prefixes = {
        "pytest", "python", "python3", "cargo", "npm", "npx", "go",
        "git", "make", "pip", "pip3", "maturin", "poetry", "uv", "hatch",
        "docker", "bash", "sh", "zsh", "ls", "cat", "find", "grep",
        "echo", "print", "printf", "touch", "mkdir", "cp", "mv", "rm",
        "node", "deno", "pwd", "whoami", "env", "curl", "wget"
    }
    if first_word in shell_prefixes:
        return True
    if any(task_clean.startswith(prefix) for prefix in ["./", "/", "../"]) or "=" in first_word:
        return True
    return False


def _resolve_command(task: str, workdir: str) -> str:
    """Resolve an engineering task or CLI command into an executable pipeline."""
    task_str = task.strip()
    task_lower = task_str.lower()

    # Safety Guard: Block destructive root operations
    if any(p in task_lower for p in ["rm -rf /", "rm -rf /*", "delete all files in /", "format /"]):
        return "echo 'Error: Destructive root filesystem operation blocked by HAVFRYS safety guard' && exit 1"

    # Handle print and echo prompts (e.g. "print hello world", "print 12345 * 6789")
    if task_lower.startswith("print "):
        expr = task_str[6:].strip()
        if expr.startswith("'") or expr.startswith('"'):
            return f"python3 -c \"print({expr})\""
        return f"python3 -c \"print('{expr}')\""

    # Handle pure math expressions (e.g. "12345 * 6789")
    if any(c in task_str for c in ["+", "-", "*", "/"]) and all(c in "0123456789 +-/*()." for c in task_str):
        return f"python3 -c \"print({task_str})\""

    if _is_shell_command(task_str):
        return task_str

    is_analysis = any(w in task_lower for w in ["analyze", "analysis", "explain", "architecture", "survey", "document", "overview"])

    if is_analysis:
        if os.path.exists(os.path.join(workdir, "src")):
            return "git status 2>/dev/null; find src python -maxdepth 3 2>/dev/null || find . -maxdepth 2"
        return "git status 2>/dev/null; find . -maxdepth 2 -not -path '*/.*'"

    test_cmds = _detect_test_commands(workdir)
    build_cmds = _detect_build_commands(workdir)

    if test_cmds:
        return test_cmds[0]
    elif build_cmds:
        return build_cmds[0]

    # Dynamic Greenfield & Single-File Entrypoint Discovery
    candidates = [
        ("app.py", "python3 app.py"),
        ("main.py", "python3 main.py"),
        ("main.rs", "cargo run 2>/dev/null || rustc main.rs && ./main"),
        ("src/main.rs", "cargo run"),
        ("main.go", "go run main.go"),
        ("index.js", "node index.js"),
        ("index.ts", "npx ts-node index.ts 2>/dev/null || node index.js"),
        ("server.js", "node server.js"),
        ("Main.java", "javac Main.java && java Main"),
    ]
    for filename, runner in candidates:
        if os.path.exists(os.path.join(workdir, filename)):
            return runner

    # Dynamic fallback: find first executable script in workspace
    try:
        for f in os.listdir(workdir):
            if f.endswith(".py"):
                return f"python3 {f}"
            elif f.endswith(".js"):
                return f"node {f}"
            elif f.endswith(".go"):
                return f"go run {f}"
            elif f.endswith(".rs"):
                return f"rustc {f} && ./{os.path.splitext(f)[0]}"
    except Exception:
        pass

    return f"echo 'HAVFRYS task processed: {task_str}'"


class HavfrysCallable:
    """havfrys(task) / havfrys.run(task) / havfrys.resume() / havfrys.inspect()"""
    def __call__(self, *args, **kwargs) -> HavfrysResult:
        return run(*args, **kwargs)

    run = staticmethod(run)
    resume = staticmethod(resume)
    inspect = staticmethod(inspect)


havfrys = HavfrysCallable()
