use anyhow::{Context, Result};
use std::path::PathBuf;

use crate::core::Project;

fn dir() -> PathBuf {
    std::env::current_dir().unwrap_or_default().join(".harada")
}
fn path(name: &str) -> PathBuf {
    dir().join(name)
}

pub fn save_project(proj: &Project) -> Result<()> {
    let d = dir();
    std::fs::create_dir_all(&d).context("create .harada")?;
    let json = serde_json::to_string_pretty(proj)?;
    std::fs::write(path("project.json"), json)?;
    let meta = serde_json::json!({
        "version": 1, "created_at": proj.created_at, "frozen": proj.frozen
    });
    std::fs::write(path("meta.json"), serde_json::to_string_pretty(&meta)?)?;
    Ok(())
}

pub fn load_project() -> Result<Project> {
    let json = std::fs::read_to_string(path("project.json")).context("read project.json")?;
    let proj: Project = serde_json::from_str(&json)?;
    
    // Capability 8: Defensive bounds checking against state corruption
    if proj.capabilities.len() != 8 {
        anyhow::bail!("Corrupted state: Project must have exactly 8 capabilities, found {}", proj.capabilities.len());
    }
    for (i, cap) in proj.capabilities.iter().enumerate() {
        if cap.tasks.len() != 8 {
            anyhow::bail!("Corrupted state: Capability {} must have exactly 8 tasks, found {}", i+1, cap.tasks.len());
        }
    }
    
    Ok(proj)
}

pub fn project_path() -> PathBuf {
    path("project.json")
}
pub fn exists() -> bool {
    project_path().exists()
}
