"""FROST — engineering execution for AI agents.

Three core primitives:
    frost.run("Fix failing tests")
    frost.resume()
    frost.inspect()

FROST automatically analyzes task complexity and deploys engineering machinery.
"""

from .core import frost, run, resume, inspect, FrostResult

__all__ = ["frost", "run", "resume", "inspect", "FrostResult"]
__version__ = "0.2.0"
