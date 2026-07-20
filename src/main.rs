mod core;
mod git;
mod github;
mod layout;
mod spec;
mod storage;
mod tui;

use crate::core::ExecutorKind;
use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use std::io::{self, IsTerminal};

#[derive(Parser)]
#[command(
    name = "harada",
    version,
    about = "Harada: The 9x9 Mandala Goal Compiler"
)]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand)]
enum Commands {
    /// Compile a goal into a 9x9 Mandala Matrix
    Compile {
        /// Freeform goal text
        goal: Option<String>,
        /// Import a compiled JSON from AI
        #[arg(long)]
        import: Option<String>,
        /// Fetch goal from GitHub issue ID
        #[arg(long)]
        from_issue: Option<String>,
        /// Fetch goal from git diff (optionally pass base ref like main)
        #[arg(long)]
        from_diff: Option<Option<String>>,
        /// Fetch goal from local RFC markdown file
        #[arg(long)]
        from_rfc: Option<String>,
    },
    /// Assign a task to an actor (self, ai, team)
    Assign {
        /// Task ID (e.g. C1T2) or capability (C1)
        task_id: Option<String>,
        /// Actor type: self, ai, team
        actor: Option<String>,
        /// AI Tool name if actor is ai
        #[arg(long)]
        tool: Option<String>,
        /// Requires human review before marking done
        #[arg(long)]
        requires_review: bool,
        /// Suggest assignments for unassigned tasks
        #[arg(long)]
        suggest: bool,
    },
    /// Generate a prompt handoff for an AI-assigned task
    Handoff {
        /// Task ID (e.g. C1T2)
        task_id: Option<String>,
        /// Export all ready AI tasks to a markdown file
        #[arg(long)]
        export_handoff: Option<String>,
    },
    /// Link a task to a git artifact (branch/commit/PR)
    Link {
        /// Task ID
        task_id: String,
        /// Branch, commit hash, or PR URL
        ref_name: String,
    },
    /// Sync task states against git/CI (detects merges and completes tasks)
    Sync {
        /// Webhook URL for Slack/Discord notifications
        #[arg(long)]
        notify: Option<String>,
    },
    /// Execution OS: Find bottlenecks and the next best task
    Work {
        /// Manually mark a task as done (for non-code tasks)
        #[arg(long)]
        mark_done: Option<String>,
        /// Export the dependency graph to DOT format
        #[arg(long)]
        graph: bool,
        /// Webhook URL for Slack/Discord notifications
        #[arg(long)]
        notify: Option<String>,
    },
    /// Velocity tracking and performance metrics
    Stats {
        /// Generate a markdown badge with current progress
        #[arg(long)]
        badge: bool,
        /// Export format: csv or json
        #[arg(long)]
        export: Option<String>,
        /// Filter events since date (YYYY-MM-DD)
        #[arg(long)]
        since: Option<String>,
    },
    /// Initialize CI/CD and Git hooks
    Init {
        /// Generate a GitHub Action workflow
        #[arg(long)]
        github_action: bool,
        /// Generate a pre-commit hook
        #[arg(long)]
        pre_commit: bool,
    },
}

fn parse_task_id(id: &str) -> Result<(usize, usize)> {
    let id = id.to_uppercase();
    if !id.starts_with('C') || id.len() != 4 || !id.contains('T') {
        anyhow::bail!("Invalid Task ID format. Expected format like C1T2");
    }
    let parts: Vec<&str> = id.split('T').collect();
    if parts.len() != 2 {
        anyhow::bail!("Invalid Task ID format. Expected format like C1T2");
    }
    let c = parts[0][1..].parse::<usize>().unwrap_or(0);
    let t = parts[1].parse::<usize>().unwrap_or(0);

    if !(1..=8).contains(&c) || !(1..=8).contains(&t) {
        anyhow::bail!("Invalid Task ID. Must be C1-8 and T1-8");
    }
    Ok((c - 1, t - 1))
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Some(Commands::Compile {
            goal,
            import,
            from_issue,
            from_diff,
            from_rfc,
        }) => {
            if let Some(import_path) = import {
                let proj = spec::parse_and_import(&import_path)?;
                storage::save_project(&proj)?;
                println!(
                    "Successfully compiled and imported the 9x9 Mandala matrix for: {}",
                    proj.goal
                );
                println!("Run 'harada work' to see your next action.");
                return Ok(());
            }

            let final_goal;
            let source_context;

            if let Some(issue_id) = from_issue {
                let ctx = git::get_context()?;
                let issue = github::get_issue(&ctx.owner, &ctx.repo, &issue_id)?;
                final_goal = format!("Resolve Issue #{}: {}", issue_id, issue.title);
                source_context = format!("Source: GitHub Issue\n\nIssue Body:\n{}", issue.body);
            } else if let Some(diff_base) = from_diff {
                let diff_text = git::get_diff(diff_base.as_deref())?;
                final_goal = "Implement changes from current diff".to_string();
                source_context = format!("Source: Git Diff\n\nDiff Content:\n{}", diff_text);
            } else if let Some(rfc_path) = from_rfc {
                let rfc_text = std::fs::read_to_string(&rfc_path)?;
                final_goal = format!("Implement RFC: {}", rfc_path);
                source_context = format!("Source: RFC Document\n\nContent:\n{}", rfc_text);
            } else if let Some(g) = goal {
                final_goal = g;
                source_context = String::new();
            } else {
                println!("Usage: harada compile \"My Goal\" OR harada compile --from-issue <id>");
                return Ok(());
            }

            let prompt_text = spec::generate_prompt(&final_goal, &source_context);
            println!("{}", prompt_text);
        }
        Some(Commands::Assign {
            task_id,
            actor,
            tool,
            requires_review,
            suggest,
        }) => {
            if !storage::exists() {
                anyhow::bail!("No project found. Run 'harada compile' first.");
            }
            let mut proj = storage::load_project()?;

            if suggest {
                let mut suggested = 0;
                for cap in &mut proj.capabilities {
                    for task in &mut cap.tasks {
                        if task.assigned_to.name == "Me" && task.status == core::Status::Pending {
                            if task.estimated_difficulty <= 3 {
                                task.assigned_to.kind = ExecutorKind::AI;
                                task.assigned_to.name = "ai".into();
                                task.assigned_to.tool = Some("Claude".into()); // Default AI
                                task.assigned_to.requires_review = true;
                            } else {
                                task.assigned_to.kind = ExecutorKind::Human;
                                task.assigned_to.name = "self".into();
                            }
                            suggested += 1;
                        }
                    }
                }
                storage::save_project(&proj)?;
                println!("Suggested assignments for {} tasks.", suggested);
                return Ok(());
            }

            let t_id = task_id.context("task_id required unless using --suggest")?;
            let act = actor.context("actor required unless using --suggest")?;

            let kind = match act.to_lowercase().as_str() {
                "self" => ExecutorKind::Human,
                "ai" => ExecutorKind::AI,
                "team" => ExecutorKind::Team,
                _ => anyhow::bail!("Invalid actor. Must be 'self', 'ai', or 'team'"),
            };

            // Bulk assign if only "C1", "C2" etc.
            if t_id.len() == 2 && t_id.starts_with('C') {
                let c: usize = t_id[1..]
                    .parse::<usize>()
                    .context("Invalid capability index")?
                    - 1;
                for (t, task) in proj.capabilities[c].tasks.iter_mut().enumerate() {
                    task.assigned_to.kind = kind.clone();
                    task.assigned_to.name = act.clone();
                    task.assigned_to.tool = tool.clone();
                    task.assigned_to.requires_review = requires_review;

                    proj.events.push(core::Event {
                        timestamp: chrono::Utc::now(),
                        event_type: core::EventType::TaskAssigned {
                            task_id: format!("C{}T{}", c + 1, t + 1),
                            actor: act.clone(),
                        },
                    });
                }
                println!("Assigned capability {} to {}", t_id, act);
            } else {
                let (c, t) = parse_task_id(&t_id)?;
                let task = &mut proj.capabilities[c].tasks[t];
                task.assigned_to.kind = kind;
                task.assigned_to.name = act.clone();
                task.assigned_to.tool = tool;
                task.assigned_to.requires_review = requires_review;

                proj.events.push(core::Event {
                    timestamp: chrono::Utc::now(),
                    event_type: core::EventType::TaskAssigned {
                        task_id: t_id.clone(),
                        actor: act.clone(),
                    },
                });
                println!("Assigned {} to {}", t_id, act);
            }
            storage::save_project(&proj)?;
        }
        Some(Commands::Handoff {
            task_id,
            export_handoff,
        }) => {
            if !storage::exists() {
                anyhow::bail!("No project found. Run 'harada compile' first.");
            }
            let proj = storage::load_project()?;

            if let Some(path) = export_handoff {
                let mut content = String::new();
                for (c, cap) in proj.capabilities.iter().enumerate() {
                    for (t, task) in cap.tasks.iter().enumerate() {
                        if task.assigned_to.kind == ExecutorKind::AI && !task.status.is_done() {
                            content.push_str(&format!(
                                "# Task C{}T{}: {}\n\n",
                                c + 1,
                                t + 1,
                                task.title
                            ));
                            content.push_str(&format!("Description: {}\n", task.description));
                            if !task.completion_criteria.is_empty() {
                                content.push_str(&format!(
                                    "Completion Criteria:\n- {}\n",
                                    task.completion_criteria.join("\n- ")
                                ));
                            }
                            content.push_str("---\n\n");
                        }
                    }
                }
                std::fs::write(&path, content)?;
                println!("Exported batch AI handoff to {}", path);
            } else if let Some(t_id) = task_id {
                let (c, t) = parse_task_id(&t_id)?;
                let task = &proj.capabilities[c].tasks[t];
                println!(
                    "Here is the handoff prompt for the AI agent (Tool: {}):\n",
                    task.assigned_to.tool.as_deref().unwrap_or("Generic AI")
                );
                println!("You are assigned the following task:");
                println!("Goal: {}", task.title);
                println!("Description: {}", task.description);
                if !task.completion_criteria.is_empty() {
                    println!(
                        "Completion Criteria:\n- {}",
                        task.completion_criteria.join("\n- ")
                    );
                }
                if let Some(ref_name) = &task.linked_ref {
                    println!("Linked Branch/Ref: {}", ref_name);
                }
            } else {
                anyhow::bail!("Must provide task_id or --export-handoff");
            }
        }
        Some(Commands::Link { task_id, ref_name }) => {
            if !storage::exists() {
                anyhow::bail!("No project found. Run 'harada compile' first.");
            }
            if !git::ref_exists(&ref_name)? {
                anyhow::bail!("Ref {} does not exist in local git repository.", ref_name);
            }
            let mut proj = storage::load_project()?;
            let (c, t) = parse_task_id(&task_id)?;
            let task = &mut proj.capabilities[c].tasks[t];
            task.linked_ref = Some(ref_name.clone());
            storage::save_project(&proj)?;
            println!("Linked {} to git ref {}", task_id, ref_name);
        }
        Some(Commands::Sync { notify }) => {
            if !storage::exists() {
                anyhow::bail!("No project found. Run 'harada compile' first.");
            }
            let mut proj = storage::load_project()?;
            let ctx = git::get_context()?;
            let base_branch = ctx.branch.clone(); // In reality, we should detect the default base branch, e.g. main

            let mut updated_count = 0;
            let mut new_events = Vec::new();

            for (c, cap) in proj.capabilities.iter_mut().enumerate() {
                for (t, task) in cap.tasks.iter_mut().enumerate() {
                    if !task.status.is_done() {
                        if let Some(ref_name) = &task.linked_ref {
                            if git::is_merged(ref_name, &base_branch).unwrap_or(false) {
                                task.status = core::Status::Completed;
                                updated_count += 1;
                                new_events.push(core::Event {
                                    timestamp: chrono::Utc::now(),
                                    event_type: core::EventType::TaskCompleted {
                                        task_id: format!("C{}T{}", c + 1, t + 1),
                                        actor: task.assigned_to.name.clone(),
                                    },
                                });
                                println!(
                                    "Task {} auto-completed ({} merged into {})",
                                    task.title, ref_name, base_branch
                                );
                            }
                        }
                    }
                }
            }
            proj.events.extend(new_events);

            // Dependency-aware auto-unblocking
            let mut newly_unblocked = 0;
            let proj_clone = proj.clone(); // Clone to read states while mutating
            for (c, cap) in proj.capabilities.iter_mut().enumerate() {
                for (t, task) in cap.tasks.iter_mut().enumerate() {
                    if task.status == core::Status::Blocked {
                        let all_deps_done = task.dependencies.iter().all(|dep_id| {
                            if let Ok((dc, dt)) = parse_task_id(dep_id) {
                                proj_clone.capabilities[dc].tasks[dt].status.is_done()
                            } else {
                                false
                            }
                        });
                        if all_deps_done {
                            task.status = core::Status::Pending;
                            newly_unblocked += 1;
                            println!(
                                "Task C{}T{} auto-unblocked (dependencies met)",
                                c + 1,
                                t + 1
                            );
                        }
                    }
                }
            }

            storage::save_project(&proj)?;

            let msg = format!(
                "Sync complete. {} tasks completed, {} tasks unblocked.",
                updated_count, newly_unblocked
            );
            println!("{}", msg);
            if let Some(url) = notify {
                let _ = ureq::post(&url).send_json(serde_json::json!({"text": msg}));
            }
        }
        Some(Commands::Work {
            mark_done,
            graph,
            notify,
        }) => {
            if !storage::exists() {
                anyhow::bail!("No project found. Run 'harada compile' first.");
            }
            let mut proj = storage::load_project()?;

            if let Some(task_id) = mark_done {
                let (c, t) = parse_task_id(&task_id)?;
                let task = &mut proj.capabilities[c].tasks[t];
                task.status = core::Status::Completed;
                proj.events.push(core::Event {
                    timestamp: chrono::Utc::now(),
                    event_type: core::EventType::TaskCompleted {
                        task_id: task_id.clone(),
                        actor: task.assigned_to.name.clone(),
                    },
                });
                storage::save_project(&proj)?;
                println!("Manually marked {} as Completed.", task_id);
                return Ok(());
            }

            if graph {
                println!("digraph G {{");
                println!("  rankdir=LR;");
                for (c, cap) in proj.capabilities.iter().enumerate() {
                    for (t, task) in cap.tasks.iter().enumerate() {
                        let id = format!("C{}T{}", c + 1, t + 1);
                        let color = if task.status.is_done() {
                            "green"
                        } else if task.status == core::Status::Blocked {
                            "red"
                        } else {
                            "black"
                        };
                        println!(
                            "  {} [label=\"{}: {}\", color=\"{}\"];",
                            id, id, task.title, color
                        );
                        for dep in &task.dependencies {
                            println!("  {} -> {};", dep, id);
                        }
                    }
                }
                println!("}}");
                return Ok(());
            }

            // Bottleneck detection & Quick Wins
            let mut best_bottleneck = None;
            let mut max_score: f32 = -1.0;
            let mut quick_wins = Vec::new();

            let now = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs();
            let stale_threshold = 3 * 24 * 3600; // 3 days

            for (c, cap) in proj.capabilities.iter().enumerate() {
                for (t, task) in cap.tasks.iter().enumerate() {
                    if !task.status.is_done() && task.status != core::Status::Blocked {
                        // Quick win detector
                        if task.dependencies.is_empty() && task.estimated_difficulty <= 2 {
                            quick_wins.push((c, t));
                        }

                        let mut score = task.estimated_difficulty as f32;

                        // Git activity weighting
                        if let Some(ref_name) = &task.linked_ref {
                            if let Ok(ts) = git::get_last_commit_timestamp(ref_name) {
                                let age = now.saturating_sub(ts);
                                if age > stale_threshold {
                                    score *= 1.5; // Stale branch, higher priority blocker
                                } else {
                                    score *= 0.5; // In motion, lower priority
                                }
                            }
                        }

                        if score > max_score {
                            best_bottleneck = Some((c, t));
                            max_score = score;
                        }
                    }
                }
            }

            if !quick_wins.is_empty() {
                println!("--- Quick Wins Available ---");
                for (c, t) in quick_wins.iter().take(3) {
                    let task = &proj.capabilities[*c].tasks[*t];
                    println!(
                        "C{}T{} - {} (Difficulty: {})",
                        c + 1,
                        t + 1,
                        task.title,
                        task.estimated_difficulty
                    );
                }
                println!("----------------------------\n");
            }

            if let Some((c, t)) = best_bottleneck {
                let task = &proj.capabilities[c].tasks[t];

                let mut output = String::new();
                output.push_str(&format!(
                    "Next Bottleneck Action: C{}T{} - {}\n",
                    c + 1,
                    t + 1,
                    task.title
                ));
                output.push_str(&format!("Description: {}\n", task.description));
                output.push_str(&format!("Difficulty: {}\n", task.estimated_difficulty));
                if let Some(r) = &task.linked_ref {
                    output.push_str(&format!("Linked Ref: {}\n", r));
                }
                if !task.completion_criteria.is_empty() {
                    output.push_str(&format!(
                        "Completion Criteria: {}\n",
                        task.completion_criteria.join(", ")
                    ));
                }

                print!("{}", output);

                if let Some(url) = notify {
                    let _ = ureq::post(&url).send_json(serde_json::json!({"text": output}));
                }
            } else {
                println!("No unblocked tasks remaining!");
            }
        }
        Some(Commands::Stats {
            badge,
            export,
            since,
        }) => {
            if !storage::exists() {
                anyhow::bail!("No project found. Run 'harada compile' first.");
            }
            let proj = storage::load_project()?;
            let (done, total) = proj.task_count();
            let pct = done.checked_mul(100).and_then(|v| v.checked_div(total)).unwrap_or(0);

            if badge {
                let color = match pct {
                    0..=30 => "red",
                    31..=70 => "yellow",
                    _ => "brightgreen",
                };
                println!(
                    "![Harada Progress](https://img.shields.io/badge/Harada_Progress-{}%25-{}.svg)",
                    pct, color
                );
                return Ok(());
            }

            let mut filtered_events = proj.events.clone();
            if let Some(s) = since {
                let d = chrono::NaiveDate::parse_from_str(&s, "%Y-%m-%d")
                    .context("Invalid date format, use YYYY-MM-DD")?;
                let dt = d.and_hms_opt(0, 0, 0).unwrap().and_utc();
                filtered_events.retain(|e| e.timestamp >= dt);
            }

            if let Some(fmt) = export {
                if fmt == "json" {
                    println!("{}", serde_json::to_string_pretty(&filtered_events)?);
                } else if fmt == "csv" {
                    println!("timestamp,event_type,task_id,actor,ref_name,action");
                    for e in filtered_events {
                        match e.event_type {
                            core::EventType::TaskCompleted { task_id, actor } => {
                                println!(
                                    "{},TaskCompleted,{},{},,",
                                    e.timestamp.to_rfc3339(),
                                    task_id,
                                    actor
                                );
                            }
                            core::EventType::TaskAssigned { task_id, actor } => {
                                println!(
                                    "{},TaskAssigned,{},{},,",
                                    e.timestamp.to_rfc3339(),
                                    task_id,
                                    actor
                                );
                            }
                            core::EventType::GitSync { ref_name, action } => {
                                println!(
                                    "{},GitSync,,,{},{}",
                                    e.timestamp.to_rfc3339(),
                                    ref_name,
                                    action
                                );
                            }
                        }
                    }
                } else {
                    anyhow::bail!("Unsupported export format. Use 'csv' or 'json'");
                }
                return Ok(());
            }

            // TUI Dashboard Print
            println!("============================================================");
            println!("                   HARADA VELOCITY DASHBOARD                ");
            println!("============================================================");
            println!("Goal: {}", proj.goal);

            let bar_len = 40;
            let filled = (pct * bar_len) / 100;
            let bar: String = (0..bar_len)
                .map(|i| if i < filled { '█' } else { '░' })
                .collect();
            println!("Overall Progress: [{}] {}/{} ({}%)", bar, done, total, pct);
            println!("------------------------------------------------------------");
            println!("Capabilities:");
            for (i, cap) in proj.capabilities.iter().enumerate() {
                let (cd, ct) = proj.cap_progress(i);
                let cp = cd.checked_mul(100).and_then(|v| v.checked_div(ct)).unwrap_or(0);
                let cb: String = (0..20)
                    .map(|j| if j < (cp * 20 / 100) { '█' } else { '░' })
                    .collect();
                println!(
                    "  C{} [{}] {:<22} {}/{} ({}%)",
                    i + 1,
                    cb,
                    cap.cell.title,
                    cd,
                    ct,
                    cp
                );
            }

            // Velocity Calculation
            let now = chrono::Utc::now();
            let duration_days = (now - proj.created_at).num_days().max(1);
            let velocity = done as f64 / duration_days as f64;

            println!("------------------------------------------------------------");
            println!("Velocity: {:.1} tasks/day", velocity);

            if velocity > 0.0 {
                let remaining = total - done;
                let days_left = (remaining as f64 / velocity).ceil() as i64;
                println!("Projected ETA: {} days", days_left);
            } else {
                println!("Projected ETA: N/A (no tasks completed yet)");
            }

            // Actor breakdown
            let mut ai_tasks = 0;
            let mut self_tasks = 0;
            for e in &filtered_events {
                if let core::EventType::TaskCompleted { actor, .. } = &e.event_type {
                    if actor == "ai" || actor.to_lowercase().contains("claude") {
                        ai_tasks += 1;
                    } else {
                        self_tasks += 1;
                    }
                }
            }
            if ai_tasks > 0 || self_tasks > 0 {
                println!("------------------------------------------------------------");
                println!("Actor Breakdown (Completed Tasks):");
                println!("  Self : {}", self_tasks);
                println!("  AI   : {}", ai_tasks);
            }
            println!("============================================================");
        }
        Some(Commands::Init {
            github_action,
            pre_commit,
        }) => {
            if github_action {
                let yml = r#"name: Harada CI
on:
  push:
    branches: [ "main" ]
  pull_request:

jobs:
  harada-sync:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run Harada Sync
      run: |
        harada sync
        harada work
"#;
                std::fs::create_dir_all(".github/workflows")?;
                std::fs::write(".github/workflows/harada.yml", yml)?;
                println!("Created .github/workflows/harada.yml");
            }
            if pre_commit {
                let hook = r#"#!/bin/sh
harada work
"#;
                std::fs::create_dir_all(".git/hooks")?;
                std::fs::write(".git/hooks/pre-commit", hook)?;

                // Make hook executable
                #[cfg(unix)]
                {
                    use std::os::unix::fs::PermissionsExt;
                    let mut perms = std::fs::metadata(".git/hooks/pre-commit")?.permissions();
                    perms.set_mode(0o755);
                    std::fs::set_permissions(".git/hooks/pre-commit", perms)?;
                }
                println!("Created .git/hooks/pre-commit");
            }
            if !github_action && !pre_commit {
                println!("Please specify --github-action or --pre-commit");
            }

            // Capability 8: Hardening Git Ignorance
            if std::path::Path::new(".git").exists() {
                let gitignore_path = ".gitignore";
                let current_ignore = std::fs::read_to_string(gitignore_path).unwrap_or_default();
                if !current_ignore.contains(".harada/") && !current_ignore.contains(".harada") {
                    use std::io::Write;
                    let mut file = std::fs::OpenOptions::new()
                        .create(true)
                        .append(true)
                        .open(gitignore_path)?;
                    writeln!(file, "\n# Harada State\n.harada/")?;
                    println!("Appended .harada/ to .gitignore");
                }
            }
        }
        None => {
            println!("Harada Goal Compiler. Run 'harada --help' for commands.");
            if storage::exists() {
                let mut proj = storage::load_project()?;
                if io::stdout().is_terminal() {
                    let _ = tui::run(&mut proj);
                    let _ = storage::save_project(&proj);
                }
            }
        }
    }
    Ok(())
}
