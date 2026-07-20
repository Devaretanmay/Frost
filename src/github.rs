use anyhow::{Context, Result};
use std::env;

#[derive(Debug)]
pub struct Issue {
    pub title: String,
    pub body: String,
}

pub fn get_issue(owner: &str, repo: &str, issue_number: &str) -> Result<Issue> {
    let url = format!(
        "https://api.github.com/repos/{}/{}/issues/{}",
        owner, repo, issue_number
    );
    let token = env::var("HARADA_GIT_TOKEN")
        .or_else(|_| env::var("GITHUB_TOKEN"))
        .unwrap_or_default();

    let mut request = ureq::get(&url)
        .header("User-Agent", "harada-cli")
        .header("Accept", "application/vnd.github.v3+json");

    if !token.is_empty() {
        request = request.header("Authorization", format!("Bearer {}", token));
    }

    let response = request
        .call()
        .context("Failed to fetch issue from GitHub API")?;

    if response.status() != 200 {
        anyhow::bail!("GitHub API returned status: {}", response.status());
    }

    let json: serde_json::Value = response
        .into_body()
        .read_json()
        .context("Failed to parse GitHub response as JSON")?;

    let title = json["title"]
        .as_str()
        .unwrap_or("Untitled Issue")
        .to_string();
    let body = json["body"].as_str().unwrap_or("").to_string();

    Ok(Issue { title, body })
}
