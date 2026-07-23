"""havfrys — developer CLI for HAVFRYS engineering execution by HAVFRYS Labs."""

from __future__ import annotations

import argparse
import sys
from havfrys import havfrys
from havfrys.server import run_server
from havfrys.installer import run_init_wizard, run_doctor


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the HAVFRYS MCP server."""
    run_server(sse=args.sse, host=args.host, port=args.port)
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Run local-first client installer wizard."""
    run_init_wizard(choice=args.select, auto_all=args.all)
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Run HAVFRYS local environment diagnostics."""
    run_doctor()
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Execute a command via HAVFRYS runtime."""
    from havfrys.ui import symbol_bullet, symbol_ok, symbol_err, BOLD, GREEN, RED, CYAN, DIM, RESET
    cmd = " ".join(args.command)
    res = havfrys(cmd, workdir=args.workdir)
    out = res.output or res.error or ""
    if out:
        print(out.strip())
    
    icon = symbol_ok() if res.status in ("success", "cached") else symbol_err()
    mode_text = f"Cached Hit" if res.cached else f"{res.mode.title()} Path"
    print(f"\n{icon} {BOLD}HAVFRYS Task:{RESET} \"{cmd}\"")
    print(f"  {DIM}├─ Status: {res.status.upper()}{RESET}")
    print(f"  {DIM}├─ Mode: {mode_text}{RESET}")
    print(f"  {DIM}└─ Latency: {res.execution_time_s:.2f}s ({res.retries + 1} attempt(s)){RESET}\n")
    return 0 if res.status in ("success", "cached") else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="havfrys",
        description="HAVFRYS — engineering execution CLI by HAVFRYS Labs",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # havfrys init
    init_p = sub.add_parser("init", help="Configure local MCP client (Claude Code, Cursor, VS Code, etc.)")
    init_p.add_argument("--select", type=int, default=None, help="Directly select client option [1-9]")
    init_p.add_argument("--all", "-a", action="store_true", help="Auto-configure all detected AI coding clients")
    init_p.set_defaults(func=cmd_init)

    # havfrys doctor
    doctor_p = sub.add_parser("doctor", help="Run local environment diagnostics")
    doctor_p.set_defaults(func=cmd_doctor)

    # havfrys serve
    serve_p = sub.add_parser("serve", help="Start the HAVFRYS MCP server")
    serve_p.add_argument("--sse", action="store_true", help="Use SSE transport")
    serve_p.add_argument("--host", default="0.0.0.0", help="Host for SSE")
    serve_p.add_argument("--port", type=int, default=8080, help="Port for SSE")
    serve_p.set_defaults(func=cmd_serve)

    # havfrys run <command>
    run_p = sub.add_parser("run", help="Execute a task via HAVFRYS")
    run_p.add_argument("command", nargs="+", help="Command or task to execute")
    run_p.add_argument("--workdir", default="", help="Working directory override")
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
