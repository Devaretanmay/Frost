"""Native execution backend for FROST (Level 0 - Zero Overhead)."""

import os
import subprocess
import sys
from typing import Any, Callable, Optional, Tuple


class NativeBackend:
    """Level 0 Native execution backend.
    
    Executes commands directly on the host machine using lightweight subprocesses.
    Zero container spinup overhead (~10ms execution latency).
    """

    def __init__(
        self,
        image: str = "",
        resource_args: Optional[list[str]] = None,
        network_args: Optional[list[str]] = None,
        timeout: int = 3600,
        workdir: str = "",
    ):
        self.timeout = timeout
        self.workdir = workdir or os.getcwd()
        self._container = "native"

    def start(self) -> str:
        """Start native backend (no-op, instant)."""
        return "native"

    def stop(self) -> None:
        """Stop native backend (no-op)."""
        pass

    def commit(self, repository: str, tag: str) -> None:
        """Checkpoint commit (no-op for native)."""
        pass

    def execute_cli(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
    ) -> Tuple[int, str, str]:
        """Execute command natively on host machine."""
        effective_cwd = cwd or self.workdir
        merged_env = {**os.environ, **(env or {})}

        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=effective_cwd,
                env=merged_env,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode("utf-8") if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = e.stderr.decode("utf-8") if isinstance(e.stderr, bytes) else (e.stderr or "")
            return 124, stdout, f"Command timed out after {self.timeout}s\n{stderr}"
        except Exception as e:
            return 1, "", str(e)

    def execute_callable(self, target: Callable[[], Any]) -> Tuple[int, str, str]:
        """Execute a Python callable in-process."""
        import io
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf_out, buf_err
        try:
            res = target()
            sys.stdout, sys.stderr = old_out, old_err
            out_str = buf_out.getvalue()
            if res is not None and not out_str:
                out_str = str(res)
            return 0, out_str, buf_err.getvalue()
        except Exception as e:
            sys.stdout, sys.stderr = old_out, old_err
            return 1, buf_out.getvalue(), str(e)
