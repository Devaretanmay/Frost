"""FROST MCP Server — one tool for engineering execution optimization.

The MCP server exposes a single ``frost`` tool. AI agents call it when
they need to execute engineering tasks with automatic optimization:

    frost("Fix the failing tests in this repository")
    frost("pytest tests/ -v", constraints=["max_retries=5"])

Usage:
    frost serve              Start MCP server (stdio transport)
    frost serve --sse        Start MCP server (HTTP/SSE transport)
"""

from __future__ import annotations

import json
import sys
from typing import Any

from frost.core import frost as _frost


def create_server() -> Any:
    """Create and return the FROST FastMCP server instance with one tool."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("MCP SDK required: pip install mcp", file=sys.stderr)
        sys.exit(1)

    mcp = FastMCP("FROST")

    @mcp.tool()
    def frost(
        task: str,
        constraints: list[str] | None = None,
        timeout: int = 3600,
        image: str = "",
        cache_key: str = "",
    ) -> str:
        """Execute an engineering task with FROST optimization.

        Internally handles session management, retries, loop detection,
        checkpointing, compression, and caching. Returns the best result.

        Use this when you need to execute a task efficiently —
        FROST decides everything else internally.

        Args:
            task: CLI command to execute with optimization.
            constraints: Optional constraints like ["max_retries=5"].
            timeout: Maximum execution time in seconds (default: 3600).
            image: Docker image for execution isolation
                   (default: python:3.12-slim).
            cache_key: Optional key for result caching across sessions.

        Returns:
            JSON string with the execution outcome including
            per-attempt history.
        """
        result = _frost(
            goal=task,
            constraints=constraints or [],
            timeout=timeout,
            image=image,
            cache_key=cache_key,
        )
        return json.dumps({
            "status": result.status,
            "output": result.output,
            "error": result.error,
            "execution_time_s": result.execution_time_s,
            "retries": result.retries,
            "cached": result.cached,
            "attempts": result.attempts,
        }, indent=2)

    return mcp


def run_server(*, sse: bool = False, host: str = "0.0.0.0", port: int = 8080) -> None:
    """Start the FROST MCP server with the given transport settings."""
    mcp = create_server()

    if sse:
        mcp.run(transport="sse", host=host, port=port)
    else:
        mcp.run(transport="stdio")


def main() -> int:
    """Entry point for ``python -m frost.server``."""
    import argparse

    parser = argparse.ArgumentParser(description="FROST MCP Server")
    parser.add_argument(
        "--sse",
        action="store_true",
        help="Use SSE (HTTP) transport instead of stdio",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host address for SSE transport (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for SSE transport (default: 8080)",
    )

    args = parser.parse_args()
    run_server(sse=args.sse, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
