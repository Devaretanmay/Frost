"""Branch Loop Detector — rich internal loop detection for micro-branches.

Operates inside each micro-branch to detect:

1. Code oscillation:     A → B → A → B
2. No meaningful diff:   Repository state unchanged across attempts
3. Semantic loop:        import fix → dep fix → import fix → dep fix
4. Compression loop:     Compressed output identical for N attempts
5. Token inefficiency:   Spent 20k tokens, changed 2 lines
6. Engineering stagnation: N attempts, no tests improved

HAVFRYS LAW #3: Nothing lives longer than its usefulness.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AttemptSignature:
    """Fingerprint of a single branch attempt for loop comparison."""

    index: int
    exit_code: int
    output_hash: str          # sha256 of compressed output
    error_hash: str           # sha256 of error output
    diff_lines: int           # lines changed in repo since branch start
    tokens_spent: int         # estimated tokens consumed


@dataclass
class LoopVerdict:
    """Result of loop detection analysis."""

    should_kill: bool = False
    reason: str = ""
    loop_type: str = ""       # "oscillation" | "stagnation" | "compression" | "inefficiency" | "no_diff"


class BranchLoopDetector:
    """Detects internal loops within a micro-branch's execution history.

    Instantiated per micro-branch. Fed attempt signatures as execution
    progresses. Returns kill verdicts when loops are detected.
    """

    def __init__(
        self,
        *,
        oscillation_window: int = 4,
        stagnation_threshold: int = 3,
        inefficiency_ratio: float = 5000.0,   # tokens per LOC changed
    ):
        self._history: list[AttemptSignature] = []
        self._oscillation_window = oscillation_window
        self._stagnation_threshold = stagnation_threshold
        self._inefficiency_ratio = inefficiency_ratio

    def record(self, sig: AttemptSignature) -> LoopVerdict:
        """Record an attempt and check for loops. Returns kill verdict."""
        self._history.append(sig)

        # Need at least 2 attempts for any loop detection
        if len(self._history) < 2:
            return LoopVerdict()

        # Check each loop type in order of severity
        checks = [
            self._check_oscillation,
            self._check_no_diff,
            self._check_compression_loop,
            self._check_stagnation,
            self._check_inefficiency,
        ]

        for check in checks:
            verdict = check()
            if verdict.should_kill:
                return verdict

        return LoopVerdict()

    def _check_oscillation(self) -> LoopVerdict:
        """Detect A → B → A → B output oscillation."""
        if len(self._history) < self._oscillation_window:
            return LoopVerdict()

        window = self._history[-self._oscillation_window:]
        hashes = [s.output_hash for s in window]

        # Check for ABAB pattern
        if len(hashes) >= 4:
            if hashes[-4] == hashes[-2] and hashes[-3] == hashes[-1] and hashes[-4] != hashes[-3]:
                return LoopVerdict(
                    should_kill=True,
                    reason=f"Output oscillation detected: A-B-A-B pattern over last {self._oscillation_window} attempts",
                    loop_type="oscillation",
                )

        return LoopVerdict()

    def _check_no_diff(self) -> LoopVerdict:
        """Detect no repository state change across multiple attempts."""
        if len(self._history) < self._stagnation_threshold:
            return LoopVerdict()

        recent = self._history[-self._stagnation_threshold:]
        if all(s.diff_lines == 0 for s in recent):
            return LoopVerdict(
                should_kill=True,
                reason=f"No repository state change after {self._stagnation_threshold} attempts",
                loop_type="no_diff",
            )

        return LoopVerdict()

    def _check_compression_loop(self) -> LoopVerdict:
        """Detect identical compressed output across consecutive attempts."""
        if len(self._history) < self._stagnation_threshold:
            return LoopVerdict()

        recent = self._history[-self._stagnation_threshold:]
        output_hashes = [s.output_hash for s in recent]

        if len(set(output_hashes)) == 1:
            return LoopVerdict(
                should_kill=True,
                reason=f"Compressed output identical for {self._stagnation_threshold} consecutive attempts",
                loop_type="compression",
            )

        return LoopVerdict()

    def _check_stagnation(self) -> LoopVerdict:
        """Detect engineering stagnation: many attempts, no improvement."""
        if len(self._history) < self._stagnation_threshold:
            return LoopVerdict()

        recent = self._history[-self._stagnation_threshold:]

        # All attempts failed with the same exit code
        if all(s.exit_code != 0 for s in recent):
            exit_codes = [s.exit_code for s in recent]
            if len(set(exit_codes)) == 1:
                return LoopVerdict(
                    should_kill=True,
                    reason=f"Engineering stagnation: {self._stagnation_threshold} attempts, same exit code {exit_codes[0]}",
                    loop_type="stagnation",
                )

        return LoopVerdict()

    def _check_inefficiency(self) -> LoopVerdict:
        """Detect token inefficiency: high token cost, minimal repo change."""
        total_tokens = sum(s.tokens_spent for s in self._history)
        max_diff = max((s.diff_lines for s in self._history), default=0)

        if total_tokens > 0 and max_diff > 0:
            ratio = total_tokens / max(max_diff, 1)
            if ratio > self._inefficiency_ratio and len(self._history) >= 3:
                return LoopVerdict(
                    should_kill=True,
                    reason=f"Token inefficiency: {total_tokens} tokens spent, {max_diff} lines changed (ratio: {ratio:.0f})",
                    loop_type="inefficiency",
                )

        return LoopVerdict()

    @property
    def attempt_count(self) -> int:
        return len(self._history)


def hash_output(text: str) -> str:
    """Deterministic hash of output text for comparison."""
    return hashlib.sha256((text or "").encode()).hexdigest()[:16]
