use regex::Regex;
use serde_json::Value;

use crate::engines::loop_detection::config::RuleConfig;

pub enum CompiledRule {
    Regex(Regex),
    Exact(String),
    JsonSchema {
        required: Vec<String>,
        schema_type: String,
    },
}

impl CompiledRule {
    pub fn matches(&self, args: &str) -> Result<(), &'static str> {
        match self {
            CompiledRule::Regex(regex) => {
                if !regex.is_match(args) {
                    return Err("Failed regex rule");
                }
                Ok(())
            }
            CompiledRule::Exact(val) => {
                if args != val {
                    return Err("Failed exact match rule");
                }
                Ok(())
            }
            CompiledRule::JsonSchema {
                required,
                schema_type,
            } => {
                let val: Value = serde_json::from_str(args).map_err(|_| "Invalid JSON")?;
                if schema_type == "object" && !val.is_object() {
                    return Err("JSON schema type mismatch (expected object)");
                }
                if schema_type == "object" {
                    if let Some(obj) = val.as_object() {
                        if !required.iter().all(|req| obj.contains_key(req)) {
                            return Err("Missing required field in JSON");
                        }
                    }
                }
                Ok(())
            }
        }
    }
}

pub struct RuleEngine {
    pub rules: Vec<CompiledRule>,
}

impl RuleEngine {
    pub fn new(configs: Vec<RuleConfig>) -> Result<Self, String> {
        let mut compiled_rules = Vec::new();
        for rule in configs {
            match rule {
                RuleConfig::Regex { pattern } => {
                    let r = Regex::new(&pattern).map_err(|e| format!("Regex error: {}", e))?;
                    compiled_rules.push(CompiledRule::Regex(r));
                }
                RuleConfig::Exact { value } => {
                    compiled_rules.push(CompiledRule::Exact(value));
                }
                RuleConfig::JsonSchema(schema) => {
                    let req = schema.required.unwrap_or_default();
                    let t = schema.schema_type.unwrap_or_else(|| String::from("object"));
                    compiled_rules.push(CompiledRule::JsonSchema {
                        required: req,
                        schema_type: t,
                    });
                }
            }
        }
        Ok(Self {
            rules: compiled_rules,
        })
    }

    pub fn validate(&self, args: &str) -> Result<(), &'static str> {
        for rule in &self.rules {
            rule.matches(args)?;
        }
        Ok(())
    }
}
