use dashmap::DashMap;
/// Rate limiting functionality
use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone)]
pub struct RateLimitConfig {
    pub requests_per_second: u64,
    pub requests_per_minute: u64,
    pub requests_per_hour: u64,
    pub burst_size: u64,
}

impl Default for RateLimitConfig {
    fn default() -> Self {
        Self {
            requests_per_second: 10,
            requests_per_minute: 600,
            requests_per_hour: 10000,
            burst_size: 20,
        }
    }
}

#[derive(Debug)]
pub struct TokenBucket {
    tokens: AtomicU64,
    last_refill: AtomicU64,
    capacity: u64,
    refill_rate: u64, // tokens per second
}

impl TokenBucket {
    pub fn new(capacity: u64, refill_rate: u64) -> Self {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as u64;

        Self {
            tokens: AtomicU64::new(capacity),
            last_refill: AtomicU64::new(now),
            capacity,
            refill_rate,
        }
    }

    pub fn try_consume(&self, tokens: u64) -> bool {
        self.refill();

        let current_tokens = self.tokens.load(Ordering::Relaxed);
        if current_tokens >= tokens {
            let new_tokens = current_tokens - tokens;
            self.tokens
                .compare_exchange_weak(
                    current_tokens,
                    new_tokens,
                    Ordering::Relaxed,
                    Ordering::Relaxed,
                )
                .is_ok()
        } else {
            false
        }
    }

    fn refill(&self) {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as u64;

        let last_refill = self.last_refill.load(Ordering::Relaxed);
        let time_passed = now - last_refill;

        if time_passed >= 1000 {
            // At least 1 second has passed
            let tokens_to_add = (time_passed / 1000) * self.refill_rate;

            let current_tokens = self.tokens.load(Ordering::Relaxed);
            let new_tokens = std::cmp::min(current_tokens + tokens_to_add, self.capacity);

            if self
                .tokens
                .compare_exchange_weak(
                    current_tokens,
                    new_tokens,
                    Ordering::Relaxed,
                    Ordering::Relaxed,
                )
                .is_ok()
            {
                self.last_refill.store(now, Ordering::Relaxed);
            }
        }
    }

    pub fn available_tokens(&self) -> u64 {
        self.refill();
        self.tokens.load(Ordering::Relaxed)
    }
}

#[derive(Debug)]
pub struct SlidingWindowCounter {
    windows: DashMap<u64, AtomicU64>, // timestamp_window -> count
    window_size_ms: u64,
    limit: u64,
}

impl SlidingWindowCounter {
    pub fn new(window_size_ms: u64, limit: u64) -> Self {
        Self {
            windows: DashMap::new(),
            window_size_ms,
            limit,
        }
    }

    pub fn try_increment(&self) -> bool {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as u64;

        self.cleanup_old_windows(now);

        let current_window = now / self.window_size_ms;
        let current_count = self.get_current_count(current_window);

        if current_count < self.limit {
            let window_counter = self
                .windows
                .entry(current_window)
                .or_insert_with(|| AtomicU64::new(0));
            window_counter.fetch_add(1, Ordering::Relaxed);
            true
        } else {
            false
        }
    }

    fn get_current_count(&self, current_window: u64) -> u64 {
        let mut total = 0;

        // Count requests in current and previous windows for smooth sliding
        for i in 0..=1 {
            if let Some(window) = self.windows.get(&(current_window - i)) {
                total += window.load(Ordering::Relaxed);
            }
        }

        total
    }

    fn cleanup_old_windows(&self, now: u64) {
        let current_window = now / self.window_size_ms;
        let cutoff_window = current_window.saturating_sub(2);

        self.windows.retain(|&window, _| window > cutoff_window);
    }

    pub fn get_remaining(&self) -> u64 {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as u64;

        let current_window = now / self.window_size_ms;
        let current_count = self.get_current_count(current_window);

        self.limit.saturating_sub(current_count)
    }
}

pub struct RateLimiter {
    token_buckets: DashMap<String, TokenBucket>,
    minute_counters: DashMap<String, SlidingWindowCounter>,
    hour_counters: DashMap<String, SlidingWindowCounter>,
    configs: DashMap<String, RateLimitConfig>,
}

impl Default for RateLimiter {
    fn default() -> Self {
        Self::new()
    }
}

impl RateLimiter {
    pub fn new() -> Self {
        Self {
            token_buckets: DashMap::new(),
            minute_counters: DashMap::new(),
            hour_counters: DashMap::new(),
            configs: DashMap::new(),
        }
    }

    pub fn set_config(&self, key: &str, config: RateLimitConfig) {
        // Create token bucket for burst control
        let bucket = TokenBucket::new(config.burst_size, config.requests_per_second);
        self.token_buckets.insert(key.to_string(), bucket);

        // Create sliding window counters
        let minute_counter = SlidingWindowCounter::new(60000, config.requests_per_minute); // 1 minute
        let hour_counter = SlidingWindowCounter::new(3600000, config.requests_per_hour); // 1 hour

        self.minute_counters.insert(key.to_string(), minute_counter);
        self.hour_counters.insert(key.to_string(), hour_counter);
        self.configs.insert(key.to_string(), config);
    }

    pub fn check_rate_limit(&self, key: &str) -> RateLimitResult {
        // Ensure config exists
        if !self.configs.contains_key(key) {
            self.set_config(key, RateLimitConfig::default());
        }

        // Check token bucket (for burst and per-second limits)
        if let Some(bucket) = self.token_buckets.get(key) {
            if !bucket.try_consume(1) {
                return RateLimitResult {
                    allowed: false,
                    reason: "Rate limit exceeded (requests per second)".to_string(),
                    retry_after_ms: Some(1000),
                    remaining_requests: bucket.available_tokens(),
                };
            }
        }

        // Check minute limit
        if let Some(minute_counter) = self.minute_counters.get(key) {
            if !minute_counter.try_increment() {
                return RateLimitResult {
                    allowed: false,
                    reason: "Rate limit exceeded (requests per minute)".to_string(),
                    retry_after_ms: Some(60000),
                    remaining_requests: minute_counter.get_remaining(),
                };
            }
        }

        // Check hour limit
        if let Some(hour_counter) = self.hour_counters.get(key) {
            if !hour_counter.try_increment() {
                return RateLimitResult {
                    allowed: false,
                    reason: "Rate limit exceeded (requests per hour)".to_string(),
                    retry_after_ms: Some(3600000),
                    remaining_requests: hour_counter.get_remaining(),
                };
            }
        }

        RateLimitResult {
            allowed: true,
            reason: "Request allowed".to_string(),
            retry_after_ms: None,
            remaining_requests: self.get_remaining_requests(key),
        }
    }

    pub fn get_remaining_requests(&self, key: &str) -> u64 {
        let bucket_remaining = self
            .token_buckets
            .get(key)
            .map(|b| b.available_tokens())
            .unwrap_or(0);

        let minute_remaining = self
            .minute_counters
            .get(key)
            .map(|c| c.get_remaining())
            .unwrap_or(0);

        let hour_remaining = self
            .hour_counters
            .get(key)
            .map(|c| c.get_remaining())
            .unwrap_or(0);

        std::cmp::min(
            std::cmp::min(bucket_remaining, minute_remaining),
            hour_remaining,
        )
    }

    pub fn get_stats(&self) -> HashMap<String, serde_json::Value> {
        let mut stats = HashMap::new();

        for entry in self.configs.iter() {
            let key = entry.key();
            let config = entry.value();

            let remaining = self.get_remaining_requests(key);

            let key_stats = serde_json::json!({
                "config": {
                    "requests_per_second": config.requests_per_second,
                    "requests_per_minute": config.requests_per_minute,
                    "requests_per_hour": config.requests_per_hour,
                    "burst_size": config.burst_size
                },
                "remaining_requests": remaining,
                "bucket_tokens": self.token_buckets.get(key).map(|b| b.available_tokens()).unwrap_or(0),
                "minute_remaining": self.minute_counters.get(key).map(|c| c.get_remaining()).unwrap_or(0),
                "hour_remaining": self.hour_counters.get(key).map(|c| c.get_remaining()).unwrap_or(0)
            });

            stats.insert(key.clone(), key_stats);
        }

        stats
    }
}

#[derive(Debug, Clone)]
pub struct RateLimitResult {
    pub allowed: bool,
    pub reason: String,
    pub retry_after_ms: Option<u64>,
    pub remaining_requests: u64,
}

// Global rate limiter
lazy_static::lazy_static! {
    static ref RATE_LIMITER: RateLimiter = RateLimiter::new();
}

pub fn check_rate_limit(key: &str) -> RateLimitResult {
    RATE_LIMITER.check_rate_limit(key)
}

pub fn set_rate_limit_config(key: &str, config: RateLimitConfig) {
    RATE_LIMITER.set_config(key, config);
}

pub fn get_remaining_requests(key: &str) -> u64 {
    RATE_LIMITER.get_remaining_requests(key)
}

pub fn get_rate_limit_stats() -> HashMap<String, serde_json::Value> {
    RATE_LIMITER.get_stats()
}
