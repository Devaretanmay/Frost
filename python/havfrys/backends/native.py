"""Native execution backend for HAVFRYS (Level 0 - Zero Overhead)."""

import io
import os
import subprocess
import sys
from typing import Any, Callable, Optional, Tuple


class NativeBackend:
    """Level 0 Native execution backend."""

    def __init__(self, image: str = "", resource_args=None, network_args=None, timeout: int = 3600, workdir: str = ""):
        self.image = image or "native"
        self.timeout = timeout
        self.workdir = workdir or os.getcwd()
        self._container = "native"

    def start(self) -> str:
        return "native"

    def stop(self) -> None:
        pass

    def commit(self, repository: str, tag: str) -> None:
        pass

    def execute_cli(self, command: str, cwd: Optional[str] = None, env: Optional[dict] = None) -> Tuple[int, str, str]:
        effective_cwd = cwd or self.workdir
        merged_env = {**os.environ, **(env or {})}
        try:
            proc = subprocess.run(
                command, shell=True, cwd=effective_cwd, env=merged_env, capture_output=True, text=True, timeout=self.timeout
            )
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as e:
            return 124, (e.stdout or "").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), f"Command timed out after {self.timeout}s"
        except Exception as e:
            return 1, "", str(e)

    def execute_callable(self, target: Callable[[], Any]) -> Tuple[int, str, str]:
        buf_out, buf_err = io.StringIO(), io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf_out, buf_err
        try:
            res = target()
            sys.stdout, sys.stderr = old_out, old_err
            return 0, buf_out.getvalue() or str(res or ""), buf_err.getvalue()
        except Exception as e:
            sys.stdout, sys.stderr = old_out, old_err
            return 1, buf_out.getvalue(), str(e)
