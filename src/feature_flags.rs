use dashmap::DashMap;
use serde::{Deserialize, Serialize};
/// Feature flag management system
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FeatureState {
    Disabled,
    Enabled,
    Canary,
    GradualRollout { percentage: u8 },
    Shadow,
}

#[derive(Debug)]
pub struct FeatureFlag {
    pub name: String,
    pub state: FeatureState,
    pub error_count: AtomicU32,
    pub enabled: AtomicBool,
    pub error_threshold: u32,
}

impl FeatureFlag {
    pub fn new(name: String, state: FeatureState) -> Self {
        let enabled = matches!(state, FeatureState::Enabled);
        Self {
            name,
            state,
            error_count: AtomicU32::new(0),
            enabled: AtomicBool::new(enabled),
            error_threshold: 10,
        }
    }

    pub fn is_enabled(&self, request_id: Option<&str>) -> bool {
        if !self.enabled.load(Ordering::Relaxed) {
            return false;
        }

        match &self.state {
            FeatureState::Disabled => false,
            FeatureState::Enabled => true,
            FeatureState::Canary => {
                // Simple hash-based canary deployment
                if let Some(id) = request_id {
                    let hash = self.simple_hash(id);
                    hash % 100 < 5 // 5% canary
                } else {
                    false
                }
            }
            FeatureState::GradualRollout { percentage } => {
                if let Some(id) = request_id {
                    let hash = self.simple_hash(id);
                    hash % 100 < (*percentage as u64)
                } else {
                    false
                }
            }
            FeatureState::Shadow => false, // Shadow mode: feature is off but monitoring continues
        }
    }

    pub fn record_error(&self) {
        let current_errors = self.error_count.fetch_add(1, Ordering::Relaxed);
        if current_errors >= self.error_threshold {
            self.enabled.store(false, Ordering::Relaxed);
        }
    }

    pub fn reset_errors(&self) {
        self.error_count.store(0, Ordering::Relaxed);
        self.enabled.store(true, Ordering::Relaxed);
    }

    fn simple_hash(&self, input: &str) -> u64 {
        let mut hash = 5381u64;
        for byte in input.bytes() {
            hash = hash.wrapping_mul(33).wrapping_add(byte as u64);
        }
        hash
    }
}

pub struct FeatureFlagManager {
    flags: DashMap<String, FeatureFlag>,
}

impl Default for FeatureFlagManager {
    fn default() -> Self {
        Self::new()
    }
}

impl FeatureFlagManager {
    pub fn new() -> Self {
        let manager = Self {
            flags: DashMap::new(),
        };

        // Initialize default feature flags
        manager.add_flag(
            "rust_routing".to_string(),
            FeatureState::GradualRollout { percentage: 10 },
        );
        manager.add_flag("rust_token_counting".to_string(), FeatureState::Enabled);
        manager.add_flag(
            "rust_rate_limiting".to_string(),
            FeatureState::GradualRollout { percentage: 25 },
        );
        manager.add_flag("rust_connection_pool".to_string(), FeatureState::Canary);

        manager
    }

    pub fn add_flag(&self, name: String, state: FeatureState) {
        let flag = FeatureFlag::new(name.clone(), state);
        self.flags.insert(name, flag);
    }

    pub fn is_enabled(&self, feature_name: &str, request_id: Option<&str>) -> bool {
        if let Some(flag) = self.flags.get(feature_name) {
            flag.is_enabled(request_id)
        } else {
            false
        }
    }

    pub fn record_error(&self, feature_name: &str) {
        if let Some(flag) = self.flags.get(feature_name) {
            flag.record_error();
        }
    }

    pub fn reset_errors(&self, feature_name: Option<&str>) {
        if let Some(name) = feature_name {
            if let Some(flag) = self.flags.get(name) {
                flag.reset_errors();
            }
        } else {
            // Reset all flags
            for flag in self.flags.iter() {
                flag.value().reset_errors();
            }
        }
    }

    pub fn get_status(&self) -> HashMap<String, serde_json::Value> {
        let mut result = HashMap::new();

        for entry in self.flags.iter() {
            let name = entry.key();
            let flag = entry.value();

            let mut flag_status = HashMap::new();
            flag_status.insert(
                "state".to_string(),
                match &flag.state {
                    FeatureState::Disabled => serde_json::Value::String("disabled".to_string()),
                    FeatureState::Enabled => serde_json::Value::String("enabled".to_string()),
                    FeatureState::Canary => serde_json::Value::String("canary".to_string()),
                    FeatureState::GradualRollout { percentage } => serde_json::json!({
                        "type": "gradual_rollout",
                        "percentage": percentage
                    }),
                    FeatureState::Shadow => serde_json::Value::String("shadow".to_string()),
                },
            );

            flag_status.insert(
                "enabled".to_string(),
                serde_json::Value::Bool(flag.enabled.load(Ordering::Relaxed)),
            );
            flag_status.insert(
                "error_count".to_string(),
                serde_json::Value::Number(serde_json::Number::from(
                    flag.error_count.load(Ordering::Relaxed),
                )),
            );
            flag_status.insert(
                "error_threshold".to_string(),
                serde_json::Value::Number(serde_json::Number::from(flag.error_threshold)),
            );

            result.insert(
                name.clone(),
                serde_json::Value::Object(flag_status.into_iter().collect()),
            );
        }

        result
    }
}

// Global feature flag manager
lazy_static::lazy_static! {
    static ref FEATURE_MANAGER: FeatureFlagManager = FeatureFlagManager::new();
}

pub fn is_feature_enabled(feature_name: &str, request_id: Option<&str>) -> bool {
    FEATURE_MANAGER.is_enabled(feature_name, request_id)
}

pub fn record_feature_error(feature_name: &str) {
    FEATURE_MANAGER.record_error(feature_name);
}

pub fn reset_feature_errors(feature_name: Option<&str>) {
    FEATURE_MANAGER.reset_errors(feature_name);
}

pub fn get_all_feature_status() -> HashMap<String, serde_json::Value> {
    FEATURE_MANAGER.get_status()
}
