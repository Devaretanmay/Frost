"""FROST — engineering execution for AI agents.

One tool. One capability: execute engineering tasks efficiently.

Usage:
    from frost import frost

    result = frost("Fix the failing tests in this repository")
    result = frost("Refactor the auth module",
                   constraints=["Do not modify public APIs"])

Everything else (sessions, compression, checkpointing, caching,
loop detection, Docker) is an internal implementation detail.
"""

from .core import frost, FrostResult

__all__ = ["frost", "FrostResult"]
__version__ = "0.2.0"
