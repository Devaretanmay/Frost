"""FROST MCP Server — one single tool for engineering execution.

Input:
    { "task": "...", "constraints": [] }

Output:
    { "status": "...", "summary": "...", "output": "...", "next_steps": "..." }
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from frost.core import frost as _frost

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None


def create_server() -> Any:
    """Create and return the FROST FastMCP server instance with ONE single tool."""
    if FastMCP is None:
        print("MCP SDK required: pip install mcp", file=sys.stderr)
        sys.exit(1)

    mcp = FastMCP("FROST")

    @mcp.tool()
    def frost(
        task: str,
        constraints: list[str] | None = None,
        timeout: int = 3600,
        image: str = "",
        workdir: str = "",
        cache_key: str = "",
    ) -> str:
        """Execute an engineering problem. FROST decides all machinery internally.

        Args:
            task: Engineering task or CLI command to execute.
            constraints: Optional constraints.
            timeout: Maximum execution time in seconds (default: 3600).
            image: Docker image override if container isolation is required.
            workdir: Working directory override.
            cache_key: Optional deterministic key for result caching.

        Returns:
            JSON with execution outcome, summary, and next steps.
        """
        result = _frost(
            goal=task,
            constraints=constraints or [],
            timeout=timeout,
            image=image,
            workdir=workdir,
            cache_key=cache_key,
        )

        status_text = "completed successfully" if result.status in ("success", "cached") else "failed"

        if result.mode == "branching":
            summary = (
                f"Task {status_text} in {result.execution_time_s:.2f}s. "
                f"Uncertainty points: {result.uncertainty_points}, "
                f"resolved: {result.uncertainty_resolved}. "
                f"Token reduction: {result.token_reduction_pct:.0f}%."
            )
        else:
            summary = f"Task {status_text} in {result.execution_time_s:.2f}s across {result.retries + 1} attempt(s)."

        next_steps = "Proceed to next task." if result.status in ("success", "cached") else "Inspect failure log and attempt code fix."

        response: dict[str, Any] = {
            "status": result.status,
            "summary": summary,
            "output": result.output,
            "error": result.error,
            "next_steps": next_steps,
            "retries": result.retries,
            "cached": result.cached,
            "mode": result.mode,
        }

        if result.uncertainty_points > 0:
            response["uncertainty_points"] = result.uncertainty_points
            response["uncertainty_resolved"] = result.uncertainty_resolved
            response["branches_spawned"] = result.branches_spawned
            response["branches_killed"] = result.branches_killed
            response["token_reduction_pct"] = result.token_reduction_pct
            if result.winning_fix:
                response["winning_fix"] = result.winning_fix

        return json.dumps(response, indent=2)

    return mcp


def run_server(*, sse: bool = False, host: str = "0.0.0.0", port: int = 8080) -> None:
    mcp = create_server()
    if sse:
        mcp.run(transport="sse", host=host, port=port)
    else:
        mcp.run(transport="stdio")


def main() -> int:
    parser = argparse.ArgumentParser(description="FROST MCP Server")
    parser.add_argument("--sse", action="store_true", help="Use SSE transport")
    parser.add_argument("--host", default="0.0.0.0", help="Host address for SSE")
    parser.add_argument("--port", type=int, default=8080, help="Port for SSE")
    args = parser.parse_args()
    run_server(sse=args.sse, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
