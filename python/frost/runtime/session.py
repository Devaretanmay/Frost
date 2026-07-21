"""FROST Session — autonomous workflow runtime that maximizes reuse."""

from __future__ import annotations
import json
import os
import time
import uuid
from typing import Any, Callable, Optional

from frost.backends import get_backend, DockerBackend
from frost.runtime.history import WorkflowHistory, Attempt
from frost._core import LoopEngine

from . import checkpoint as _checkpoint
from . import cache as _reuse

class Session:
    """A FROST Session orchestrating execution, loop detection, checkpointing, and reuse."""

    def __init__(
        self,
        task: str = "",
        *,
        backend: Optional[DockerBackend] = None,
        checkpoint_enabled: bool = True,
        loop_detection_enabled: bool = True,
        compression_enabled: bool = True,
        max_attempts: int = 100_000,
        input_hash: str = "",
        timeout: int = 3600,
        image: str = "",
        workdir: str = "",
    ):
        self.session_id = f"frost-{uuid.uuid4().hex[:8]}"
        self.task = task
        self.max_attempts = max_attempts
        self.timeout = timeout
        self.history = WorkflowHistory(session_id=self.session_id, task=task)
        
        self.checkpoint_enabled = checkpoint_enabled
        self.loop_detection_enabled = loop_detection_enabled
        self.compression_enabled = compression_enabled
        self.input_hash = input_hash

        self.attempt = 0
        self.loop_hits = 0
        self._loop_engine: Optional[LoopEngine] = None
        self._reused = False
        self._reuse_entry: Optional[_reuse.CacheEntry] = None
        self._entered = False
        resolved_workdir = workdir or os.environ.get("FROST_WORKDIR", "")
        self._backend = backend or get_backend(
            image=image,
            timeout=timeout,
            workdir=resolved_workdir,
        )

    def __repr__(self) -> str:
        return (f"<FROST Session {self.session_id} "
                f"attempt={self.attempt} loops={self.loop_hits}>")

    def enter(self) -> Session:
        if self.input_hash:
            entry = _reuse.lookup(self.input_hash)
            if entry and entry.status in ("success", "cached", "failed"):
                self._reused = True
                self._reuse_entry = entry
                self._entered = True
                return self

        container_id = self._backend.start()

        if self.loop_detection_enabled:
            self._loop_engine = LoopEngine(
                "max_repeats: 3\n"
                "history_window: 16\n"
                "sensitivity: default\n"
                "ignore_args: false\n"
            )

        if self.checkpoint_enabled:
            _checkpoint.create(container_id, self.session_id, 0, token_estimate=0, loop_hits=0)
            
        self._entered = True
        return self

    def exit(self) -> WorkflowHistory:
        self._backend.stop()
        if self.history.status == "running":
            self.history.status = "failed"
            
        # Store artifacts locally
        try:
            base = os.path.expanduser("~/.frost/sessions")
            os.makedirs(base, exist_ok=True)
            path = os.path.join(base, f"{self.session_id}.json")
            with open(path, "w") as fh:
                json.dump(self.history.to_dict(), fh, indent=2)
            self.history.artifacts["stored_at"] = path
        except Exception:
            pass
            
        return self.history

    def run(
        self,
        target: Callable[[], Any] | str,
        *,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        on_failure: Optional[Callable[[dict], Optional[str]]] = None,
    ) -> dict[str, Any]:
        if not self._entered:
            self.enter()

        if self._reused and self._reuse_entry:
            return {
                "status": "cached",
                "input_hash": self.input_hash,
                "result": self._reuse_entry.output,
                "token_spent": self._reuse_entry.token_spent,
                "loop_hits": self._reuse_entry.loop_hits,
                "attempts": self._reuse_entry.attempts,
            }

        while self.attempt < self.max_attempts:
            self.attempt += 1

            current_target = str(target)

            if self.loop_detection_enabled and self._loop_engine:
                tool_name = f"frost_run_{self.attempt}"
                args_json = json.dumps({"target": current_target, "attempt": self.attempt})
                if self._loop_engine.verify(tool_name, args_json) != 0:
                    self.loop_hits += 1
                    if self.checkpoint_enabled:
                        best = _checkpoint.best(self.session_id)
                        if best:
                            self._backend.stop()
                            restored_id = _checkpoint.restore(best, ["sleep", "infinity"])
                            self._backend._container = restored_id
                    continue

            started = time.time()
            if callable(target) and not isinstance(target, str):
                exit_code, out, err = self._backend.execute_callable(target)
                cmd_repr = f"python:{getattr(target, '__name__', 'target')}"
            else:
                exit_code, out, err = self._backend.execute_cli(current_target, cwd, env)
                cmd_repr = current_target
                
            if self.compression_enabled:
                from frost._core import route_and_compress
                out = route_and_compress(out) if out else out
                err = route_and_compress(err) if err else err

            err_msg = err if exit_code != 0 else None

            attempt = Attempt(
                index=self.attempt, command=cmd_repr, exit_code=exit_code,
                stdout=out, stderr=err, started_at=started,
                duration_s=time.time() - started, error=err_msg,
            )
            self.history.record(attempt)
            attempt_info = dict(
                index=attempt.index, command=attempt.command,
                exit_code=attempt.exit_code, stdout=attempt.stdout,
                stderr=attempt.stderr, started_at=attempt.started_at,
                duration_s=attempt.duration_s, error=attempt.error,
            )

            if exit_code in (126, 127):
                # Unrecoverable: command not found or not executable
                # Fail fast instead of burning all retries
                self.history.status = "failed"
                self.history.artifacts["last_stderr"] = err
                hint = (
                    "Command not found. The Docker image "
                    f"'{self._backend.image}' may be missing required tools. "
                    "Set FROST_IMAGE or pass image='...' with the right image."
                )
                self.history.artifacts["failure_hint"] = hint
                break

            if exit_code == 0:
                self.history.status = "success"
                self.history.artifacts.setdefault("last_stdout", out)
                if self.checkpoint_enabled:
                    _checkpoint.create(self._backend._container, self.session_id, self.attempt, token_estimate=0, loop_hits=self.loop_hits)
                break

            # Failure — ask agent for a better command (Path C)
            if on_failure and self.attempt < self.max_attempts:
                new_command = on_failure(attempt_info)
                if new_command is not None and new_command != current_target:
                    # Checkpoint before switching to the new command
                    if self.checkpoint_enabled:
                        _checkpoint.create(self._backend._container, self.session_id, self.attempt, token_estimate=0, loop_hits=self.loop_hits)
                    target = new_command
                    continue

            # No agent feedback or same command — checkpoint and retry with loop detection
            if self.checkpoint_enabled:
                _checkpoint.create(self._backend._container, self.session_id, self.attempt, token_estimate=0, loop_hits=self.loop_hits)

        self.exit()

        if self.input_hash:
            entry = _reuse.CacheEntry(
                input_hash=self.input_hash,
                status=self.history.status,
                output=self.history.artifacts.get("last_stdout", ""),
                token_spent=0,
                loop_hits=self.loop_hits,
                attempts=self.attempt,
            )
            _reuse.store(entry)

        return self.history.to_dict()

    def run_cli(self, command: str, **kwargs) -> dict[str, Any]:
        return self.run(command, **kwargs)

    def __enter__(self) -> Session:
        return self.enter()

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self._entered and not self._reused:
            self.exit()
        return False

def session(**kwargs) -> Session:
    return Session(**kwargs)
