/// Token counting functionality using tiktoken-rs
use std::collections::HashMap;
use std::sync::RwLock;
use tiktoken_rs::{cl100k_base, o200k_base, p50k_base, p50k_edit, r50k_base, CoreBPE};

use crate::pricing;

/// Cached encodings for different model families
struct EncodingCache {
    cl100k: Option<CoreBPE>,    // GPT-4, GPT-3.5-turbo, text-embedding-ada-002
    o200k: Option<CoreBPE>,     // GPT-4o, o1 models
    p50k: Option<CoreBPE>,      // Codex models
    p50k_edit: Option<CoreBPE>, // text-davinci-edit
    r50k: Option<CoreBPE>,      // GPT-3 models
}

impl EncodingCache {
    fn new() -> Self {
        Self {
            cl100k: None,
            o200k: None,
            p50k: None,
            p50k_edit: None,
            r50k: None,
        }
    }

    /// Get cached encoding without initializing (for read-only access)
    fn get_cached_encoding(&self, encoding_type: &str) -> Option<&CoreBPE> {
        match encoding_type {
            "cl100k_base" => self.cl100k.as_ref(),
            "o200k_base" => self.o200k.as_ref(),
            "p50k_base" => self.p50k.as_ref(),
            "p50k_edit" => self.p50k_edit.as_ref(),
            "r50k_base" => self.r50k.as_ref(),
            _ => self.cl100k.as_ref(),
        }
    }

    fn get_encoding(&mut self, model: &str) -> Result<&CoreBPE, String> {
        // Map model names to encoding types
        let encoding_type = Self::model_to_encoding(model);

        match encoding_type {
            "cl100k_base" => {
                if self.cl100k.is_none() {
                    self.cl100k = Some(
                        cl100k_base().map_err(|e| format!("Failed to load cl100k_base: {}", e))?,
                    );
                }
                Ok(self.cl100k.as_ref().unwrap())
            }
            "o200k_base" => {
                if self.o200k.is_none() {
                    self.o200k = Some(
                        o200k_base().map_err(|e| format!("Failed to load o200k_base: {}", e))?,
                    );
                }
                Ok(self.o200k.as_ref().unwrap())
            }
            "p50k_base" => {
                if self.p50k.is_none() {
                    self.p50k =
                        Some(p50k_base().map_err(|e| format!("Failed to load p50k_base: {}", e))?);
                }
                Ok(self.p50k.as_ref().unwrap())
            }
            "p50k_edit" => {
                if self.p50k_edit.is_none() {
                    self.p50k_edit =
                        Some(p50k_edit().map_err(|e| format!("Failed to load p50k_edit: {}", e))?);
                }
                Ok(self.p50k_edit.as_ref().unwrap())
            }
            "r50k_base" => {
                if self.r50k.is_none() {
                    self.r50k =
                        Some(r50k_base().map_err(|e| format!("Failed to load r50k_base: {}", e))?);
                }
                Ok(self.r50k.as_ref().unwrap())
            }
            _ => {
                // Default to cl100k_base
                if self.cl100k.is_none() {
                    self.cl100k = Some(
                        cl100k_base().map_err(|e| format!("Failed to load cl100k_base: {}", e))?,
                    );
                }
                Ok(self.cl100k.as_ref().unwrap())
            }
        }
    }

    fn model_to_encoding(model: &str) -> &'static str {
        let model_lower = model.to_lowercase();

        // o200k_base models (GPT-4o, o1 series) - use starts_with for safety
        if model_lower.starts_with("gpt-4o")
            || model_lower.starts_with("o1-")
            || model_lower.starts_with("o1-preview")
            || model_lower.starts_with("o1-mini")
        {
            return "o200k_base";
        }

        // cl100k_base models (GPT-4, GPT-3.5-turbo, embeddings) - use starts_with
        if model_lower.starts_with("gpt-4")
            || model_lower.starts_with("gpt-3.5-turbo")
            || model_lower.starts_with("text-embedding")
            || model_lower.starts_with("claude-")
        {
            return "cl100k_base";
        }

        // p50k_base models (Codex) - use starts_with
        if model_lower.starts_with("code-") || model_lower.starts_with("codex") {
            return "p50k_base";
        }

        // p50k_edit models - use starts_with
        if model_lower.starts_with("text-davinci-edit") {
            return "p50k_edit";
        }

        // r50k_base models (older GPT-3) - use starts_with
        if model_lower.starts_with("davinci")
            || model_lower.starts_with("curie")
            || model_lower.starts_with("babbage")
            || model_lower.starts_with("ada")
        {
            return "r50k_base";
        }

        // Default to cl100k_base
        "cl100k_base"
    }
}

pub struct TokenCounter {
    cache: RwLock<EncodingCache>,
}

impl Default for TokenCounter {
    fn default() -> Self {
        Self::new()
    }
}

impl TokenCounter {
    pub fn new() -> Self {
        Self {
            cache: RwLock::new(EncodingCache::new()),
        }
    }

    pub fn count_tokens(&self, text: &str, model: Option<&str>) -> Result<usize, String> {
        let model = model.unwrap_or("gpt-3.5-turbo");
        let encoding_type = EncodingCache::model_to_encoding(model);

        // Try read lock first (fast path)
        {
            let cache = self
                .cache
                .read()
                .map_err(|e| format!("Lock error: {}", e))?;
            if let Some(encoding) = cache.get_cached_encoding(encoding_type) {
                let tokens = encoding.encode_with_special_tokens(text);
                return Ok(tokens.len());
            }
        }

        // Need to initialize - use write lock
        let mut cache = self
            .cache
            .write()
            .map_err(|e| format!("Lock error: {}", e))?;
        let encoding = cache.get_encoding(model)?;
        let tokens = encoding.encode_with_special_tokens(text);
        Ok(tokens.len())
    }

    pub fn count_tokens_batch(
        &self,
        texts: &[String],
        model: Option<&str>,
    ) -> Result<Vec<usize>, String> {
        let model = model.unwrap_or("gpt-3.5-turbo");
        let encoding_type = EncodingCache::model_to_encoding(model);

        // Try read lock first (fast path)
        {
            let cache = self
                .cache
                .read()
                .map_err(|e| format!("Lock error: {}", e))?;
            if let Some(encoding) = cache.get_cached_encoding(encoding_type) {
                let results: Vec<usize> = texts
                    .iter()
                    .map(|text| encoding.encode_with_special_tokens(text).len())
                    .collect();
                return Ok(results);
            }
        }

        // Need to initialize - use write lock
        let mut cache = self
            .cache
            .write()
            .map_err(|e| format!("Lock error: {}", e))?;
        let encoding = cache.get_encoding(model)?;

        let results: Vec<usize> = texts
            .iter()
            .map(|text| encoding.encode_with_special_tokens(text).len())
            .collect();

        Ok(results)
    }

    pub fn estimate_cost(
        &self,
        input_tokens: usize,
        output_tokens: usize,
        model: &str,
    ) -> Result<f64, String> {
        // Try to get pricing from loaded data first
        let pricing = pricing::get_pricing_data();

        if let (Some(input_cost), Some(output_cost)) = (
            pricing.get_input_cost_per_1m(model),
            pricing.get_output_cost_per_1m(model),
        ) {
            let input_cost_per_1k = input_cost / 1000.0;
            let output_cost_per_1k = output_cost / 1000.0;

            let input_cost = (input_tokens as f64 / 1000.0) * input_cost_per_1k;
            let output_cost = (output_tokens as f64 / 1000.0) * output_cost_per_1k;
            return Ok(input_cost + output_cost);
        }

        // Fall back to default pricing for unknown models
        let (input_cost_per_1k, output_cost_per_1k) = pricing::default_pricing_for_model(model);

        // Log warning for unknown models (once per model)
        static WARNED: std::sync::Once = std::sync::Once::new();
        WARNED.call_once(|| {
            eprintln!(
                "WARNING: Unknown model '{}' - using default cost (input: ${}/1M, output: ${}/1M). \
                Update model pricing with: DOWNLOAD_MODEL_PRICING=1 cargo build",
                model,
                input_cost_per_1k as u64,
                output_cost_per_1k as u64
            );
        });

        let input_cost = (input_tokens as f64 / 1000.0) * input_cost_per_1k;
        let output_cost = (output_tokens as f64 / 1000.0) * output_cost_per_1k;

        Ok(input_cost + output_cost)
    }

    pub fn get_model_limits(&self, model: &str) -> HashMap<String, serde_json::Value> {
        let mut limits = HashMap::new();

        // Try to get limits from loaded pricing data first
        let pricing = pricing::get_pricing_data();

        if let Some(context_window) = pricing.get_context_window(model) {
            let max_output = pricing.get_max_output(model).unwrap_or(4096);

            limits.insert(
                "context_window".to_string(),
                serde_json::Value::Number(serde_json::Number::from(context_window)),
            );
            limits.insert(
                "max_output_tokens".to_string(),
                serde_json::Value::Number(serde_json::Number::from(max_output)),
            );
            return limits;
        }

        // Fall back to default limits
        let context_window = pricing::default_context_window_for_model(model);
        limits.insert(
            "context_window".to_string(),
            serde_json::Value::Number(serde_json::Number::from(context_window)),
        );
        limits.insert(
            "max_output_tokens".to_string(),
            serde_json::Value::Number(serde_json::Number::from(4096)),
        );

        limits
    }

    pub fn validate_input(&self, text: &str, model: &str) -> Result<bool, String> {
        let token_count = self.count_tokens(text, Some(model))?;
        let limits = self.get_model_limits(model);

        if let Some(context_window) = limits.get("context_window").and_then(|v| v.as_u64()) {
            if token_count > context_window as usize {
                return Err(format!(
                    "Input exceeds model context window: {} tokens > {} limit",
                    token_count, context_window
                ));
            }
        }

        Ok(true)
    }
}

// Global token counter instance
lazy_static::lazy_static! {
    static ref TOKEN_COUNTER: TokenCounter = TokenCounter::new();
}

pub fn count_tokens(text: &str, model: Option<&str>) -> Result<usize, String> {
    TOKEN_COUNTER.count_tokens(text, model)
}

pub fn count_tokens_batch(texts: &[String], model: Option<&str>) -> Result<Vec<usize>, String> {
    TOKEN_COUNTER.count_tokens_batch(texts, model)
}

pub fn estimate_cost(
    input_tokens: usize,
    output_tokens: usize,
    model: &str,
) -> Result<f64, String> {
    TOKEN_COUNTER.estimate_cost(input_tokens, output_tokens, model)
}

pub fn get_model_limits(model: &str) -> HashMap<String, serde_json::Value> {
    TOKEN_COUNTER.get_model_limits(model)
}

pub fn validate_input(text: &str, model: &str) -> Result<bool, String> {
    TOKEN_COUNTER.validate_input(text, model)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_count_tokens_gpt4() {
        let counter = TokenCounter::new();
        let result = counter.count_tokens("Hello, world!", Some("gpt-4"));
        assert!(result.is_ok());
        let tokens = result.unwrap();
        assert!(tokens > 0);
        assert!(tokens < 10); // "Hello, world!" should be around 4 tokens
    }

    #[test]
    fn test_count_tokens_batch() {
        let counter = TokenCounter::new();
        let texts = vec![
            "Hello".to_string(),
            "World".to_string(),
            "Hello, world!".to_string(),
        ];
        let result = counter.count_tokens_batch(&texts, Some("gpt-4"));
        assert!(result.is_ok());
        let counts = result.unwrap();
        assert_eq!(counts.len(), 3);
    }

    #[test]
    fn test_model_encoding_selection() {
        // Test that different models use appropriate encodings
        assert_eq!(EncodingCache::model_to_encoding("gpt-4o"), "o200k_base");
        assert_eq!(EncodingCache::model_to_encoding("gpt-4"), "cl100k_base");
        assert_eq!(
            EncodingCache::model_to_encoding("gpt-3.5-turbo"),
            "cl100k_base"
        );
        assert_eq!(
            EncodingCache::model_to_encoding("code-davinci-002"),
            "p50k_base"
        );
    }
}
