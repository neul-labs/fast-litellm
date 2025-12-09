use dashmap::DashMap;
/// Connection pooling functionality
use std::collections::HashMap;
use std::sync::atomic::{AtomicU32, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone)]
pub struct Connection {
    pub id: String,
    pub endpoint: String,
    pub created_at: u64,
    pub last_used: u64,
    pub request_count: u32,
    pub is_healthy: bool,
}

impl Connection {
    pub fn new(id: String, endpoint: String) -> Self {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as u64;

        Self {
            id,
            endpoint,
            created_at: now,
            last_used: now,
            request_count: 0,
            is_healthy: true,
        }
    }

    pub fn use_connection(&mut self) {
        self.last_used = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as u64;
        self.request_count += 1;
    }

    pub fn is_expired(&self, max_age_ms: u64) -> bool {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as u64;

        now - self.created_at > max_age_ms
    }

    pub fn is_idle(&self, max_idle_ms: u64) -> bool {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as u64;

        now - self.last_used > max_idle_ms
    }
}

pub struct ConnectionPool {
    connections: DashMap<String, Connection>,
    available_connections: DashMap<String, Vec<String>>, // endpoint -> connection_ids
    active_connections: AtomicU32,
    total_connections: AtomicU32,
    max_connections_per_endpoint: u32,
    max_total_connections: u32,
    connection_timeout_ms: u64,
    max_idle_time_ms: u64,
}

impl Default for ConnectionPool {
    fn default() -> Self {
        Self::new()
    }
}

impl ConnectionPool {
    pub fn new() -> Self {
        Self {
            connections: DashMap::new(),
            available_connections: DashMap::new(),
            active_connections: AtomicU32::new(0),
            total_connections: AtomicU32::new(0),
            max_connections_per_endpoint: 10,
            max_total_connections: 100,
            connection_timeout_ms: 30000, // 30 seconds
            max_idle_time_ms: 300000,     // 5 minutes
        }
    }

    pub fn get_connection(&self, endpoint: &str) -> Option<String> {
        // Try to get an available connection
        if let Some(mut available) = self.available_connections.get_mut(endpoint) {
            if let Some(connection_id) = available.pop() {
                if let Some(mut conn) = self.connections.get_mut(&connection_id) {
                    conn.use_connection();
                    self.active_connections.fetch_add(1, Ordering::Relaxed);
                    return Some(connection_id);
                }
            }
        }

        // Create new connection if within limits
        if self.can_create_connection(endpoint) {
            let connection_id = self.create_connection(endpoint);
            if let Some(mut conn) = self.connections.get_mut(&connection_id) {
                conn.use_connection();
                self.active_connections.fetch_add(1, Ordering::Relaxed);
                return Some(connection_id);
            }
        }

        None
    }

    pub fn return_connection(&self, connection_id: &str) {
        if let Some(connection) = self.connections.get(connection_id) {
            let endpoint = connection.endpoint.clone();

            // Return to available pool
            let mut available = self.available_connections.entry(endpoint).or_default();
            available.push(connection_id.to_string());

            self.active_connections.fetch_sub(1, Ordering::Relaxed);
        }
    }

    pub fn remove_connection(&self, connection_id: &str) {
        if let Some((_, connection)) = self.connections.remove(connection_id) {
            // Remove from available connections
            if let Some(mut available) = self.available_connections.get_mut(&connection.endpoint) {
                available.retain(|id| id != connection_id);
            }

            self.total_connections.fetch_sub(1, Ordering::Relaxed);
        }
    }

    pub fn health_check_connection(&self, connection_id: &str) -> bool {
        // Placeholder for actual health check
        // In real implementation, would make a health check request
        if let Some(mut connection) = self.connections.get_mut(connection_id) {
            connection.is_healthy = true; // Assume healthy for now
            connection.is_healthy
        } else {
            false
        }
    }

    pub fn cleanup_expired_connections(&self) {
        let expired_connections: Vec<String> = self
            .connections
            .iter()
            .filter_map(|entry| {
                let connection = entry.value();
                if connection.is_expired(self.connection_timeout_ms)
                    || connection.is_idle(self.max_idle_time_ms)
                {
                    Some(entry.key().clone())
                } else {
                    None
                }
            })
            .collect();

        for connection_id in expired_connections {
            self.remove_connection(&connection_id);
        }
    }

    pub fn get_stats(&self) -> HashMap<String, serde_json::Value> {
        let mut stats = HashMap::new();

        stats.insert(
            "active_connections".to_string(),
            serde_json::Value::Number(serde_json::Number::from(
                self.active_connections.load(Ordering::Relaxed),
            )),
        );
        stats.insert(
            "total_connections".to_string(),
            serde_json::Value::Number(serde_json::Number::from(
                self.total_connections.load(Ordering::Relaxed),
            )),
        );
        stats.insert(
            "max_total_connections".to_string(),
            serde_json::Value::Number(serde_json::Number::from(self.max_total_connections)),
        );

        // Per-endpoint stats
        let mut endpoint_stats = HashMap::new();
        for entry in self.available_connections.iter() {
            let endpoint = entry.key();
            let available_count = entry.value().len();

            endpoint_stats.insert(
                endpoint.clone(),
                serde_json::json!({
                    "available_connections": available_count,
                    "max_connections": self.max_connections_per_endpoint
                }),
            );
        }

        stats.insert(
            "endpoints".to_string(),
            serde_json::Value::Object(endpoint_stats.into_iter().collect()),
        );

        stats
    }

    fn can_create_connection(&self, endpoint: &str) -> bool {
        let total = self.total_connections.load(Ordering::Relaxed);
        if total >= self.max_total_connections {
            return false;
        }

        let endpoint_count = self
            .available_connections
            .get(endpoint)
            .map(|v| v.len())
            .unwrap_or(0) as u32;

        endpoint_count < self.max_connections_per_endpoint
    }

    fn create_connection(&self, endpoint: &str) -> String {
        let connection_id = format!(
            "conn_{}_{}",
            endpoint.replace("://", "_").replace("/", "_"),
            self.total_connections.load(Ordering::Relaxed)
        );

        let connection = Connection::new(connection_id.clone(), endpoint.to_string());
        self.connections.insert(connection_id.clone(), connection);
        self.total_connections.fetch_add(1, Ordering::Relaxed);

        connection_id
    }
}

// Global connection pool
lazy_static::lazy_static! {
    static ref CONNECTION_POOL: ConnectionPool = ConnectionPool::new();
}

pub fn get_connection(endpoint: &str) -> Option<String> {
    CONNECTION_POOL.get_connection(endpoint)
}

pub fn return_connection(connection_id: &str) {
    CONNECTION_POOL.return_connection(connection_id);
}

pub fn remove_connection(connection_id: &str) {
    CONNECTION_POOL.remove_connection(connection_id);
}

pub fn health_check_connection(connection_id: &str) -> bool {
    CONNECTION_POOL.health_check_connection(connection_id)
}

pub fn cleanup_expired_connections() {
    CONNECTION_POOL.cleanup_expired_connections();
}

pub fn get_connection_pool_stats() -> HashMap<String, serde_json::Value> {
    CONNECTION_POOL.get_stats()
}
