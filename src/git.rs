use anyhow::{Context, Result};
use std::process::Command;

#[derive(Debug, Clone)]
pub struct GitContext {
    pub owner: String,
    pub repo: String,
    pub branch: String,
}

pub fn get_context() -> Result<GitContext> {
    let branch = Command::new("git")
        .args(["branch", "--show-current"])
        .output()
        .context("Failed to run git branch")?;
    let branch = String::from_utf8(branch.stdout)?.trim().to_string();

    let remote = Command::new("git")
        .args(["config", "--get", "remote.origin.url"])
        .output()
        .context("Failed to get remote origin url")?;
    let remote_url = String::from_utf8(remote.stdout)?.trim().to_string();

    // Parse owner/repo from remote URL
    // Supports:
    // https://github.com/owner/repo.git
    // git@github.com:owner/repo.git
    let path = if remote_url.starts_with("http") {
        let parts: Vec<&str> = remote_url.split("github.com/").collect();
        if parts.len() < 2 {
            anyhow::bail!("Unsupported remote URL format");
        }
        parts[1].trim_end_matches(".git").to_string()
    } else if remote_url.starts_with("git@") {
        let parts: Vec<&str> = remote_url.split(':').collect();
        if parts.len() < 2 {
            anyhow::bail!("Unsupported remote URL format");
        }
        parts[1].trim_end_matches(".git").to_string()
    } else {
        anyhow::bail!("Unsupported remote URL format");
    };

    let path_parts: Vec<&str> = path.split('/').collect();
    if path_parts.len() < 2 {
        anyhow::bail!("Invalid owner/repo path in remote");
    }

    Ok(GitContext {
        owner: path_parts[0].to_string(),
        repo: path_parts[1].to_string(),
        branch,
    })
}

pub fn get_diff(base_ref: Option<&str>) -> Result<String> {
    let base = base_ref.unwrap_or("main");
    let diff = Command::new("git")
        .args(["diff", base])
        .output()
        .context("Failed to run git diff")?;

    if !diff.status.success() {
        anyhow::bail!("git diff failed: {}", String::from_utf8_lossy(&diff.stderr));
    }

    Ok(String::from_utf8_lossy(&diff.stdout).into_owned())
}

pub fn ref_exists(ref_name: &str) -> Result<bool> {
    let output = Command::new("git")
        .args(["rev-parse", "--verify", ref_name])
        .output()?;
    Ok(output.status.success())
}

pub fn is_merged(ref_name: &str, base: &str) -> Result<bool> {
    let output = Command::new("git")
        .args(["merge-base", "--is-ancestor", ref_name, base])
        .output()?;
    Ok(output.status.success())
}

pub fn get_last_commit_timestamp(ref_name: &str) -> Result<u64> {
    let output = Command::new("git")
        .args(["log", "-1", "--format=%ct", ref_name])
        .output()?;
    if !output.status.success() {
        anyhow::bail!("Failed to get last commit timestamp for {}", ref_name);
    }
    let ts_str = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let ts = ts_str.parse::<u64>().context("Invalid timestamp format")?;
    Ok(ts)
}
