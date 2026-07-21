use crate::engines::loop_detection::config::{FrostConfig, Sensitivity};
use crate::engines::loop_detection::engine::RuleEngine;
use crate::engines::loop_detection::history::HistoryTracker;

pub const ERROR_BUF_SIZE: usize = 1024;

pub struct FrostState {
    pub sensitivity: Sensitivity,
    pub max_repeats: usize,
    pub ignore_args: bool,
    pub history_window: Option<usize>,

    pub engine: RuleEngine,
    pub history: HistoryTracker,
    pub error_buffer: Vec<u8>,
    pub warning_buffer: Vec<u8>,
}

impl FrostState {
    pub fn new(yaml_str: &str) -> Result<Self, String> {
        let config = FrostConfig::from_yaml(yaml_str)?;

        let engine = RuleEngine::new(config.rules)?;
        let history = HistoryTracker::new();

        Ok(Self {
            sensitivity: config.sensitivity,
            max_repeats: config.max_repeats,
            ignore_args: config.ignore_args,
            history_window: config.history_window,
            engine,
            history,
            error_buffer: Vec::with_capacity(ERROR_BUF_SIZE),
            warning_buffer: Vec::with_capacity(ERROR_BUF_SIZE),
        })
    }

    pub fn block_result(&self) -> u8 {
        match self.sensitivity {
            Sensitivity::Low => 1,
            Sensitivity::Default => 2,
            Sensitivity::High => 3,
        }
    }

    pub fn get_effective_threshold(&self, _tool_name: &str) -> usize {
        match self.sensitivity {
            Sensitivity::Low => (self.max_repeats as f32 * 1.5) as usize,
            Sensitivity::Default => self.max_repeats,
            Sensitivity::High => (self.max_repeats as f32 * 0.6) as usize,
        }
    }

    pub fn set_error(&mut self, msg: &str) {
        self.error_buffer.clear();

        let max_len = (ERROR_BUF_SIZE - 1).min(msg.len());
        self.error_buffer
            .extend_from_slice(&msg.as_bytes()[..max_len]);
        self.error_buffer.push(0);
    }

    pub fn set_warning(&mut self, msg: &str) {
        self.warning_buffer.clear();

        let max_len = (ERROR_BUF_SIZE - 1).min(msg.len());
        self.warning_buffer
            .extend_from_slice(&msg.as_bytes()[..max_len]);
        self.warning_buffer.push(0);
    }

    pub fn has_warning(&self) -> bool {
        !self.warning_buffer.is_empty()
    }
}
