"""Tests for FROST — Linear-First Runtime with Micro-Branching.

Tests cover:
1. Branch Loop Detector (oscillation, stagnation, compression loops)
2. Uncertainty Detector (retry vs branch decision)
3. Micro-Branch (budget enforcement, kill semantics)
4. Orchestrator (linear path, uncertainty branching)
5. Core integration (frost.run, frost.inspect)
6. Engineering Memory (persistence, skip failed)
"""

import json
import os
import time
import pytest

from frost.core import frost, run, inspect
from frost.branch_loop import BranchLoopDetector, AttemptSignature
from frost.uncertainty import detect_uncertainty
from frost.memory import EngineeringMemory, StrategyOutcome


# ---------------------------------------------------------------------------
# Branch Loop Detector
# ---------------------------------------------------------------------------


class TestBranchLoopDetector:

    def test_no_loop_on_single_attempt(self):
        det = BranchLoopDetector()
        verdict = det.record(AttemptSignature(
            index=1, exit_code=1, output_hash="aaa", error_hash="bbb",
            diff_lines=0, tokens_spent=100,
        ))
        assert not verdict.should_kill

    def test_oscillation_detected(self):
        det = BranchLoopDetector(oscillation_window=4, stagnation_threshold=5)
        sigs = [
            AttemptSignature(index=1, exit_code=1, output_hash="A", error_hash="x", diff_lines=1, tokens_spent=50),
            AttemptSignature(index=2, exit_code=2, output_hash="B", error_hash="y", diff_lines=2, tokens_spent=50),
            AttemptSignature(index=3, exit_code=1, output_hash="A", error_hash="x", diff_lines=1, tokens_spent=50),
            AttemptSignature(index=4, exit_code=2, output_hash="B", error_hash="y", diff_lines=2, tokens_spent=50),
        ]
        for sig in sigs[:-1]:
            v = det.record(sig)
            assert not v.should_kill

        verdict = det.record(sigs[-1])
        assert verdict.should_kill
        assert verdict.loop_type == "oscillation"

    def test_no_diff_stagnation(self):
        det = BranchLoopDetector(stagnation_threshold=3)
        for i in range(3):
            verdict = det.record(AttemptSignature(
                index=i+1, exit_code=1, output_hash=f"h{i}",
                error_hash="e", diff_lines=0, tokens_spent=100,
            ))
        assert verdict.should_kill
        assert verdict.loop_type == "no_diff"

    def test_compression_loop(self):
        det = BranchLoopDetector(stagnation_threshold=3)
        for i in range(3):
            verdict = det.record(AttemptSignature(
                index=i+1, exit_code=1, output_hash="same",
                error_hash="e", diff_lines=i+1, tokens_spent=100,
            ))
        assert verdict.should_kill
        assert verdict.loop_type == "compression"

    def test_stagnation_same_exit_code(self):
        det = BranchLoopDetector(stagnation_threshold=3)
        for i in range(3):
            verdict = det.record(AttemptSignature(
                index=i+1, exit_code=2, output_hash=f"out{i}",
                error_hash=f"err{i}", diff_lines=i+1, tokens_spent=100,
            ))
        assert verdict.should_kill
        assert verdict.loop_type == "stagnation"


# ---------------------------------------------------------------------------
# Uncertainty Detector
# ---------------------------------------------------------------------------


class TestUncertaintyDetector:

    def test_first_failure_is_not_uncertainty(self):
        signal = detect_uncertainty(
            error_output="ModuleNotFoundError: No module named 'foo'",
            exit_code=1,
            attempt_number=1,
            previous_errors=[],
        )
        assert not signal.is_uncertainty

    def test_repeated_error_is_uncertainty(self):
        error = "ModuleNotFoundError: No module named 'foo'"
        signal = detect_uncertainty(
            error_output=error,
            exit_code=1,
            attempt_number=2,
            previous_errors=[error],
        )
        assert signal.is_uncertainty
        assert len(signal.suggested_fixes) > 0

    def test_unrecoverable_never_branches(self):
        signal = detect_uncertainty(
            error_output="bash: command not found",
            exit_code=127,
            attempt_number=5,
            previous_errors=["bash: command not found"] * 4,
        )
        assert not signal.is_uncertainty

    def test_ambiguous_pattern_triggers_branching(self):
        signal = detect_uncertainty(
            error_output="conflicting dependencies: pkg==1.0 vs pkg==2.0",
            exit_code=1,
            attempt_number=3,
            previous_errors=["some other error"],
        )
        assert signal.is_uncertainty
        assert signal.confidence > 0.5


# ---------------------------------------------------------------------------
# Engineering Memory
# ---------------------------------------------------------------------------


class TestEngineeringMemory:

    def test_record_and_retrieve(self, tmp_path):
        mem = EngineeringMemory(session_id="test-mem", memory_dir=tmp_path)
        mem.record(StrategyOutcome(
            strategy="fix_import", task_fingerprint="abc",
            status="failed", error="didn't work",
        ))
        mem.record(StrategyOutcome(
            strategy="shim", task_fingerprint="abc",
            status="success", score=0.9,
        ))

        assert mem.failed_strategies("abc") == ["fix_import"]
        assert mem.best_strategy("abc") == "shim"

    def test_persistence(self, tmp_path):
        mem1 = EngineeringMemory(session_id="test-persist", memory_dir=tmp_path)
        mem1.record(StrategyOutcome(
            strategy="direct", task_fingerprint="xyz",
            status="success", score=0.8,
        ))

        mem2 = EngineeringMemory(session_id="test-persist", memory_dir=tmp_path)
        assert mem2.best_strategy("xyz") == "direct"


# ---------------------------------------------------------------------------
# Core Integration
# ---------------------------------------------------------------------------


class TestCoreLinearPath:

    def setup_method(self):
        if os.path.exists(".frost_cache.json"):
            try:
                os.remove(".frost_cache.json")
            except OSError:
                pass

    def test_simple_command_succeeds_linearly(self):
        result = run("echo hello frost engine")
        assert result.status == "success"
        assert result.mode == "linear"
        assert result.uncertainty_points == 0

    def test_frost_callable(self):
        result = frost("echo callable test")
        assert result.status == "success"

    def test_empty_task_fails(self):
        result = run("")
        assert result.status == "failed"

    def test_inspect_returns_report_fields(self):
        run("echo inspect test")
        info = inspect()
        assert "mode" in info
        assert "uncertainty_points" in info
        assert info["mode"] == "linear"

    def test_failing_command_retries_linearly(self):
        result = run("bash -c 'exit 1'")
        assert result.status == "failed"
        assert result.retries >= 1
