#[derive(Debug, PartialEq)]
pub enum LoopVerdict {
    Allow,
    WarnOscillation(String),
    BlockExactMatch(String),
    BlockOscillation(String),
}

const MAX_TOOLS: usize = 256;
const SEQ_LEN: usize = 16;

pub struct ToolArena {
    names: Vec<String>,
}

impl Default for ToolArena {
    fn default() -> Self {
        Self::new()
    }
}

impl ToolArena {
    pub fn new() -> Self {
        Self {
            names: Vec::with_capacity(MAX_TOOLS),
        }
    }

    pub fn get_or_insert(&mut self, name: &str) -> u16 {
        for (i, n) in self.names.iter().enumerate() {
            if n == name {
                return i as u16;
            }
        }
        if self.names.len() < MAX_TOOLS {
            self.names.push(name.to_string());
            (self.names.len() - 1) as u16
        } else {
            u16::MAX
        }
    }
}

pub struct HistoryTracker {
    pub call_history: Vec<(String, String)>,
    tool_arena: ToolArena,
    sequence_ring: [u16; SEQ_LEN],
    sequence_idx: usize,
    oscillation_cycles: usize,
}

impl Default for HistoryTracker {
    fn default() -> Self {
        Self::new()
    }
}

impl HistoryTracker {
    pub fn new() -> Self {
        Self {
            call_history: Vec::new(),
            tool_arena: ToolArena::new(),
            sequence_ring: [0; SEQ_LEN],
            sequence_idx: 0,
            oscillation_cycles: 0,
        }
    }

    fn check_argument_variance(&self, period: usize) -> bool {
        let len = self.call_history.len();
        if len < period * 2 {
            return true;
        }
        for i in 1..=period {
            let (_, args1) = &self.call_history[len - i];
            let (_, args2) = &self.call_history[len - i - period];
            if args1 != args2 {
                return true;
            }
        }
        false
    }

    pub fn check_loop(
        &mut self,
        tool: &str,
        args: &str,
        ignore_args: bool,
        max_repeats: usize,
        history_window: Option<usize>,
    ) -> LoopVerdict {
        let mut repeat_count = 1;
        let window_size = history_window
            .unwrap_or(max_repeats * 2)
            .max(max_repeats * 2);

        for (past_tool, past_args) in self.call_history.iter().rev().take(window_size) {
            if past_tool == tool && (ignore_args || past_args == args) {
                repeat_count += 1;
            }
        }

        if repeat_count >= max_repeats {
            return LoopVerdict::BlockExactMatch(format!(
                "Agent appears to be looping on tool {}",
                tool
            ));
        }

        let tool_id = self.tool_arena.get_or_insert(tool);
        self.sequence_ring[self.sequence_idx % SEQ_LEN] = tool_id;
        self.sequence_idx += 1;
        self.call_history.push((tool.to_string(), args.to_string()));

        if let Some(period) = self.detect_oscillation() {
            self.oscillation_cycles += 1;
            let changing = self.check_argument_variance(period);
            if !changing {
                return LoopVerdict::BlockOscillation(
                    "Agent is stuck in an oscillation loop with identical arguments.".into(),
                );
            }
            if self.oscillation_cycles >= max_repeats {
                return LoopVerdict::BlockOscillation(format!(
                    "Agent oscillated {} times without progress. Pivot required.",
                    self.oscillation_cycles
                ));
            }
            return LoopVerdict::WarnOscillation(format!(
                "Agent appears to be oscillating between tools (cycle {}). Are arguments converging?",
                self.oscillation_cycles
            ));
        }

        self.oscillation_cycles = 0;
        LoopVerdict::Allow
    }

    fn detect_oscillation(&self) -> Option<usize> {
        if self.sequence_idx < 4 {
            return None;
        }
        let max_len = self.sequence_idx.min(SEQ_LEN);
        let mut window = Vec::with_capacity(max_len);
        for i in 0..max_len {
            let idx = (self.sequence_idx - max_len + i) % SEQ_LEN;
            window.push(self.sequence_ring[idx]);
        }
        for period in 2..=(max_len / 2) {
            let mut repeating = true;
            for i in period..max_len {
                if window[i] != window[i - period] {
                    repeating = false;
                    break;
                }
            }
            if repeating {
                return Some(period);
            }
        }
        None
    }
}
