<p align="center">
  <img src="docs/assets/frost_logo.jpg" alt="FROST Banner" width="100%">
</p>

<h1 align="center">FROST</h1>

<p align="center">
  <b>Autonomous Engineering Execution Platform for AI Coding Agents</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/frost-ai/"><img src="https://img.shields.io/pypi/v/frost-ai.svg?style=flat-square&color=00f0ff" alt="PyPI Package"></a>
  <a href="https://pypi.org/project/frost-ai/"><img src="https://img.shields.io/pypi/pyversions/frost-ai.svg?style=flat-square&color=3776ab" alt="Python Versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License"></a>
  <a href="https://github.com/Devaretanmay/Frost"><img src="https://img.shields.io/badge/architecture-local--first-success.svg?style=flat-square" alt="Local-First Architecture"></a>
</p>

---

## What is FROST?

FROST provides execution resilience, micro-branching, loop prevention, state recovery, and context window protection for AI coding agents (Claude Code, Cursor, Gemini CLI, VS Code, Windsurf, OpenCode, Cline, Continue, Zed).

Instead of forcing AI models to reason over raw, noisy terminal outputs or commit upfront to risky repository-wide changes, FROST manages execution machinery locally under strict budgets.

---

## Quickstart

### 1. Install via PyPI
```bash
pip install frost-ai
```

### 2. Auto-Configure Local Coding Agent
```bash
frost init
```
```text
Welcome to FROST.

Detected Claude Code.

Configure automatically? [Y/n]
```

### 3. Verify Environment Health
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
Version:             v0.2.2
Repository:          [ok] Ready
```

---

## Architectural Invariants & Laws

```text
  Coding Agent (Claude Code / Cursor / Gemini CLI)
                         │
                         ▼ (stdio transport)
                    frost serve
                 (local process)
                         │
                         ├─► Simple Command ──> Level 0 Native Execution (~20ms)
                         ├─► Failure Point  ──> Uncertainty Detector
                         │                         │
                         │                         ▼
                         │               Spawn Micro-Branches
                         │                         │
                         │                         ▼
                         │               BranchLoopDetector (Kill Bad Actors)
                         │                         │
                         │                         ▼
                         └────────────── Immediate Patch Merge (git apply --3way)
```

### The 7 Invariants
1. **Linear Execution Default**: Simple commands execute natively with ~20ms overhead.
2. **Branch at Uncertainty**: Micro-branching only activates when ambiguous failures recur.
3. **Tiny, Short-Lived Branches**: Ephemeral worktrees constrained by hard budgets (2,000 tokens, 5 attempts, 3 minutes).
4. **Compress Before Reasoning**: Streams compressed via SmartCrusher before model evaluation (95%+ token reduction).
5. **Rich Internal Loop Detection**: Catches code oscillation ($A \to B \to A \to B$), no-diff stagnation, and compression loops.
6. **Aggressive Branch Termination**: Bad branches exceeding budgets or looping are killed immediately.
7. **Immediate Patch Merge**: Winning micro-branch merges back into the source working tree cleanly.

### The 3 FROST Laws
- **Law #1**: Nothing reasons over raw artifacts.
- **Law #2**: Nothing branches unless uncertainty exists.
- **Law #3**: Nothing lives longer than its usefulness.

---

## Python API Primitives

```python
import frost

# 1. Execute an engineering task
result = frost.run("pytest tests/ --tb=short")

# 2. Resume work from last execution state
result = frost.resume()

# 3. Inspect execution trajectory history
info = frost.inspect()
```

### Result Schema
```python
@dataclass
class FrostResult:
    task: str
    status: str                  # "success" | "failed" | "cached"
    output: str                  # Compressed execution output
    error: Optional[str]
    execution_time_s: float
    retries: int
    mode: str                    # "linear" | "branching"
    uncertainty_points: int
    branches_spawned: int
    branches_killed: int
    token_reduction_pct: float
    winning_fix: str
```

---

## Single-Tool FastMCP Server

FROST exposes a single, unified MCP tool (`frost`) over stdio:

```bash
frost serve
```

### Input
```json
{
  "task": "pytest tests/ -q"
}
```

### Output
```json
{
  "status": "success",
  "summary": "Task completed successfully in 0.05s across 1 attempt(s).",
  "output": "...",
  "error": null,
  "next_steps": "Proceed to next task.",
  "retries": 0,
  "cached": false,
  "mode": "linear"
}
```

---

## Empirical Benchmarks

Empirical benchmark metrics are generated reproducibly via `python benchmarks/run_benchmarks.py` and output to [`benchmarks/results.json`](file:///Users/tanmaydevare/Tanmay/Agent/Harada/benchmarks/results.json).

```bash
python benchmarks/run_benchmarks.py
```

| Task | Category | Mode | Latency | Token Reduction |
| :--- | :--- | :---: | :---: | :---: |
| `high_volume_file_discovery` | Repository structure scan | Linear | 0.35s | **50.0%** |
| `git_commit_history_scan` | Commit log scan | Linear | 0.03s | **50.0%** |
| `pytest_suite_execution` | Test suite with micro-branching | Branching | 6.99s | **53.1%** |

---

## Local Development & Testing

### Requirements
- Python 3.10+
- Rust 1.75+ (Cargo)

### Build Rust Engine
```bash
maturin develop --offline
```

### Run Full Test Suite
```bash
pytest tests/
cargo test
```

---

## License

FROST is released under the [MIT License](LICENSE).
