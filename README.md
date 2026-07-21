# FROST

**FROST solves engineering problems for AI agents. Everything else is an implementation detail.**

```python
from frost import frost

result = frost("Fix the failing tests in this repository")
result = frost("Refactor the auth module",
               constraints=["Do not modify public APIs"])
```

---

## Why

AI coding agents are good at writing code. They're bad at retrying when things fail, managing context when output is verbose, and avoiding loops when they get stuck. FROST handles all of that invisibly.

| Without FROST | With FROST |
|--------------|------------|
| Agent runs a command | Agent delegates an engineering problem |
| Fails → retries manually → burns context | FROST retries internally with loop detection |
| Same task runs again next session | FROST caches results by content hash |
| Long task fails at 95% | FROST checkpoints and resumes |
| Verbose output fills context window | FROST compresses output automatically |

---

## Install

```bash
pip install frost
```

Requires Python 3.10+ and Docker (for execution isolation).

See **[IMAGES.md](IMAGES.md)** for Docker image recommendations by language.

---

## Usage

### For agents

```python
from frost import frost

# Delegate an engineering problem
result = frost("Fix the failing tests in tests/")
print(result.status, result.output)

# Cache results by content hash
result = frost("Update all dependencies to their latest versions", cache_key="dep-upgrade")

# Enforce constraints
result = frost("Refactor the payment module",
               constraints=["Must use the existing database schema",
                            "Must pass all existing tests"])
```

### For developers

```bash
frost serve                    # Start the MCP server
frost run exec 'pytest tests/' # Debug: run a command in a container
```

Make the ``frost`` tool available to your agent via MCP:

```bash
frost serve                    # Start the MCP server (stdio)
frost serve --sse --port 8080  # Or SSE for HTTP transport
```

The agent gets one tool: ``frost`` — it delegates engineering problems, FROST handles execution.

---

## How It Works

FROST wraps each execution with hidden infrastructure:

- **Session management** — isolated Docker environment per task
- **Retry with loop detection** — stops infinite retry loops
- **Checkpointing** — saves state so failures don't restart from zero
- **Compression** — reduces output size by 50–94%
- **Caching** — content-addressed cache eliminates duplicate work
- **Branching and parallel exploration** — explores multiple solutions (planned)

None of these are user-facing. The agent delegates a problem. FROST returns the best result.

---

## Architecture

```
Agent
  │
  └── frost("Fix the failing tests")
        │
        ├── Session (isolated Docker environment)
        ├── Loop detection (Rust)
        ├── Compression engine (Rust)
        ├── Checkpointing (Docker commit)
        ├── Cache (content-addressed, ~/.frost/cache)
        └── ... (more hidden infrastructure)
```

---

## Status

Early alpha. Retry, caching, checkpointing, and output compression work but need real-world validation with production agent workloads.

## License

Apache 2.0
