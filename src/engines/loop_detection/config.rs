use serde::Deserialize;

#[derive(Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum Sensitivity {
    Low,
    Default,
    High,
}

#[derive(Deserialize, Debug, Clone)]
pub struct JsonSchemaSubset {
    pub required: Option<Vec<String>>,
    #[serde(rename = "type")]
    pub schema_type: Option<String>,
}

#[derive(Deserialize, Debug, Clone)]
#[serde(tag = "type")]
#[serde(rename_all = "snake_case")]
pub enum RuleConfig {
    Regex { pattern: String },
    Exact { value: String },
    JsonSchema(JsonSchemaSubset),
}

#[derive(Deserialize, Debug, Clone)]
pub struct HavfrysConfig {
    #[serde(default = "default_sensitivity")]
    pub sensitivity: Sensitivity,
    #[serde(default = "default_max_repeats")]
    pub max_repeats: usize,
    #[serde(default)]
    pub ignore_args: bool,
    pub history_window: Option<usize>,

    #[serde(default)]
    pub rules: Vec<RuleConfig>,
}

impl HavfrysConfig {
    pub fn from_yaml(yaml_str: &str) -> Result<Self, String> {
        serde_yml::from_str(yaml_str).map_err(|e| format!("YAML parsing error: {}", e))
    }
}

fn default_sensitivity() -> Sensitivity {
    Sensitivity::Default
}

fn default_max_repeats() -> usize {
    3
}
