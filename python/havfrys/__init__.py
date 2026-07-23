"""HAVFRYS — engineering execution for AI agents by HAVFRYS Labs.

Three core primitives:
    havfrys.run("Fix failing tests")
    havfrys.resume()
    havfrys.inspect()

HAVFRYS automatically analyzes task complexity and deploys engineering machinery.
"""

import sys
from .core import havfrys, run, resume, inspect, HavfrysResult, FrostResult, frost

sys.modules["frost"] = sys.modules[__name__]

__all__ = ["havfrys", "run", "resume", "inspect", "HavfrysResult", "FrostResult", "frost"]
__version__ = "0.2.4"
