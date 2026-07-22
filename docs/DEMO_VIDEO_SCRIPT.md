# FROST 2-Minute Launch Demo Video Script & Storyboard

**Total Duration**: 120 Seconds (2:00)  
**Target Audience**: AI Developers, Infrastructure Engineers, AI Coding Agent Users (Claude Code, Cursor, Windsurf, OpenCode)  
**Tone**: Fast-paced, technical, precise, developer-centric.

---

## Storyboard & Scene-by-Scene Breakdown

```
[0:00 - 0:15] ──▶ SCENE 1: The Problem (Linear Agent Failure)
[0:15 - 0:40] ──▶ SCENE 2: Meet FROST & FastMCP Setup
[0:40 - 1:15] ──▶ SCENE 3: Uncertainty Point & Micro-Branch Spawning
[1:15 - 1:45] ──▶ SCENE 4: Loop Killing & Immediate Patch Merge
[1:45 - 2:00] ──▶ SCENE 5: Repository GREEN & Call to Action
```

---

### Scene 1: The Problem — The Trial-and-Error Loop (0:00 – 0:15)

* **Visual**: Split screen / Dark terminal showing an AI coding agent attempting a complex migration (e.g. Pydantic V1 $\to$ V2). The agent changes code, runs tests, fails, undoes code, fails again, spinning in a loop. Red error logs scrolling endlessly.
* **On-Screen Text**: *AI agents excel at linear coding. But fail when engineering tasks become uncertain.*
* **Voiceover**:  
  > "AI coding agents are incredible at linear tasks. But when a major dependency upgrade or refactor breaks 40 tests across your codebase, standard agents panic. They get stuck in trial-and-error loops, burn through context windows, and hallucinate broken fixes."

---

### Scene 2: Introducing FROST & FastMCP (0:15 – 0:40)

* **Visual**: Terminal clears. User types `pip install frost-ai` followed by `frost init` and `frost doctor`. System output displays crisp green diagnostic checkmarks.
* **Command Executed**:
  ```bash
  frost doctor
  ```
* **Terminal Output**:
  ```text
  FROST Diagnostics
  
  Runtime:             [ok] Installed
  Python:              [ok] 3.14.6
  MCP Server:          [ok] Available (frost serve)
  Clients:             [ok] Claude Code, Cursor, VS Code detected
  Compression Engine:  [ok] Loaded (Lossless + SmartCrusher)
  Loop Detection:      [ok] Loaded (BranchLoopDetector)
  Version:             v0.2.2
  ```
* **Voiceover**:  
  > "Meet FROST — an uncertainty-aware engineering runtime built for AI coding agents. FROST exposes a single, unified MCP tool that gives your agent execution resilience, parallel micro-branching, and log compression."

---

### Scene 3: Task Submission & Uncertainty-Driven Micro-Branching (0:40 – 1:15)

* **Visual**: The agent calls FROST via MCP: `"Modernize repository to Python 3.14, Pydantic V2, and SQLAlchemy 2.0 while preserving 100% test pass rate."`
* **Execution Flow**:
  1. FROST starts in **Linear Mode** (20ms overhead).
  2. Test run fails with `PydanticV1SchemaDeprecationError` and generic mapper failure $\to$ **UNCERTAINTY POINT DETECTED**.
  3. Animated terminal graphic shows FROST instantly spawning 3 isolated `git worktree` micro-branches in parallel.
* **On-Screen Visual**:
  ```text
  [UNCERTAINTY POINT DETECTED]
  ├── Branch A (worktree-a): Explicit Pydantic V2 & ORM relationships
  ├── Branch B (worktree-b): Legacy Compatibility Layer
  └── Branch C (worktree-c): Version Pinning
  ```
* **Voiceover**:  
  > "Simple commands run linearly with zero overhead. But the moment a complex error occurs, FROST's uncertainty detector triggers. Instead of guessing in place, FROST instantly spawns budget-constrained micro-branches in isolated git worktrees."

---

### Scene 4: Internal Loop Termination & Patch Merge (1:15 – 1:45)

* **Visual**: The terminal updates with live branch evaluations:
  - Branch B encounters code oscillation ($A \to B \to A \to B$) $\to$ **KILLED BY LOOP ENGINE**.
  - Branch C regresses 12 unit tests $\to$ **KILLED BY BUDGET ENGINE**.
  - Branch A passes 100% of unit & integration tests $\to$ **WINNER SELECTED**.
  - FROST automatically executes `git apply --3way` merging Branch A back into `master`.
* **On-Screen Visual**:
  ```text
  [EVALUATION & TERMINATION]
  ├── Branch B: Oscillation Loop Detected  [KILLED]
  ├── Branch C: 12 Test Failures           [KILLED]
  └── Branch A: 54/54 Tests PASSED         [WINNER MERGED]
  ```
* **Voiceover**:  
  > "FROST's Rust compression and loop engines monitor branch trajectories in real time. Looping or failing branches are killed aggressively before token drift happens. The winning patch is merged cleanly back into your working tree."

### Scene 5: Repository GREEN Conclusion (1:45 – 2:00)

* **Visual**: Terminal shows clean test suite output:  
  `================ 54 passed in 1.42s ================`  
  `frost inspect` shows **68.4% Context Token Reduction**.
* **Closing Screen Graphic**:
  - FROST Logo
  - `pip install frost-ai`
  - `frost serve`
  - GitHub: `github.com/Devaretanmay/Frost`
  - License: Business Source License 1.1 (BUSL-1.1)
* **Voiceover**:  
  > "Repository GREEN. Zero hallucinations. Zero token waste. Run FROST with `pip install frost-ai`."

---

## Production Tips for Recording

1. **Terminal Recording Tool**: Use **VHS by Charm** (`brew install charmbr/tap/vhs`) or **Asciinema** for pixel-perfect terminal animations.
2. **Terminal Theme**: Dark theme (Catppuccin Macchiato or Tokyo Night), 18pt font (JetBrains Mono).
3. **Voiceover**: Clear, high-quality audio narration.
4. **BGM**: Low-volume subtle ambient background audio.
