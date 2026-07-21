"""frost — developer CLI for FROST engineering execution.

Primary:
    frost serve              Start the MCP server for agent integration

Debug:
    frost run exec <cmd>     Execute a command in a container (for testing)
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time


def _check_docker() -> str | None:
    """Return docker path or None if not available."""
    path = shutil.which("docker")
    if not path:
        return None
    try:
        subprocess.run([path, "info"], capture_output=True, timeout=10, check=True)
        return path
    except (subprocess.CalledProcessError, OSError):
        return None


def _size_str(n_bytes: int) -> str:
    if n_bytes > 1024 * 1024:
        return f"{n_bytes / (1024 * 1024):.1f} MB"
    if n_bytes > 1024:
        return f"{n_bytes / 1024:.1f} KB"
    return f"{n_bytes} B"


# ------------------------------------------------------------------ #
# Command: frost serve
# ------------------------------------------------------------------ #


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the FROST MCP server."""
    from frost.server import run_server

    run_server(sse=args.sse, host=args.host, port=args.port)
    return 0


# ------------------------------------------------------------------ #
# Command: frost run exec  (debug utility)
# ------------------------------------------------------------------ #


def cmd_run_exec(args: argparse.Namespace) -> int:
    """Execute a shell command inside a container (debug utility)."""
    docker = _check_docker()
    if not docker:
        print("Docker is required. Install Docker and try again.", file=sys.stderr)
        return 1

    command = " ".join(args.command)
    image = args.image or os.environ.get("FROST_IMAGE", "python:3.12")
    mount = args.mount or os.environ.get("FROST_WORKDIR", os.getcwd())

    # Start container
    docker_args = [docker, "run", "-d", "--rm", "-v", f"{mount}:/workspace", "-w", "/workspace"]
    docker_args += [image, "sleep", "infinity"]
    proc = subprocess.run(
        docker_args,
        capture_output=True, text=True, timeout=30,
    )
    if proc.returncode != 0:
        print(f"Failed to start container: {proc.stderr.strip()}", file=sys.stderr)
        return 1
    container_id = proc.stdout.strip()

    # Execute command
    exec_t = time.time()
    try:
        proc = subprocess.run(
            [docker, "exec", container_id, "sh", "-c", command],
            capture_output=True, text=True, timeout=args.timeout,
        )
    except subprocess.TimeoutExpired:
        print(f"  Timed out after {args.timeout}s", file=sys.stderr)
        return 1
    finally:
        subprocess.run([docker, "rm", "-f", container_id], capture_output=True)
    exec_s = time.time() - exec_t
    stdout, stderr = proc.stdout, proc.stderr

    # Apply FROST compression
    try:
        from frost._core import route_and_compress
        stdout = route_and_compress(stdout) if stdout else stdout
        stderr = route_and_compress(stderr) if stderr else stderr
    except ImportError:
        pass

    output_size = len(stdout) + len(stderr)

    print(f"  Execution : {exec_s:.1f}s (exit code {proc.returncode})")
    print(f"  Output    : {_size_str(output_size)}")

    if proc.returncode != 0:
        print(f"  Command failed with exit code {proc.returncode}", file=sys.stderr)

    return proc.returncode


# ------------------------------------------------------------------ #
# Parser
# ------------------------------------------------------------------ #


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="frost",
        description="FROST — developer CLI for engineering execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Primary:
  frost serve              Start the MCP server

Debug:
  frost run exec 'cmd'     Execute a command in a container
        """,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # frost serve
    serve_p = sub.add_parser("serve", help="Start the FROST MCP server")
    serve_p.add_argument("--sse", action="store_true", help="Use SSE (HTTP) transport instead of stdio")
    serve_p.add_argument("--host", default="0.0.0.0", help="Host for SSE transport")
    serve_p.add_argument("--port", type=int, default=8080, help="Port for SSE transport")
    serve_p.set_defaults(func=cmd_serve)

    # frost run (debug utility)
    run_p = sub.add_parser("run", help="Debug utilities")
    run_sub = run_p.add_subparsers(dest="subcommand", required=True)

    exec_p = run_sub.add_parser("exec", help="Execute a command in a container")
    exec_p.add_argument("command", nargs="+", help="Command to execute")
    exec_p.add_argument("--image", default="", help="Docker image (default: python:3.12)")
    exec_p.add_argument("--mount", default="", help="Host directory to mount as /workspace (default: current dir)")
    exec_p.add_argument("--timeout", type=int, default=3600, help="Timeout in seconds")
    exec_p.set_defaults(func=cmd_run_exec)

    return parser


# ------------------------------------------------------------------ #
# Entry point
# ------------------------------------------------------------------ #


def main(argv: list[str] | None = None) -> int:
    """Entry point for the frost CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if hasattr(args, "func"):
        return args.func(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
