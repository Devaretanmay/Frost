use blake3;

pub fn hash_field_name(field_name: &str) -> String {
    let h = blake3::hash(field_name.as_bytes());
    h.to_hex().as_str()[..8].to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_string() {
        assert_eq!(hash_field_name(""), "af1349b9");
    }

    #[test]
    fn deterministic() {
        assert_eq!(hash_field_name("test"), hash_field_name("test"));
    }

    #[test]
    fn output_length_is_8() {
        assert_eq!(hash_field_name("a").len(), 8);
        assert_eq!(hash_field_name(&"x".repeat(1000)).len(), 8);
    }
}
