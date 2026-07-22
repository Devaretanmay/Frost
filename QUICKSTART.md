# FROST Quickstart (`frost-ai`)

FROST provides autonomous execution resilience for AI coding agents. The user gives FROST an engineering task. FROST executes linearly by default, detects uncertainty, micro-branches when needed, and merges the winning fix.

## Installation & Setup

```bash
pip install frost-ai
```

```bash
frost init
```

```text
Welcome to FROST.

Detected Claude Code.

Configure automatically? [Y/n]
```

### Diagnostics

```bash
frost doctor
```

```text
FROST Diagnostics

Runtime:             [ok] Installed
Python:              [ok] 3.14.6
MCP Server:          [ok] Available (frost serve)
Clients:             [ok] Claude Code, Cursor, VS Code detected
Compression Engine:  [ok] Loaded (Lossless + SmartCrusher)
Loop Detection:      [ok] Loaded (BranchLoopDetector)
Version:             v0.2.1
Repository:          [ok] Ready
```

---

## Python API Usage

```python
import frost

# 1. Run a task
result = frost.run("Fix failing tests in this repository")

# 2. Resume if interrupted
result = frost.resume()

# 3. Inspect history and trajectory metrics
info = frost.inspect()
```

---

## The 3 Core Primitives

| Primitive | Usage | Description |
| :--- | :--- | :--- |
| `frost.run(task)` | `frost.run("pytest tests/")` | Solves an engineering task with linear-first execution and uncertainty branching. |
| `frost.resume()` | `frost.resume()` | Resumes execution state, skipping previously failed strategies via memory. |
| `frost.inspect()` | `frost.inspect()` | Returns attempt logs, micro-branch summaries, and token reduction metrics. |

---

## Automatic Internal Escalation

Caller flags like `docker=True`, `cache=True`, or `compression=True` are not required. FROST manages internal machinery automatically:

- **Simple task**: Level 0 Native Execution (~20 ms overhead)
- **Large output**: LogCompressor (95%+ token reduction)
- **Repeated error**: Uncertainty Detector spawns budget-constrained micro-branches
- **Internal loop**: BranchLoopDetector terminates code oscillation or stagnation
- **Winner selection**: Winning branch merged immediately into source repository

---

## MCP Server (Single Tool Integration)

Start the FastMCP server for AI agent integration:

```bash
frost serve
```

### Input
```json
{
  "task": "Upgrade this repository to Python 3.13"
}
```

### Output
```json
{
  "status": "success",
  "summary": "Task completed successfully in 0.05s across 1 attempt(s).",
  "output": "...",
  "next_steps": "Proceed to next task.",
  "retries": 0,
  "cached": false,
  "mode": "linear"
}
```
