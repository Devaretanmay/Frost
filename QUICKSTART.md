# FROST Quickstart

**Engineering execution for AI agents.**

One function. Executes engineering tasks efficiently.

```python
from frost import frost

result = frost("pytest tests/ -v")
result = frost("python agent.py", constraints=["max_retries=5"])
```

---

## Install

```bash
pip install frost
```

Requires Python 3.10+ and Docker (for execution isolation).

---

## Python API

```python
from frost import frost

# Execute a task with all optimizations
result = frost("pytest tests/ -v")
print(result.status)            # "success" | "failed" | "cached"
print(result.output)            # Compressed output from the best attempt
print(result.execution_time_s)  # Wall-clock time
print(result.retries)           # How many retries were needed

# Cache results across sessions
result = frost("npm run build", cache_key="my-build-v3")

# Enforce constraints
result = frost("python train.py --epochs 10", constraints=["max_retries=3"])
```

---

## MCP Server

Start the server so agents can call the ``frost`` tool:

```bash
frost serve
```

Add to Claude Code:

```bash
claude mcp add frost -- python -m frost.server
```

---

## What FROST Does

Under the hood, `frost()` wraps each execution with:

- **Retry** — retries failures with loop detection so agents don't get stuck
- **Checkpointing** — saves state so failures don't restart from zero
- **Compression** — reduces output size by 50–94%
- **Caching** — skips duplicate executions via content-addressed cache
- **Isolation** — runs each task in a clean Docker environment

None of this is visible. One function. One outcome: faster, cheaper execution.
