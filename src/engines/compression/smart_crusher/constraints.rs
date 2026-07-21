use std::collections::BTreeSet;

use serde_json::Value;

use super::outliers::{detect_error_items_for_preservation, detect_structural_outliers};

/// Returns indices of items that must be preserved during crushing.
/// Merges results from error-keyword detection and structural-outlier detection.
pub fn must_keep(items: &[Value], item_strings: Option<&[String]>) -> Vec<usize> {
    let mut kept: BTreeSet<usize> = BTreeSet::new();
    for idx in detect_error_items_for_preservation(items, item_strings) {
        kept.insert(idx);
    }
    for idx in detect_structural_outliers(items) {
        kept.insert(idx);
    }
    kept.into_iter().collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn must_keep_finds_error_items() {
        let mut items: Vec<Value> = (0..9).map(|i| json!({"id": i, "status": "ok"})).collect();
        items.push(json!({"id": 9, "status": "ERROR", "msg": "FATAL: boom"}));
        let kept = must_keep(&items, None);
        assert!(kept.contains(&9), "error item must be flagged for keep");
    }

    #[test]
    fn must_keep_uses_item_strings_when_provided() {
        let items: Vec<Value> = vec![json!({"a": 1}), json!({"a": "exception"})];
        let strings: Vec<String> = items
            .iter()
            .map(|v| serde_json::to_string(v).unwrap())
            .collect();
        let with_cache = must_keep(&items, Some(&strings));
        let without_cache = must_keep(&items, None);
        assert_eq!(with_cache, without_cache);
        assert!(with_cache.contains(&1));
    }

    #[test]
    fn must_keep_finds_structural_outliers() {
        let mut items: Vec<Value> = (0..20)
            .map(|i| json!({"id": i, "kind": "common"}))
            .collect();
        items.push(json!({"id": 20, "kind": "common", "rare_extra_field": "x"}));
        let kept = must_keep(&items, None);
        assert!(
            kept.contains(&20),
            "item with rare field should be a structural outlier"
        );
    }

    #[test]
    fn must_keep_merges_error_and_outlier_indices() {
        let mut items: Vec<Value> = (0..20)
            .map(|i| json!({"id": i, "kind": "common"}))
            .collect();
        items.push(json!({"id": 20, "kind": "common", "x": "rare"}));
        items.push(json!({"id": 21, "status": "error", "msg": "FATAL"}));
        let kept = must_keep(&items, None);
        assert!(kept.contains(&20), "structural outlier must be kept");
        assert!(kept.contains(&21), "error item must be kept");
    }

    #[test]
    fn must_keep_handles_empty_array() {
        let kept = must_keep(&[], None);
        assert!(kept.is_empty());
    }
}
