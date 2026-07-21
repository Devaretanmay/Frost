pub mod backends;

use std::time::Duration;

pub use backends::InMemoryCcrStore;

pub const DEFAULT_CAPACITY: usize = 1000;
pub const DEFAULT_TTL: Duration = Duration::from_secs(1800);

pub fn compute_key(payload: &[u8]) -> String {
    let h = blake3::hash(payload);
    let hex = h.to_hex();
    hex.as_str()[..24].to_string()
}


