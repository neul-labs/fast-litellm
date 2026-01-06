//! Model pricing and context window data loaded from LiteLLM's pricing JSON.
//! This provides up-to-date pricing for hundreds of models.
//!
//! To update pricing, run:
//! ```bash
//! DOWNLOAD_MODEL_PRICING=1 cargo build
//! ```

use dashmap::DashMap;
use serde::Deserialize;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::OnceLock;

/// Tracks pricing data loading status and metrics
struct PricingStats {
    /// Number of models loaded from JSON
    models_loaded: AtomicUsize,
    /// Number of lookup failures (model not found)
    lookup_failures: AtomicUsize,
    /// Whether the JSON file was successfully loaded
    json_loaded_successfully: AtomicUsize, // 0 = no, 1 = yes
}

impl PricingStats {
    const fn new() -> Self {
        Self {
            models_loaded: AtomicUsize::new(0),
            lookup_failures: AtomicUsize::new(0),
            json_loaded_successfully: AtomicUsize::new(0),
        }
    }

    fn record_model_load(&self, count: usize) {
        self.models_loaded.store(count, Ordering::Relaxed);
    }

    fn record_lookup_failure(&self) {
        self.lookup_failures.fetch_add(1, Ordering::Relaxed);
    }

    fn record_json_loaded(&self, success: bool) {
        self.json_loaded_successfully.store(if success { 1 } else { 0 }, Ordering::Relaxed);
    }

    fn json_loaded(&self) -> bool {
        self.json_loaded_successfully.load(Ordering::Relaxed) == 1
    }
}

/// Pricing data structure from LiteLLM's model_prices_and_context_window.json
#[derive(Debug, Clone, Deserialize)]
pub struct ModelPricing {
    pub litellm_provider: Option<String>,
    pub mode: Option<String>,
    #[serde(default)]
    pub max_input_tokens: Option<u32>,
    #[serde(default)]
    pub max_output_tokens: Option<u32>,
    #[serde(default)]
    pub max_tokens: Option<u32>,
    #[serde(default)]
    pub input_cost_per_token: Option<f64>,
    #[serde(default)]
    pub output_cost_per_token: Option<f64>,
    #[serde(default)]
    pub output_cost_per_image: Option<f64>,
    #[serde(default)]
    pub input_cost_per_pixel: Option<f64>,
}

/// Loaded pricing data
pub struct PricingData {
    /// Map of model name -> pricing info
    pub models: HashMap<String, ModelPricing>,
    /// Cache for fast lookups: input model -> whether found
    lookup_cache: DashMap<String, bool>,
}

impl PricingData {
    /// Create new pricing data with empty maps
    pub fn new() -> Self {
        Self {
            models: HashMap::new(),
            lookup_cache: DashMap::new(),
        }
    }

    /// Insert a model with its pricing
    pub fn insert(&mut self, model: String, pricing: ModelPricing) {
        self.models.insert(model, pricing);
        self.lookup_cache.clear();
    }

    /// Find pricing for a model, trying various name normalizations
    pub fn find_pricing(&self, model: &str) -> Option<&ModelPricing> {
        // Check cache first (cache miss results)
        if let Some(found) = self.lookup_cache.get(model) {
            if !*found {
                // Record lookup failure for unknown model
                get_pricing_stats().record_lookup_failure();
                return None;
            }
            return Some(
                self.models
                    .get(model)
                    .expect("cache entry should exist if marked as found"),
            );
        }

        // Find the pricing
        let result = self.find_pricing_uncached(model);

        // Cache the result
        self.lookup_cache.insert(model.to_string(), result.is_some());

        // Record failure if not found
        if result.is_none() {
            get_pricing_stats().record_lookup_failure();
        }

        result
    }

    fn find_pricing_uncached(&self, model: &str) -> Option<&ModelPricing> {
        // Direct match
        if let Some(pricing) = self.models.get(model) {
            return Some(pricing);
        }

        // Try without provider prefix (e.g., "gpt-4" from "azure/gpt-4")
        if let Some(slash_pos) = model.find('/') {
            let without_prefix = &model[slash_pos + 1..];
            if let Some(pricing) = self.models.get(without_prefix) {
                // Make sure it's not chat+completion mode confusion
                if pricing.mode.as_ref().map(|m| m.contains("chat")).unwrap_or(true) {
                    return Some(pricing);
                }
            }
        }

        // Try with common provider prefixes
        if let Some(pricing) = self.models.get(&format!("openai/{}", model)) {
            return Some(pricing);
        }
        if let Some(pricing) = self.models.get(&format!("azure/{}", model)) {
            return Some(pricing);
        }
        if let Some(pricing) = self.models.get(&format!("anthropic.{}", model)) {
            return Some(pricing);
        }
        if let Some(pricing) = self.models.get(&format!("google/{}", model)) {
            return Some(pricing);
        }
        if let Some(pricing) = self.models.get(&format!("bedrock/{}", model)) {
            return Some(pricing);
        }

        None
    }

    /// Get input cost per 1M tokens for a model
    pub fn get_input_cost_per_1m(&self, model: &str) -> Option<f64> {
        self.find_pricing(model)
            .and_then(|p| p.input_cost_per_token)
            .map(|cost| cost * 1_000_000.0)
    }

    /// Get output cost per 1M tokens for a model
    pub fn get_output_cost_per_1m(&self, model: &str) -> Option<f64> {
        self.find_pricing(model)
            .and_then(|p| p.output_cost_per_token)
            .map(|cost| cost * 1_000_000.0)
    }

    /// Get context window (max input + max output) for a model
    pub fn get_context_window(&self, model: &str) -> Option<u32> {
        self.find_pricing(model).and_then(|p| {
            let input = p.max_input_tokens.unwrap_or(0);
            let output = p.max_output_tokens.or(p.max_tokens).unwrap_or(0);
            if input > 0 || output > 0 {
                Some(input + output)
            } else {
                None
            }
        })
    }

    /// Get max output tokens for a model
    pub fn get_max_output(&self, model: &str) -> Option<u32> {
        self.find_pricing(model)
            .and_then(|p| p.max_output_tokens.or(p.max_tokens))
    }
}

/// Get the pricing data file path
fn get_pricing_file_path() -> Option<PathBuf> {
    // Try to find the pricing file from the build output
    if let Ok(out_dir) = std::env::var("OUT_DIR") {
        let path = PathBuf::from(out_dir).join("model_prices.json");
        if path.exists() {
            return Some(path);
        }
    }

    // Fall back to checking in the source directory (for local development)
    let local_path = PathBuf::from("model_prices.json");
    if local_path.exists() {
        return Some(local_path);
    }

    None
}

/// Load pricing data from JSON file
fn load_pricing_data() -> PricingData {
    let mut data = PricingData::new();

    // Get stats reference for recording
    let stats = get_pricing_stats();

    if let Some(pricing_file) = get_pricing_file_path() {
        match fs::read_to_string(pricing_file) {
            Ok(content) => {
                match serde_json::from_str::<serde_json::Value>(&content) {
                    Ok(json) => {
                        // Parse the JSON structure (skip "sample_spec" key)
                        if let Some(models) = json.as_object() {
                            for (model_name, model_data) in models {
                                // Skip the sample_spec entry
                                if model_name == "sample_spec" {
                                    continue;
                                }

                                if let Some(pricing_info) = model_data.as_object() {
                                    let pricing = ModelPricing {
                                        litellm_provider: pricing_info
                                            .get("litellm_provider")
                                            .and_then(|v| v.as_str().map(String::from)),
                                        mode: pricing_info
                                            .get("mode")
                                            .and_then(|v| v.as_str().map(String::from)),
                                        max_input_tokens: pricing_info
                                            .get("max_input_tokens")
                                            .and_then(|v| v.as_u64().map(|u| u as u32)),
                                        max_output_tokens: pricing_info
                                            .get("max_output_tokens")
                                            .and_then(|v| v.as_u64().map(|u| u as u32)),
                                        max_tokens: pricing_info
                                            .get("max_tokens")
                                            .and_then(|v| v.as_u64().map(|u| u as u32)),
                                        input_cost_per_token: pricing_info
                                            .get("input_cost_per_token")
                                            .and_then(|v| v.as_f64()),
                                        output_cost_per_token: pricing_info
                                            .get("output_cost_per_token")
                                            .and_then(|v| v.as_f64()),
                                        output_cost_per_image: pricing_info
                                            .get("output_cost_per_image")
                                            .and_then(|v| v.as_f64()),
                                        input_cost_per_pixel: pricing_info
                                            .get("input_cost_per_pixel")
                                            .and_then(|v| v.as_f64()),
                                    };

                                    // Only insert if it has chat/completion mode or has cost info
                                    if pricing.mode.is_none()
                                        || pricing.mode.as_ref().unwrap() != "image_generation"
                                    {
                                        data.insert(model_name.clone(), pricing);
                                    }
                                }
                            }
                            eprintln!(
                                "Loaded {} model pricing entries from JSON",
                                data.models.len()
                            );
                            stats.record_model_load(data.models.len());
                            stats.record_json_loaded(true);
                        }
                    }
                    Err(e) => {
                        // Only warn once per process
                        static WARNED: std::sync::Once = std::sync::Once::new();
                        WARNED.call_once(|| {
                            eprintln!(
                                "WARNING: Failed to parse model pricing JSON: {}. Using defaults.",
                                e
                            );
                        });
                        stats.record_json_loaded(false);
                    }
                }
            }
            Err(e) => {
                // Only warn once per process
                static WARNED: std::sync::Once = std::sync::Once::new();
                WARNED.call_once(|| {
                    eprintln!(
                        "WARNING: Failed to read model pricing file: {}. Using defaults.",
                        e
                    );
                });
                stats.record_json_loaded(false);
            }
        }
    } else {
        // Only warn once per process
        static WARNED: std::sync::Once = std::sync::Once::new();
        WARNED.call_once(|| {
            eprintln!(
                "WARNING: Model pricing file not found. Using embedded defaults. \
                Run 'DOWNLOAD_MODEL_PRICING=1 cargo build' to download latest pricing."
            );
        });
        stats.record_json_loaded(false);
    }

    data
}

/// Get the global pricing data (loaded once)
pub fn get_pricing_data() -> &'static PricingData {
    static PRICING_DATA: OnceLock<PricingData> = OnceLock::new();
    PRICING_DATA.get_or_init(load_pricing_data)
}

/// Get the global pricing stats
fn get_pricing_stats() -> &'static PricingStats {
    static PRICING_STATS: OnceLock<PricingStats> = OnceLock::new();
    PRICING_STATS.get_or_init(PricingStats::new)
}

/// Get pricing status information
pub fn get_pricing_status() -> serde_json::Value {
    let stats = get_pricing_stats();
    serde_json::json!({
        "json_loaded": stats.json_loaded(),
        "models_loaded": stats.models_loaded.load(Ordering::Relaxed),
        "lookup_failures": stats.lookup_failures.load(Ordering::Relaxed),
    })
}

/// Default pricing for unknown models (fallback)
pub fn default_pricing_for_model(model: &str) -> (f64, f64) {
    let model_lower = model.to_lowercase();

    // GPT-4 class pricing default
    if model_lower.contains("gpt-4") {
        (30.0, 60.0) // $30/$60 per 1M
    }
    // GPT-3.5 class pricing default
    else if model_lower.contains("gpt-3.5") || model_lower.contains("gpt-3") {
        (0.5, 1.5) // $0.50/$1.50 per 1M
    }
    // Claude class default
    else if model_lower.contains("claude") {
        (15.0, 75.0) // $15/$75 per 1M
    }
    // Embeddings
    else if model_lower.contains("embedding") || model_lower.contains("text-embedding") {
        (0.1, 0.0) // $0.10 per 1M input
    }
    // Default
    else {
        (1.0, 2.0) // $1/$2 per 1M
    }
}

/// Default context window for unknown models
pub fn default_context_window_for_model(model: &str) -> u32 {
    let model_lower = model.to_lowercase();

    if model_lower.contains("gpt-4") {
        131072 // 128k
    } else if model_lower.contains("gpt-3.5") {
        16384 // 16k
    } else if model_lower.contains("claude") {
        200000 // 200k
    } else {
        4096 // 4k default
    }
}
