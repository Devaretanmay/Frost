# Harada

![Harada Progress](https://img.shields.io/badge/Harada_Progress-100%25-brightgreen.svg)
![Crates.io](https://img.shields.io/crates/v/harada.svg)
![License](https://img.shields.io/crates/l/harada.svg)

Harada is an opinionated **Dev-First Execution OS** that turns complex goals into executable 1x8x8 grids of tasks, auto-detects bottlenecks via Git activity, and seamlessly delegates work between humans and AI agents.

Built around a single immovable invariant:
**Every goal must decompose into exactly 8 capabilities. Every capability must decompose into exactly 8 tasks. Exactly 64 tasks. No exceptions.**

## Zero-to-One Onboarding

### 1. Install Harada
```bash
# Via Cargo
cargo install harada

# Via Curl Installer
curl -sSL https://raw.githubusercontent.com/example/harada/main/install.sh | bash

# Via Homebrew
brew install example/tap/harada
```

### 2. Compile Your First Goal
Give Harada a goal. It will generate a prompt for you to paste into Claude/ChatGPT.
```bash
harada compile "Build a Rust distributed cache"
```
*Paste the resulting JSON from the AI into `response.json`*

```bash
harada compile --import response.json
```

### 3. Setup CI & Hooks
Initialize Harada for your Git repository:
```bash
harada init --pre-commit --github-action
```

### 4. Let the Execution OS Guide You
Harada's `work` command detects the critical path and tells you exactly what to do next based on branch activity and dependencies:
```bash
harada work
```

### 5. Assign to AI
Want an AI agent to do a task?
```bash
# Auto-suggest AI tools for easy tasks
harada assign --suggest

# Generate a prompt specifically for the assigned AI tool
harada handoff C1T2
```

### 6. Auto-Complete via Git
Work on the task on a branch, then link it:
```bash
harada link C1T2 my-feature-branch
```
When `my-feature-branch` is merged into `main`, Harada will instantly mark the task as completed and unblock downstream dependencies automatically:
```bash
harada sync
```

## Advanced Features
- **Velocity Dashboard:** `harada stats` provides ETAs, actor breakdowns, and TUI charts.
- **Dependency Graphs:** `harada work --graph` outputs Graphviz DOT logic.
- **CI Notifiers:** Add `--notify <slack_url>` to ping your team on new bottlenecks.

## State & Storage
All data is stored locally and securely in `.harada/state.json` inside your current working directory. There is no cloud sync, no accounts, and no data lock-in.

---
*Built with Rust. Driven by Constraints.*
