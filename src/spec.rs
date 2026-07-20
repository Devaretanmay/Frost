use crate::core::Project;
use anyhow::{Context, Result};
use std::fs;

pub fn generate_prompt(goal: &str, context: &str) -> String {
    let ctx_block = if context.is_empty() {
        String::new()
    } else {
        format!("Context:\n{}\n\n", context)
    };

    format!(
        r#"You are Harada, a strict Goal Compiler.
I need to compile the following goal into a 1x8x8 Mandala matrix.
Goal: {}

{}Constraints:
1. You MUST decompose the goal into EXACTLY 8 capabilities.
2. For each capability, you MUST generate EXACTLY 8 tasks.
3. Total tasks must be EXACTLY 64. No exceptions.
4. Each task must have a title, description, estimated_difficulty (1-5), completion_criteria (array of 1-3 strings), and validation_criteria (array of 1-3 strings).
5. Output ONLY valid JSON matching the schema below. No markdown formatting, no explanations.

Schema:
{{
  "goal": "{}",
  "capabilities": [
    {{
      "title": "String",
      "description": "String",
      "tasks": [
        {{
          "title": "String",
          "description": "String",
          "estimated_difficulty": 1,
          "completion_criteria": ["String"],
          "validation_criteria": ["String"],
          "dependencies": [] 
        }}
      ] // Exactly 8 tasks
    }}
  ] // Exactly 8 capabilities
}}
"#,
        goal, ctx_block, goal
    )
}

pub fn parse_and_import(file_path: &str) -> Result<Project> {
    let content = fs::read_to_string(file_path).context("Failed to read import file")?;

    let parsed: serde_json::Value = serde_json::from_str(&content).context("Failed to parse JSON. Ensure the AI output is strictly valid JSON without markdown blocks.")?;

    let goal_str = parsed["goal"].as_str().unwrap_or("Untitled Goal");
    let caps = parsed["capabilities"]
        .as_array()
        .context("Missing capabilities array")?;

    if caps.len() != 8 {
        anyhow::bail!(
            "Constraint violation: Matrix must have exactly 8 capabilities (found {})",
            caps.len()
        );
    }

    let mut project = Project::new(goal_str, &[]);
    project.capabilities.clear();

    for (i, cap) in caps.iter().enumerate() {
        let cap_title = cap["title"]
            .as_str()
            .map(|s| s.to_string())
            .unwrap_or_else(|| format!("Capability {}", i + 1));
        let cap_desc = cap["description"].as_str().unwrap_or("");

        let mut c_cell = crate::core::Cell::new(crate::core::Role::Capability, &cap_title);
        c_cell.description = cap_desc.to_string();

        let mut capability = crate::core::Capability {
            cell: c_cell,
            tasks: Vec::new(),
        };

        let tasks = cap["tasks"]
            .as_array()
            .context("Missing tasks array in capability")?;
        if tasks.len() != 8 {
            anyhow::bail!(
                "Constraint violation: Capability '{}' must have exactly 8 tasks (found {})",
                cap_title,
                tasks.len()
            );
        }

        for (j, task) in tasks.iter().enumerate() {
            let task_title = task["title"]
                .as_str()
                .map(|s| s.to_string())
                .unwrap_or_else(|| format!("Task {}", j + 1));
            let mut t_cell = crate::core::Cell::new(crate::core::Role::Task, &task_title);
            t_cell.description = task["description"].as_str().unwrap_or("").to_string();
            t_cell.estimated_difficulty = task["estimated_difficulty"].as_u64().unwrap_or(1) as u32;

            if let Some(arr) = task["completion_criteria"].as_array() {
                t_cell.completion_criteria = arr
                    .iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect();
            }
            if let Some(arr) = task["validation_criteria"].as_array() {
                t_cell.validation_criteria = arr
                    .iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect();
            }
            if let Some(arr) = task["dependencies"].as_array() {
                t_cell.dependencies = arr
                    .iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect();
            }

            capability.tasks.push(t_cell);
        }

        project.capabilities.push(capability);
    }

    Ok(project)
}
