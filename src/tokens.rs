/// Token counting functionality using tiktoken-rs
use std::collections::HashMap;
use std::sync::RwLock;
use tiktoken_rs::{cl100k_base, o200k_base, p50k_base, p50k_edit, r50k_base, CoreBPE};

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

        // o200k_base models (GPT-4o, o1 series)
        if model_lower.contains("gpt-4o")
            || model_lower.contains("o1-")
            || model_lower.contains("o1_")
        {
            return "o200k_base";
        }

        // cl100k_base models (GPT-4, GPT-3.5-turbo, embeddings)
        if model_lower.contains("gpt-4")
            || model_lower.contains("gpt-3.5")
            || model_lower.contains("text-embedding")
            || model_lower.contains("claude")
        // Use cl100k for Claude as approximation
        {
            return "cl100k_base";
        }

        // p50k_base models (Codex)
        if model_lower.contains("code-") || model_lower.contains("codex") {
            return "p50k_base";
        }

        // p50k_edit models
        if model_lower.contains("edit") {
            return "p50k_edit";
        }

        // r50k_base models (older GPT-3)
        if model_lower.contains("davinci")
            || model_lower.contains("curie")
            || model_lower.contains("babbage")
            || model_lower.contains("ada")
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
        // Updated pricing (as of 2024)
        let (input_cost_per_1k, output_cost_per_1k) = match model {
            // GPT-4o
            "gpt-4o" | "gpt-4o-2024-08-06" => (0.0025, 0.01),
            "gpt-4o-mini" | "gpt-4o-mini-2024-07-18" => (0.00015, 0.0006),

            // GPT-4 Turbo
            "gpt-4-turbo" | "gpt-4-turbo-2024-04-09" => (0.01, 0.03),
            "gpt-4-turbo-preview" | "gpt-4-0125-preview" => (0.01, 0.03),

            // GPT-4
            "gpt-4" | "gpt-4-0613" => (0.03, 0.06),
            "gpt-4-32k" | "gpt-4-32k-0613" => (0.06, 0.12),

            // GPT-3.5 Turbo
            "gpt-3.5-turbo" | "gpt-3.5-turbo-0125" => (0.0005, 0.0015),
            "gpt-3.5-turbo-instruct" => (0.0015, 0.002),

            // Claude models (Anthropic pricing)
            "claude-3-opus" | "claude-3-opus-20240229" => (0.015, 0.075),
            "claude-3-sonnet" | "claude-3-sonnet-20240229" => (0.003, 0.015),
            "claude-3-haiku" | "claude-3-haiku-20240307" => (0.00025, 0.00125),
            "claude-3-5-sonnet" | "claude-3-5-sonnet-20240620" => (0.003, 0.015),

            // Default
            _ => (0.001, 0.002),
        };

        let input_cost = (input_tokens as f64 / 1000.0) * input_cost_per_1k;
        let output_cost = (output_tokens as f64 / 1000.0) * output_cost_per_1k;

        Ok(input_cost + output_cost)
    }

    pub fn get_model_limits(&self, model: &str) -> HashMap<String, serde_json::Value> {
        let mut limits = HashMap::new();

        let (context_window, max_output) = match model {
            // GPT-4o
            "gpt-4o" | "gpt-4o-2024-08-06" => (128000, 16384),
            "gpt-4o-mini" | "gpt-4o-mini-2024-07-18" => (128000, 16384),

            // GPT-4 Turbo
            "gpt-4-turbo" | "gpt-4-turbo-2024-04-09" => (128000, 4096),
            "gpt-4-turbo-preview" | "gpt-4-0125-preview" => (128000, 4096),

            // GPT-4
            "gpt-4" | "gpt-4-0613" => (8192, 4096),
            "gpt-4-32k" | "gpt-4-32k-0613" => (32768, 4096),

            // GPT-3.5 Turbo
            "gpt-3.5-turbo" | "gpt-3.5-turbo-0125" => (16385, 4096),
            "gpt-3.5-turbo-16k" => (16385, 4096),

            // Claude models
            "claude-3-opus" | "claude-3-opus-20240229" => (200000, 4096),
            "claude-3-sonnet" | "claude-3-sonnet-20240229" => (200000, 4096),
            "claude-3-haiku" | "claude-3-haiku-20240307" => (200000, 4096),
            "claude-3-5-sonnet" | "claude-3-5-sonnet-20240620" => (200000, 8192),

            _ => (4096, 4096),
        };

        limits.insert(
            "context_window".to_string(),
            serde_json::Value::Number(serde_json::Number::from(context_window)),
        );
        limits.insert(
            "max_output_tokens".to_string(),
            serde_json::Value::Number(serde_json::Number::from(max_output)),
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
