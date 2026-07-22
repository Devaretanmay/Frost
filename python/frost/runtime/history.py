from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class Attempt:
    index: int
    command: str
    exit_code: int
    stdout: str
    stderr: str
    started_at: float
    duration_s: float
    error: Optional[str] = None

@dataclass
class WorkflowHistory:
    session_id: str
    task: str = ""
    attempts: list[Attempt] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    status: str = "running"

    def record(self, attempt: Attempt) -> None:
        self.attempts.append(attempt)

    @property
    def failures(self) -> int:
        return sum(1 for a in self.attempts if a.exit_code != 0)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "task": self.task,
            "status": self.status,
            "attempts": len(self.attempts),
            "failures": self.failures,
            "duration_s": round(sum(a.duration_s for a in self.attempts), 2),
            "artifacts": self.artifacts,
            "history": [
                {
                    "index": a.index,
                    "command": a.command,
                    "exit_code": a.exit_code,
                    "stdout": a.stdout,
                    "stderr": a.stderr,
                    "duration_s": round(a.duration_s, 2),
                    "error": a.error,
                }
                for a in self.attempts
            ],
        }
