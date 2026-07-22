"""Reuse Cache for FROST — content-addressed workflow result storage.

The core moat: same input hash → same result → zero execution cost.
Cache keys are sha256(content_hash) where content_hash is user-provided
or derived from (target_repr + docker_image + input_context).

No session identity, no timestamp, no randomness in the key —
structurally findable across machines and sessions.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional


CACHE_DIR = Path.home() / ".frost" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Current cache entry schema version
CACHE_VERSION = 1


@dataclass
class CacheEntry:
    """One reusable workflow result."""

    version: int = CACHE_VERSION
    input_hash: str = ""
    status: str = ""                     # "success" | "cached" | "failed"
    output: Optional[str] = None         # serialized result summary
    token_spent: int = 0                 # tokens the ORIGINAL run cost
    loop_hits: int = 0
    attempts: int = 0
    timestamp: float = 0.0

    def age_seconds(self) -> float:
        return time.time() - self.timestamp


# ---------------------------------------------------------------------------
# Lookup / Store
# ---------------------------------------------------------------------------


def _cache_path(input_hash: str) -> Path:
    """File path for a cache entry.  Two-level sharding for dir scalability."""
    prefix = input_hash[:2]
    shard = CACHE_DIR / prefix
    shard.mkdir(parents=True, exist_ok=True)
    return shard / f"{input_hash}.json"


def lookup(input_hash: str) -> Optional[CacheEntry]:
    """Look up a cached result by input hash."""
    try:
        path = _cache_path(input_hash)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return _deserialize(data)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        # Corrupt or invalid entry — clean up
        try:
            path = _cache_path(input_hash)
            if path.exists():
                path.unlink(missing_ok=True)
        except Exception:
            pass
        return None
    except Exception:
        return None


def store(entry: CacheEntry) -> None:
    """Store a execution result in the cache."""
    try:
        path = _cache_path(entry.input_hash)
        entry.timestamp = time.time()
        path.write_text(json.dumps(asdict(entry), indent=2, ensure_ascii=False))
    except Exception:
        pass


def invalidate(input_hash: str) -> None:
    """Remove a cache entry."""
    path = _cache_path(input_hash)
    path.unlink(missing_ok=True)


def collect(max_age_s: float = 86400 * 30) -> int:
    """Purge entries older than *max_age_s*.  Returns count removed."""
    now = time.time()
    removed = 0
    for shard in CACHE_DIR.iterdir():
        if not shard.is_dir():
            continue
        for p in shard.iterdir():
            if p.suffix != ".json":
                continue
            try:
                raw = json.loads(p.read_text())
                age = now - raw.get("timestamp", 0)
                if age > max_age_s:
                    p.unlink()
                    removed += 1
            except (json.JSONDecodeError, OSError):
                p.unlink(missing_ok=True)
                removed += 1
    return removed


# ---------------------------------------------------------------------------
# Input hash derivation
# ---------------------------------------------------------------------------


def derive_hash(
    target: Any,
    image: str = "",
    extra: Optional[dict[str, str]] = None,
) -> str:
    """Deterministic hash from target + image + extra context.

    Two identical workflows across machines produce the same hash.
    No randomness, no identity — only computational content matters.
    """
    h = hashlib.sha256()
    if callable(target):
        import inspect
        try:
            src = inspect.getsource(target)
        except (OSError, TypeError):
            src = repr(target)
        h.update(src.encode())
    else:
        h.update(str(target).encode())
    h.update(image.encode())
    if extra:
        for k in sorted(extra.keys()):
            h.update(k.encode())
            h.update(extra[k].encode())
    return h.hexdigest()[:16]  # short enough for ergonomics


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _deserialize(raw: dict) -> CacheEntry:
    """Version-aware deserialization with backward compat."""
    ver = raw.get("version", 0)

    if ver == 0:
        # Pre-version format: minimal valid entry
        return CacheEntry(
            version=CACHE_VERSION,
            input_hash=raw.get("input_hash", ""),
            status=raw.get("status", "unknown"),
            output=raw.get("output"),
            token_spent=raw.get("token_spent", 0),
            loop_hits=raw.get("loop_hits", 0),
            attempts=raw.get("attempts", 0),
            timestamp=raw.get("timestamp", 0.0),
        )

    if ver == CACHE_VERSION:
        return CacheEntry(
            version=raw["version"],
            input_hash=raw["input_hash"],
            status=raw["status"],
            output=raw.get("output"),
            token_spent=raw.get("token_spent", 0),
            loop_hits=raw.get("loop_hits", 0),
            attempts=raw.get("attempts", 0),
            timestamp=raw.get("timestamp", 0.0),
        )

    raise ValueError(f"Unsupported cache version {ver}")
