"""Uncertainty Detector — decides whether a failure is a retry or a branch point.

FROST LAW #2: Nothing branches unless uncertainty exists.

A failure is an uncertainty point when:
- The error is ambiguous (multiple possible fixes)
- A linear retry already failed (same error twice)
- The error pattern matches known multi-fix domains (middleware, deps, imports)
- The diff between attempts oscillates

A failure is NOT an uncertainty point when:
- It's the first failure (try once more linearly)
- The error is unrecoverable (command not found, permission denied)
- The fix is obvious (single clear error message)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# Error patterns that indicate multiple valid fixes exist
_UNCERTAINTY_PATTERNS = [
    # Dependency conflicts — could be pin, upgrade, or replace
    r"(?i)conflicting\s+dependencies",
    r"(?i)version\s+conflict",
    r"(?i)incompatible\s+versions?",
    r"(?i)requirement\s+.*\s+not\s+satisfied",

    # Import/module errors — could be path fix, shim, or replacement
    r"(?i)ModuleNotFoundError",
    r"(?i)ImportError",
    r"(?i)cannot\s+import\s+name",
    r"(?i)No\s+module\s+named",

    # Middleware/plugin errors — structural ambiguity
    r"(?i)middleware.*(?:error|fail|broken|deprecated)",
    r"(?i)plugin.*(?:error|fail|broken|deprecated)",

    # API breakage — could be adapt, shim, or rewrite
    r"(?i)AttributeError.*has\s+no\s+attribute",
    r"(?i)TypeError.*(?:unexpected|missing|got\s+an?\s+unexpected)",
    r"(?i)DeprecationWarning",

    # Configuration errors — multiple valid configs
    r"(?i)configuration\s+error",
    r"(?i)invalid\s+(?:config|setting|option)",
]

# Errors that are unrecoverable — never branch on these
_UNRECOVERABLE_PATTERNS = [
    r"(?i)command\s+not\s+found",
    r"(?i)permission\s+denied",
    r"(?i)no\s+space\s+left",
    r"(?i)killed.*out\s+of\s+memory",
    r"(?i)segmentation\s+fault",
    r"(?i)core\s+dumped",
]


@dataclass
class UncertaintySignal:
    """Result of uncertainty analysis on a failure."""

    is_uncertainty: bool = False
    confidence: float = 0.0      # 0.0–1.0, how certain we are this is ambiguous
    reason: str = ""
    suggested_fixes: list[str] = field(default_factory=list)


def detect_uncertainty(
    *,
    error_output: str,
    exit_code: int,
    attempt_number: int,
    previous_errors: list[str],
) -> UncertaintySignal:
    """Analyze a failure to decide: retry linearly or branch?

    Returns an UncertaintySignal. The orchestrator uses this to decide
    whether to spawn micro-branches.
    """
    error = error_output or ""

    # Rule 1: Unrecoverable errors — never branch
    for pattern in _UNRECOVERABLE_PATTERNS:
        if re.search(pattern, error):
            return UncertaintySignal(
                is_uncertainty=False,
                reason=f"Unrecoverable error: {pattern}",
            )

    # Rule 2: First failure — retry linearly before considering branching
    if attempt_number <= 1:
        return UncertaintySignal(
            is_uncertainty=False,
            reason="First failure — retry linearly before branching",
        )

    # Rule 3: Same error repeated — this is an uncertainty point
    if previous_errors and error:
        error_hash = _normalize_error(error)
        for prev in previous_errors[-2:]:
            if _normalize_error(prev) == error_hash:
                fixes = _suggest_fixes(error)
                return UncertaintySignal(
                    is_uncertainty=True,
                    confidence=0.85,
                    reason="Same error repeated after retry — multiple fixes likely",
                    suggested_fixes=fixes,
                )

    # Rule 4: Error matches known ambiguous patterns
    matched_patterns = []
    for pattern in _UNCERTAINTY_PATTERNS:
        if re.search(pattern, error):
            matched_patterns.append(pattern)

    if matched_patterns and attempt_number >= 2:
        fixes = _suggest_fixes(error)
        return UncertaintySignal(
            is_uncertainty=True,
            confidence=min(0.5 + 0.1 * len(matched_patterns), 0.95),
            reason=f"Error matches {len(matched_patterns)} ambiguous pattern(s)",
            suggested_fixes=fixes,
        )

    # Rule 5: Multiple consecutive failures with different errors — escalating
    if attempt_number >= 3 and len(previous_errors) >= 2:
        unique_errors = len(set(_normalize_error(e) for e in previous_errors[-3:]))
        if unique_errors >= 2:
            fixes = _suggest_fixes(error)
            return UncertaintySignal(
                is_uncertainty=True,
                confidence=0.7,
                reason=f"Multiple distinct failures ({unique_errors}) — problem is ambiguous",
                suggested_fixes=fixes,
            )

    # Default: not uncertain, retry linearly
    return UncertaintySignal(
        is_uncertainty=False,
        reason="Error does not match uncertainty criteria",
    )


def _normalize_error(error: str) -> str:
    """Normalize error text for comparison (strip line numbers, paths, timestamps)."""
    # Strip line numbers
    normalized = re.sub(r"line\s+\d+", "line N", error)
    # Strip file paths
    normalized = re.sub(r"/[\w/.-]+\.py", "FILE.py", normalized)
    # Strip timestamps
    normalized = re.sub(r"\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}", "TIMESTAMP", normalized)
    # Strip memory addresses
    normalized = re.sub(r"0x[0-9a-fA-F]+", "ADDR", normalized)
    # Collapse whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized[:500]  # cap for comparison


def _suggest_fixes(error: str) -> list[str]:
    """Generate candidate fix approaches based on error content."""
    fixes = []
    error_lower = error.lower()

    if "import" in error_lower or "module" in error_lower:
        fixes.extend([
            "fix_import_path",
            "add_compatibility_import",
            "replace_module",
        ])

    if "deprecat" in error_lower:
        fixes.extend([
            "update_to_new_api",
            "add_deprecation_shim",
            "pin_old_version",
        ])

    if "version" in error_lower or "conflict" in error_lower:
        fixes.extend([
            "pin_compatible_version",
            "upgrade_dependency",
            "replace_dependency",
        ])

    if "middleware" in error_lower or "plugin" in error_lower:
        fixes.extend([
            "fix_middleware_config",
            "add_compatibility_shim",
            "replace_middleware",
        ])

    if "attribute" in error_lower or "typeerror" in error_lower:
        fixes.extend([
            "update_api_call",
            "add_type_adapter",
            "rewrite_function",
        ])

    if not fixes:
        fixes = ["direct_fix", "alternative_approach", "workaround"]

    return fixes[:4]  # max 4 micro-branches
