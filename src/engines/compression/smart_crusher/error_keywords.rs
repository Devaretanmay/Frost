pub const ERROR_KEYWORDS: &[&str] = &[
    "error",
    "exception",
    "failed",
    "failure",
    "critical",
    "fatal",
    "crash",
    "panic",
    "abort",
    "timeout",
    "denied",
    "rejected",
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn matches_python_count() {
        assert_eq!(ERROR_KEYWORDS.len(), 12);
    }

    #[test]
    fn all_lowercase_invariant() {
        for &kw in ERROR_KEYWORDS {
            assert_eq!(
                kw,
                kw.to_lowercase(),
                "ERROR_KEYWORDS must all be lowercase"
            );
        }
    }

    #[test]
    fn pinned_membership() {
        let expected = [
            "error",
            "exception",
            "failed",
            "failure",
            "critical",
            "fatal",
            "crash",
            "panic",
            "abort",
            "timeout",
            "denied",
            "rejected",
        ];
        let actual: std::collections::BTreeSet<&str> = ERROR_KEYWORDS.iter().copied().collect();
        let expected: std::collections::BTreeSet<&str> = expected.iter().copied().collect();
        assert_eq!(actual, expected);
    }
}
