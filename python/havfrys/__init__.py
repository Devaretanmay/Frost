"""HAVFRYS — engineering execution for AI agents by HAVFRYS Labs.

Three core primitives:
    havfrys.run("Fix failing tests")
    havfrys.resume()
    havfrys.inspect()

HAVFRYS automatically analyzes task complexity and deploys engineering machinery.
"""

from .core import havfrys, run, resume, inspect, HavfrysResult, FrostResult, frost

__all__ = ["havfrys", "run", "resume", "inspect", "HavfrysResult", "FrostResult", "frost"]
__version__ = "0.2.2"
