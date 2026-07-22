"""frost — developer CLI for FROST engineering execution."""

from __future__ import annotations

import argparse
import sys
from frost import frost
from frost.server import run_server
from frost.installer import run_init_wizard


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the FROST MCP server."""
    run_server(sse=args.sse, host=args.host, port=args.port)
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Run local-first client installer wizard."""
    run_init_wizard(choice=args.select)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Execute a command via FROST runtime."""
    cmd = " ".join(args.command)
    res = frost(cmd, image=args.image, workdir=args.workdir, timeout=args.timeout)
    out = res.output or res.error or ""
    if out:
        print(out.strip())
    print(f"[{res.status}] Completed in {res.execution_time_s:.2f}s ({res.retries} attempts)")
    return 0 if res.status in ("success", "cached") else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="frost",
        description="FROST — engineering execution CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # frost init
    init_p = sub.add_parser("init", help="Configure local MCP client (Claude Code, Cursor, VS Code, etc.)")
    init_p.add_argument("--select", type=int, default=None, help="Directly select client option [1-7]")
    init_p.set_defaults(func=cmd_init)

    # frost serve
    serve_p = sub.add_parser("serve", help="Start the FROST MCP server")
    serve_p.add_argument("--sse", action="store_true", help="Use SSE transport")
    serve_p.add_argument("--host", default="0.0.0.0", help="Host for SSE")
    serve_p.add_argument("--port", type=int, default=8080, help="Port for SSE")
    serve_p.set_defaults(func=cmd_serve)

    # frost run <command>
    run_p = sub.add_parser("run", help="Execute a task via FROST")
    run_p.add_argument("command", nargs="+", help="Command or task to execute")
    run_p.add_argument("--image", default="", help="Docker image override (Level 3)")
    run_p.add_argument("--workdir", default="", help="Working directory override")
    run_p.add_argument("--timeout", type=int, default=3600, help="Timeout in seconds")
    run_p.set_defaults(func=cmd_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        return args.func(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
