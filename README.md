<p align="center">
  <img src="docs/assets/frost_logo.jpg" alt="FROST Banner" width="100%">
</p>

<h1 align="center">FROST</h1>

<p align="center">
  <b>An Uncertainty-Aware Engineering Runtime for AI Coding Agents</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/frost-ai/"><img src="https://img.shields.io/pypi/v/frost-ai.svg?style=flat-square&color=00f0ff" alt="PyPI Package"></a>
  <a href="https://pypi.org/project/frost-ai/"><img src="https://img.shields.io/pypi/pyversions/frost-ai.svg?style=flat-square&color=3776ab" alt="Python Versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License"></a>
  <a href="https://github.com/Devaretanmay/Frost"><img src="https://img.shields.io/badge/architecture-uncertainty--aware-success.svg?style=flat-square" alt="Uncertainty-Aware Architecture"></a>
</p>

---

## What is FROST?

FROST is an **uncertainty-aware engineering runtime** built for AI coding agents (Claude Code, Cursor, Gemini CLI, VS Code, Windsurf, OpenCode, Cline, Continue, Zed).

AI coding agents excel at linear tasks, but fail when tasks become uncertain. When a complex refactor or dependency upgrade breaks 40 tests across a codebase, agents lose their place, oscillate in trial-and-error loops, and hallucinate fixes.

FROST provides execution resilience:
- **Linear by Default**: Simple commands execute with near-zero overhead.
- **Uncertainty-Driven Micro-Branching**: Automatically detects when linear execution hits an uncertainty point, spawning budget-constrained micro-branches to evaluate competing engineering solutions in isolated worktrees.
- **Aggressive Loop Termination**: Detects code oscillation ($A \to B \to A \to B$) and kills failing branches before token drift occurs.
- **Immediate Merge**: Merges the winning branch back into the working tree cleanly.

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
Upgrade Core Modules

        ↓

Linear Execution (PASS)

        ↓

Breaking API / Migration Error (FAIL)

        ↓

UNCERTAINTY POINT DETECTED

        ↓

Spawn 3 Isolated Micro-Branches
├── Branch A: Compatibility Layer (worktree-a)
├── Branch B: Public API Refactor (worktree-b)
└── Branch C: Pin Dependency Version (worktree-c)

        ↓

Internal Loop Detection & Evaluation
├── Branch B: Oscillation Loop (KILL)
├── Branch C: Regresses 12 Tests (KILL)
└── Branch A: 100% Tests Pass (WINNER)

        ↓

Immediate Patch Merge (git apply --3way)

        ↓

Resume Linear Execution
```

### The 7 Invariants
1. **Linear Execution Default**: Simple commands execute natively with ~20ms overhead.
2. **Branch at Uncertainty**: Micro-branching only activates when ambiguous failures recur.
3. **Tiny, Short-Lived Branches**: Ephemeral worktrees constrained by hard budgets (2,000 tokens, 5 attempts, 3 minutes).
4. **Compress Before Reasoning**: Output streams are compressed before model evaluation.
5. **Rich Internal Loop Detection**: Catches code oscillation ($A \to B \to A \to B$), no-diff stagnation, and compression loops.
6. **Aggressive Branch Termination**: Bad branches exceeding budgets or looping are killed immediately.
7. **Immediate Patch Merge**: Winning micro-branch merges back into the source working tree cleanly.

### The 3 FROST Laws
- **Law #1**: Nothing reasons over raw artifacts.
- **Law #2**: Nothing branches unless uncertainty exists.
- **Law #3**: Nothing lives longer than its usefulness.

---

## Single-Tool FastMCP Server

FROST exposes a single, unified MCP tool (`frost`) over stdio:

```bash
frost serve
```

### Input
```json
{
  "task": "Upgrade codebase to Pydantic V2 and fix breaking schema changes"
}
```

### Output
```json
{
  "status": "success",
  "summary": "Task completed successfully in 1.42s across 2 attempt(s). Spawning 2 micro-branches; Branch A merged.",
  "output": "...",
  "error": null,
  "next_steps": "Proceed to next task.",
  "retries": 1,
  "cached": false,
  "mode": "branching"
}
```

---

## Python API Primitives

```python
import frost

# 1. Execute an engineering task
result = frost.run("Fix breaking API migration tests")

# 2. Resume work from last execution state
result = frost.resume()

# 3. Inspect execution trajectory history
info = frost.inspect()
```

---

## Local Development & Testing

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
