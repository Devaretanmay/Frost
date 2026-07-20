use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Role {
    Goal,
    Capability,
    Task,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Status {
    Pending,
    InProgress,
    Completed,
    Failed,
    NeedsReview,
    NotRequired,
    Blocked,
    Waiting,
    Skipped,
    Cancelled,
}
impl Status {
    pub fn is_done(&self) -> bool {
        matches!(
            self,
            Status::Completed | Status::Skipped | Status::Cancelled | Status::NotRequired
        )
    }
    pub fn cycle(&self) -> Self {
        match self {
            Status::Pending => Status::InProgress,
            Status::InProgress => Status::Completed,
            Status::Completed => Status::NeedsReview,
            Status::NeedsReview => Status::Pending,
            Status::Blocked => Status::InProgress,
            Status::Waiting => Status::InProgress,
            s => s.clone(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ExecutorKind {
    Human,
    AI,
    Team,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Executor {
    pub kind: ExecutorKind,
    pub name: String,
    pub tool: Option<String>,
    pub requires_review: bool,
}
impl Default for Executor {
    fn default() -> Self {
        Self {
            kind: ExecutorKind::Human,
            name: "Me".into(),
            tool: None,
            requires_review: false,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Cell {
    pub role: Role,
    pub title: String,
    pub description: String,
    pub status: Status,
    pub assigned_to: Executor,
    pub notes: String,
    pub completion_criteria: Vec<String>,
    pub validation_criteria: Vec<String>,
    pub estimated_difficulty: u32,
    pub dependencies: Vec<String>,
    pub linked_ref: Option<String>,
    pub test_ref: Option<String>,
}
impl Cell {
    pub fn new(role: Role, title: &str) -> Self {
        Self {
            role,
            title: title.into(),
            description: String::new(),
            status: Status::Pending,
            assigned_to: Executor::default(),
            notes: String::new(),
            completion_criteria: Vec::new(),
            validation_criteria: Vec::new(),
            estimated_difficulty: 1,
            dependencies: Vec::new(),
            linked_ref: None,
            test_ref: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Capability {
    pub cell: Cell,
    pub tasks: Vec<Cell>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EventType {
    TaskCompleted { task_id: String, actor: String },
    TaskAssigned { task_id: String, actor: String },
    GitSync { ref_name: String, action: String },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub event_type: EventType,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Project {
    pub goal: String,
    pub capabilities: Vec<Capability>,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub frozen: bool,
    #[serde(default)]
    pub events: Vec<Event>,
}
impl Project {
    pub fn new(goal: &str, cap_names: &[&str]) -> Self {
        let caps = cap_names
            .iter()
            .map(|name| {
                let tasks = (0..8)
                    .map(|j| Cell::new(Role::Task, &format!("T{}", j + 1)))
                    .collect();
                Capability {
                    cell: Cell::new(Role::Capability, name),
                    tasks,
                }
            })
            .collect();
        Self {
            goal: goal.into(),
            capabilities: caps,
            created_at: chrono::Utc::now(),
            frozen: false,
            events: Vec::new(),
        }
    }

    pub fn task_count(&self) -> (usize, usize) {
        let total = self.capabilities.iter().map(|c| c.tasks.len()).sum();
        let done = self
            .capabilities
            .iter()
            .flat_map(|c| &c.tasks)
            .filter(|t| t.status.is_done())
            .count();
        (done, total)
    }

    pub fn cap_progress(&self, i: usize) -> (usize, usize) {
        let tasks = &self.capabilities[i].tasks;
        (
            tasks.iter().filter(|t| t.status.is_done()).count(),
            tasks.len(),
        )
    }
}
