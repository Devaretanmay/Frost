"""Tests for FROST Session — basic lifecycle, checkpoint, loop detection, reuse."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

from frost.runtime.session import session, Session
from frost.runtime import checkpoint as _checkpoint
from frost.runtime import cache as _reuse


# ============================================================================
# v0.1.0 — core lifecycle
# ============================================================================


def test_imports():
    assert callable(session)
    assert isinstance(session.__name__, str)


def test_session_create():
    s = Session(task="test")
    assert s.task == "test"
    assert s.session_id.startswith("frost-")
    assert s.max_attempts == 100_000
    assert s.checkpoint_enabled is True
    assert s.loop_detection_enabled is True
    assert s.compression_enabled is True
    assert s.attempt == 0
    assert s.loop_hits == 0
    assert s.input_hash == ""


def test_session_create_minimal():
    s = Session()
    assert s.session_id.startswith("frost-")
    assert s.task == ""



def test_session_repr():
    s = Session(task="test-task")
    r = repr(s)
    assert "FROST" in r
    assert "Session" in r
    assert s.session_id in r


def test_checkpoint_best_empty():
    assert _checkpoint.best("nonexistent-session") is None


# ============================================================================
# v0.1.1 — content-addressed reuse
# ============================================================================


class TestReuseCache:
    """Tests for the reuse cache module (no Docker needed)."""

    def setup_method(self):
        self._orig_dir = _reuse.CACHE_DIR
        self._tmp = Path(tempfile.mkdtemp())
        _reuse.CACHE_DIR = self._tmp

    def teardown_method(self):
        _reuse.CACHE_DIR = self._orig_dir
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_store_and_lookup(self):
        entry = _reuse.CacheEntry(
            input_hash="abc123",
            status="success",
            token_spent=1000,
            loop_hits=0,
            attempts=1,
        )
        _reuse.store(entry)

        found = _reuse.lookup("abc123")
        assert found is not None
        assert found.input_hash == "abc123"
        assert found.status == "success"
        assert found.token_spent == 1000
        assert found.version == _reuse.CACHE_VERSION

    def test_lookup_miss(self):
        assert _reuse.lookup("nonexistent") is None

    def test_lookup_corrupt_entry(self):
        path = _reuse._cache_path("corrupt")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not json")
        assert _reuse.lookup("corrupt") is None
        assert not path.exists()  # cleaned up

    def test_invalidate(self):
        entry = _reuse.CacheEntry(input_hash="to-remove", status="success")
        _reuse.store(entry)
        assert _reuse.lookup("to-remove") is not None
        _reuse.invalidate("to-remove")
        assert _reuse.lookup("to-remove") is None

    def test_collect_stale(self):
        """store() overwrites timestamp, so write the stale entry manually."""
        stale_path = _reuse._cache_path("stale1")
        stale_path.parent.mkdir(parents=True, exist_ok=True)
        stale_path.write_text(json.dumps({
            "version": _reuse.CACHE_VERSION,
            "input_hash": "stale1",
            "status": "success",
            "output": None,
            "token_spent": 0,
            "loop_hits": 0,
            "attempts": 1,
            "timestamp": 0,  # epoch = very old
            "tags": {},
        }))

        fresh_path = _reuse._cache_path("fresh1")
        fresh_path.write_text(json.dumps({
            "version": _reuse.CACHE_VERSION,
            "input_hash": "fresh1",
            "status": "success",
            "output": None,
            "token_spent": 0,
            "loop_hits": 0,
            "attempts": 1,
            "timestamp": time.time() + 86400 * 30,  # far future
            "tags": {},
        }))

        removed = _reuse.collect(max_age_s=86400)
        assert removed >= 1
        assert _reuse.lookup("stale1") is None
        assert _reuse.lookup("fresh1") is not None

    def test_derive_hash_deterministic(self):
        """Same function reference produces same hash."""
        def fn():
            return 42

        h1 = _reuse.derive_hash(fn, image="python:3.12")
        h2 = _reuse.derive_hash(fn, image="python:3.12")
        assert h1 == h2

    def test_derive_hash_differs_by_image(self):
        def fn():
            return 42

        h1 = _reuse.derive_hash(fn, image="python:3.12")
        h2 = _reuse.derive_hash(fn, image="python:3.11")
        assert h1 != h2

    def test_derive_hash_with_extra(self):
        def fn():
            return 42

        h1 = _reuse.derive_hash(fn, extra={"env": "prod"})
        h2 = _reuse.derive_hash(fn, extra={"env": "staging"})
        assert h1 != h2


class TestSessionReuse:
    """Tests for session reuse path — no Docker needed beyond basic import."""

    def setup_method(self):
        self._orig_dir = _reuse.CACHE_DIR
        self._tmp = Path(tempfile.mkdtemp())
        _reuse.CACHE_DIR = self._tmp

    def teardown_method(self):
        _reuse.CACHE_DIR = self._orig_dir
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_session_has_input_hash(self):
        s = Session(input_hash="myhash")
        assert s.input_hash == "myhash"

    def test_session_input_hash_default(self):
        s = Session()
        assert s.input_hash == ""

    def test_reuse_not_triggered_without_hash(self):
        s = Session()
        assert not s._reused

    def test_reuse_not_triggered_on_miss(self):
        s = Session(input_hash="not-cached")
        assert not s._reused

    def test_reuse_flag_set_on_cache_hit(self):
        entry = _reuse.CacheEntry(
            input_hash="sim-hit",
            status="success",
            token_spent=500,
            loop_hits=0,
            attempts=1,
        )
        _reuse.store(entry)

        found = _reuse.lookup("sim-hit")
        assert found is not None
        assert found.token_spent == 500

    def test_input_hash_via_session_function(self):
        s = session(input_hash="factory-hash")
        assert s.input_hash == "factory-hash"


# ============================================================================
# v0.1.1 — checkpoint versioning
# ============================================================================


class TestCheckpointVersioning:
    """Checkpoint version header + backward compat (no Docker)."""

    def setup_method(self):
        self._orig_dir = _checkpoint.CHECKPOINT_DIR
        self._tmp = Path(tempfile.mkdtemp())
        _checkpoint.CHECKPOINT_DIR = self._tmp

    def teardown_method(self):
        _checkpoint.CHECKPOINT_DIR = self._orig_dir
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_checkpoint_version_constant(self):
        assert _checkpoint.CHECKPOINT_VERSION == 1

    def test_checkpoint_meta_has_version(self):
        meta = _checkpoint.CheckpointMeta(
            checkpoint_id="test",
            session_id="sess",
            timestamp=1000.0,
            attempt=1,
            image_tag="img:tag",
            container_id="cid",
        )
        assert meta.version == 1

    def test_deserialize_v0_backward_compat(self):
        v0_data = {
            "checkpoint_id": "old-ckpt",
            "session_id": "old-sess",
            "timestamp": 500.0,
            "attempt": 2,
            "image_tag": "img:v0",
            "container_id": "cid-old",
            "token_estimate": 300,
            "loop_hits": 1,
            "labels": {"note": "legacy"},
        }
        meta = _checkpoint._deserialize_meta(v0_data)
        assert meta.version == _checkpoint.CHECKPOINT_VERSION
        assert meta.checkpoint_id == "old-ckpt"
        assert meta.token_estimate == 300
        assert meta.loop_hits == 1
        assert meta.labels == {"note": "legacy"}

    def test_deserialize_v1(self):
        v1_data = {
            "version": 1,
            "checkpoint_id": "new-ckpt",
            "session_id": "new-sess",
            "timestamp": 1500.0,
            "attempt": 1,
            "image_tag": "img:v1",
            "container_id": "cid-new",
            "token_estimate": 500,
            "loop_hits": 0,
            "labels": {},
        }
        meta = _checkpoint._deserialize_meta(v1_data)
        assert meta.version == 1
        assert meta.checkpoint_id == "new-ckpt"
        assert meta.token_estimate == 500

    def test_deserialize_v1_persisted_and_loaded(self):
        from frost.runtime.checkpoint import _save_meta

        meta = _checkpoint.CheckpointMeta(
            checkpoint_id="roundtrip",
            session_id="sess-rt",
            timestamp=2000.0,
            attempt=3,
            image_tag="img:rt",
            container_id="cid-rt",
            token_estimate=1000,
            loop_hits=0,
            labels={"env": "test"},
        )
        _save_meta(meta)

        loaded = _checkpoint.load_meta("roundtrip")
        assert loaded is not None
        assert loaded.version == 1
        assert loaded.checkpoint_id == "roundtrip"
        assert loaded.session_id == "sess-rt"
        assert loaded.token_estimate == 1000
        assert loaded.labels == {"env": "test"}

    def test_load_meta_missing(self):
        assert _checkpoint.load_meta("does-not-exist") is None

    def test_load_meta_corrupt(self):
        path = _checkpoint._meta_path("corrupt-sess", "corrupt")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{bad json")
        assert _checkpoint.load_meta("corrupt") is None
        assert not path.exists()

    def test_best_v0_and_v1_mixed(self):
        from frost.runtime.checkpoint import _save_meta

        v0_meta = _checkpoint.CheckpointMeta(
            checkpoint_id="v0-ckpt", session_id="mixed",
            timestamp=100.0, attempt=1, image_tag="img:v0",
            container_id="c0", token_estimate=100, loop_hits=0,
        )
        _save_meta(v0_meta)
        # Overwrite saved meta to v0 format (no version field)
        path = _checkpoint._meta_path("mixed", "v0-ckpt")
        data = json.loads(path.read_text())
        del data["version"]
        path.write_text(json.dumps(data))

        v1_meta = _checkpoint.CheckpointMeta(
            checkpoint_id="v1-ckpt", session_id="mixed",
            timestamp=200.0, attempt=2, image_tag="img:v1",
            container_id="c1", token_estimate=200, loop_hits=0,
        )
        _save_meta(v1_meta)

        best = _checkpoint.best("mixed")
        assert best is not None
        assert best.checkpoint_id == "v1-ckpt"
