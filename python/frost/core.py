"""FROST — engineering execution for AI agents.

One tool. One capability: solve engineering problems efficiently.

Usage:
    from frost import frost

    result = frost("Fix the failing tests in this repository")
    result = frost("Refactor the auth module", constraints=["Do not modify public APIs"])

Everything else — sessions, compression, checkpointing, caching,
loop detection, Docker — is an internal implementation detail.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Optional

from frost.runtime.session import Session


@dataclass
class FrostResult:
    """Result of a FROST execution.

    Attributes:
        task: The original task that was executed.
        status: "success" | "failed" | "cached"
        output: Compressed output from the best attempt.
        error: Error message if execution failed.
        execution_time_s: Total wall-clock time in seconds.
        retries: Number of retry attempts.
        cached: Whether result was served from cache.
        attempts: List of per-attempt details (command, exit_code, etc.).
    """

    task: str = ""
    status: str = "failed"
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time_s: float = 0.0
    retries: int = 0
    cached: bool = False
    attempts: list[dict] = field(default_factory=list)


def frost(
    goal: str,
    *,
    constraints: Optional[list[str]] = None,
    timeout: int = 3600,
    image: str = "",
    workdir: str = "",
    cache_key: str = "",
) -> FrostResult:
    """Solve an engineering task with FROST optimization.

    Creates an isolated session, executes the task, and applies
    automatic retries, loop detection, checkpointing, compression,
    and caching. Returns the best result across all attempts.

    The calling agent provides the intelligence. FROST provides the
    execution optimization — isolation, retries, checkpointing,
    compression, caching, and loop detection::

        result = frost("Fix the failing tests in tests/")
        result = frost("Refactor the auth module",
                       constraints=["Do not modify public APIs"])

    Args:
        goal: The engineering task to solve.
        constraints: Optional list of constraints like
                     ``["max_retries=5"]``.
        timeout: Maximum execution time in seconds (default: 3600).
        image: Docker image for execution isolation
               (default: python:3.12, or ``$FROST_IMAGE``).
        workdir: Host directory to mount into the container as the
                 working directory (default: current directory,
                 or ``$FROST_WORKDIR``).
        cache_key: Optional deterministic key for result caching
                   across sessions.

    Returns:
        FrostResult with the best execution outcome.
    """
    if not goal:
        return FrostResult(task=goal, status="failed", error="No task provided")

    start = time.time()

    # Parse constraints
    max_retries = 10
    if constraints:
        for c in constraints:
            if c.startswith("max_retries="):
                try:
                    max_retries = int(c.split("=", 1)[1])
                except ValueError:
                    pass

    # Default workdir to current directory so project files are accessible
    resolved_workdir = workdir or os.environ.get("FROST_WORKDIR", os.getcwd())

    # Create and run session with FROST optimizations
    sess = Session(
        task=goal[:80],
        max_attempts=max_retries,
        input_hash=cache_key,
        timeout=timeout,
        image=image,
        workdir=resolved_workdir,
    )

    try:
        result = sess.run(goal)
        elapsed = time.time() - start
        status = result.get("status", "failed")
        # Build output — use stdout on success, stderr on failure
        artifacts = result.get("artifacts", {})
        output = artifacts.get("last_stdout", "")
        if status != "success" and not output:
            # Include stderr so the agent can see what went wrong
            output = artifacts.get("last_stderr", "")

        # Build error message — include failure hint when available
        error = None
        if status != "success":
            base_error = (
                result.get("history", [{}])[-1].get("error", "Task failed")
                if result.get("history") else "Task failed"
            )
            hint = artifacts.get("failure_hint", "")
            error = f"{base_error}\n{hint}" if hint else base_error

        return FrostResult(
            task=goal,
            status=status,
            output=output,
            error=error,
            execution_time_s=elapsed,
            retries=result.get("attempts", 0),
            cached=status == "cached",
            attempts=result.get("history", []),
        )
    except Exception as e:
        elapsed = time.time() - start
        return FrostResult(
            task=goal,
            status="failed",
            error=str(e),
            execution_time_s=elapsed,
        )
