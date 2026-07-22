"""FROST — Uncertainty-Aware Engineering Execution Runtime.

Three Primitives:
    frost.run("pytest tests/")
    frost.resume()
    frost.inspect()

The 3 Laws:
    #1: Nothing reasons over raw artifacts.
    #2: Nothing branches unless uncertainty exists.
    #3: Nothing lives longer than its usefulness.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from frost.orchestrator import Orchestrator, ExecutionReport
from frost.micro_branch import BranchBudget
from frost.memory import EngineeringMemory
from frost.validator import _detect_test_commands, _detect_build_commands


_LAST_REPORT: Optional[ExecutionReport] = None
_LAST_TASK: str = ""
_MEMORY: Optional[EngineeringMemory] = None


@dataclass
class FrostResult:
    """Result of a FROST execution."""
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


def run(
    goal: str,
    *,
    constraints: Optional[list[str]] = None,
    timeout: int = 3600,
    image: str = "",
    workdir: str = "",
    cache_key: str = "",
) -> FrostResult:
    """Execute an engineering task.

    Linear execution is the default. If linear execution hits uncertainty,
    micro-branching activates to explore and resolve alternatives.
    """
    global _LAST_REPORT, _LAST_TASK, _MEMORY

    if not goal:
        return FrostResult(task=goal, status="failed", error="No task provided")

    _LAST_TASK = goal
    start = time.time()

    max_retries = 10
    if constraints:
        for c in constraints:
            if c.startswith("max_retries="):
                try:
                    max_retries = int(c.split("=", 1)[1])
                except ValueError:
                    pass

    resolved_workdir = workdir or os.environ.get("FROST_WORKDIR", os.getcwd())

    # Initialize memory
    if _MEMORY is None:
        _MEMORY = EngineeringMemory(session_id=f"frost-{hash(goal) % 100000:05d}")

    # Orchestrator: linear-first with micro-branching at uncertainty
    orchestrator = Orchestrator(
        task=goal,
        workdir=resolved_workdir,
        max_linear_retries=max_retries,
        branch_budget=BranchBudget(),
        memory=_MEMORY,
        timeout=timeout,
    )

    # Resolve executable command
    executable = _resolve_command(goal, resolved_workdir)

    report = orchestrator.execute(executable)
    _LAST_REPORT = report

    elapsed = time.time() - start

    return FrostResult(
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


def resume() -> FrostResult:
    """Resume the last execution. Memory skips previously failed strategies."""
    global _LAST_TASK
    if not _LAST_TASK:
        return FrostResult(status="failed", error="No previous session to resume")
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


def _resolve_command(task: str, workdir: str) -> str:
    """Return explicit command string without fragile NLP heuristics."""
    return task.strip()


class FrostCallable:
    """frost(task) / frost.run(task) / frost.resume() / frost.inspect()"""
    def __call__(self, *args, **kwargs) -> FrostResult:
        return run(*args, **kwargs)

    run = staticmethod(run)
    resume = staticmethod(resume)
    inspect = staticmethod(inspect)


frost = FrostCallable()
