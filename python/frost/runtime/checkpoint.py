"""Checkpoint/restore for FROST Sessions.

Uses docker commit/save/load for container state snapshots.
Checkpoints store filesystem state + workflow metadata (attempt count,
token estimate, loop status) so restores are cheap.
"""

from __future__ import annotations

import json
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


CHECKPOINT_VERSION = 1
CHECKPOINT_DIR = Path.home() / ".frost" / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)




@dataclass
class CheckpointMeta:
    """Metadata for one checkpoint."""
    checkpoint_id: str
    session_id: str
    timestamp: float
    attempt: int
    image_tag: str
    container_id: str
    version: int = CHECKPOINT_VERSION
    token_estimate: int = 0
    loop_hits: int = 0
    labels: dict[str, str] = field(default_factory=dict)

    @property
    def age_s(self) -> float:
        return time.time() - self.timestamp


def _tag(session_id: str, checkpoint_id: str) -> str:
    return f"frost-ckpt-{session_id}-{checkpoint_id}"


def create(container_id: str, session_id: str, attempt: int,
           token_estimate: int = 0, loop_hits: int = 0,
           labels: Optional[dict[str, str]] = None) -> CheckpointMeta:
    """Create a checkpoint from a running container.

    Uses ``docker commit`` to snapshot the container's filesystem + state.
    Returns metadata; the checkpoint image stays in the local Docker daemon.
    """
    ckpt_id = uuid.uuid4().hex[:12]
    tag = _tag(session_id, ckpt_id)

    if container_id == "native" or container_id.startswith("native"):
        meta = CheckpointMeta(
            checkpoint_id=ckpt_id,
            session_id=session_id,
            timestamp=time.time(),
            attempt=attempt,
            image_tag="native",
            container_id=container_id,
            token_estimate=token_estimate,
            loop_hits=loop_hits,
            labels=labels or {},
        )
        _save_meta(meta)
        return meta

    proc = subprocess.run(
        ["docker", "commit", container_id, tag],
        capture_output=True, text=True, timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Checkpoint failed: {proc.stderr.strip()}")

    meta = CheckpointMeta(
        checkpoint_id=ckpt_id,
        session_id=session_id,
        timestamp=time.time(),
        attempt=attempt,
        image_tag=tag,
        container_id=container_id,
        token_estimate=token_estimate,
        loop_hits=loop_hits,
        labels=labels or {},
    )
    _save_meta(meta)
    return meta


def restore(meta: CheckpointMeta, command: list[str]) -> str:
    """Restore a checkpoint into a new container.

    Runs the checkpointed image with the given command (typically
    ``["sleep", "infinity"]``). Returns the new container ID.
    """
    new_container = subprocess.run(
        ["docker", "run", "-d", "--rm", meta.image_tag] + command,
        capture_output=True, text=True, timeout=30,
    )
    if new_container.returncode != 0:
        raise RuntimeError(
            f"Restore failed: {new_container.stderr.strip()}"
        )
    return new_container.stdout.strip()


def clean(checkpoint_id: str) -> None:
    """Remove a checkpoint image and its metadata."""
    meta = load_meta(checkpoint_id)
    if meta:
        subprocess.run(
            ["docker", "rmi", meta.image_tag],
            capture_output=True, text=True, timeout=30,
        )
    _drop_meta(checkpoint_id)


def best(session_id: str) -> Optional[CheckpointMeta]:
    """Return the best (most recent, lowest loop-hits) checkpoint for a session."""
    pattern = CHECKPOINT_DIR / f"{session_id}-*.json"
    metas = []
    for p in Path(CHECKPOINT_DIR).glob(f"{session_id}-*.json"):
        try:
            data = json.loads(p.read_text())
            metas.append(_deserialize_meta(data))
        except (json.JSONDecodeError, KeyError, TypeError):
            p.unlink(missing_ok=True)
    if not metas:
        return None
    # Prefer: more recent, fewer loop hits, lower attempt
    metas.sort(key=lambda m: (m.loop_hits, -m.timestamp, m.attempt))
    return metas[0]


# -- internal helpers --------------------------------------------------------

def _meta_path(session_id: str, checkpoint_id: str) -> Path:
    return CHECKPOINT_DIR / f"{session_id}-{checkpoint_id}.json"


def _save_meta(meta: CheckpointMeta) -> None:
    try:
        path = _meta_path(meta.session_id, meta.checkpoint_id)
        path.write_text(json.dumps({
            "version": meta.version,
            "checkpoint_id": meta.checkpoint_id,
            "session_id": meta.session_id,
            "timestamp": meta.timestamp,
            "attempt": meta.attempt,
            "image_tag": meta.image_tag,
            "container_id": meta.container_id,
            "token_estimate": meta.token_estimate,
            "loop_hits": meta.loop_hits,
            "labels": meta.labels,
        }, indent=2))
    except Exception:
        pass


def load_meta(checkpoint_id: str) -> Optional[CheckpointMeta]:
    """Load checkpoint metadata by ID.

    Version-aware: handles pre-version (v0) metadata via backward compat.
    """
    for p in CHECKPOINT_DIR.glob(f"*-{checkpoint_id}.json"):
        try:
            data = json.loads(p.read_text())
            return _deserialize_meta(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            p.unlink(missing_ok=True)
    return None


def _deserialize_meta(data: dict) -> CheckpointMeta:
    """Version-aware deserialization with backward compat."""
    ver = data.get("version", 0)
    if ver == 0:
        # Pre-version metadata: fill defaults
        return CheckpointMeta(
            version=CHECKPOINT_VERSION,
            checkpoint_id=data["checkpoint_id"],
            session_id=data["session_id"],
            timestamp=data["timestamp"],
            attempt=data.get("attempt", 0),
            image_tag=data["image_tag"],
            container_id=data["container_id"],
            token_estimate=data.get("token_estimate", 0),
            loop_hits=data.get("loop_hits", 0),
            labels=data.get("labels", {}),
        )
    if ver == 1:
        return CheckpointMeta(**data)
    raise ValueError(f"Unsupported checkpoint version {ver}")

def _drop_meta(checkpoint_id: str) -> None:
    for p in CHECKPOINT_DIR.glob(f"*-{checkpoint_id}.json"):
        p.unlink(missing_ok=True)
