# Architecture Guide

Technical implementation details of LiteLLM Rust acceleration.

## Overview

LiteLLM Rust acceleration provides seamless performance improvements while maintaining full compatibility with the original Python implementation through a layered architecture.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ User Application                                            │
│ import litellm_rust                                         │
│ import litellm                                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│ LiteLLM Python Package (Monkeypatched)                     │
│ ├── litellm.router.Router                                  │
│ ├── litellm.utils.token_counter                            │
│ ├── litellm.SimpleRateLimiter                              │
│ └── litellm.SimpleConnectionPool                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│ Python Integration Layer (litellm_rust)                    │
│ ├── Enhanced Monkeypatching                                │
│ ├── Feature Flag Management                                │
│ ├── Performance Monitoring                                 │
│ └── Automatic Fallback                                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│ Rust Components (PyO3 Extensions)                          │
│ ├── litellm-core        (Advanced Routing)                 │
│ ├── litellm-token       (Token Counting)                   │
│ ├── litellm-rate-limiter (Rate Limiting)                   │
│ └── litellm-connection-pool (Connection Management)        │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Enhanced Monkeypatching System

**PerformanceWrapper**: Intelligent function wrapping with metrics
**AsyncPerformanceWrapper**: Async-compatible version
**HybridClass**: Class-level patching with feature flag integration

### 2. Feature Flag Management

- **Gradual Rollout**: Percentage-based feature deployment
- **Canary Testing**: Small-scale feature validation
- **Shadow Mode**: Background execution without affecting responses
- **Automatic Degradation**: Error-based feature disabling

### 3. Performance Monitoring

- **Real-time Metrics**: Latency, throughput, error rates
- **Statistical Analysis**: P50, P95, P99 percentiles
- **Alert System**: Configurable thresholds and notifications
- **Optimization Engine**: Automated recommendations

### 4. Rust Acceleration Components

#### litellm-core (Advanced Routing)
- **Lock-free routing**: DashMap-based deployment storage
- **Multiple strategies**: LeastBusy, LatencyBased, CostBased
- **Health monitoring**: Automatic unhealthy deployment detection

#### litellm-token (Token Counting)
- **tiktoken-rs integration**: Native Rust tokenization
- **Batch processing**: Multiple texts with single encoding
- **Smart caching**: LRU eviction with configurable limits

#### litellm-rate-limiter (Rate Limiting)
- **Token bucket algorithm**: Industry-standard implementation
- **High-precision timing**: Nanosecond accuracy
- **Concurrent access**: Lock-free operations

#### litellm-connection-pool (Connection Management)
- **HTTP/2 multiplexing**: Multiple requests per connection
- **Intelligent reuse**: Keep-alive management
- **Load balancing**: Even distribution across connections

## Key Design Principles

1. **Zero-Copy Operations**: Minimize data transfer overhead
2. **Lock-Free Concurrency**: DashMap and atomic operations
3. **Graceful Degradation**: Automatic Python fallback
4. **Production Safety**: Comprehensive monitoring and error handling
5. **Performance Transparency**: Detailed metrics and recommendations

## Data Flow

### Request Processing
```
Request → Feature Check → Rust Implementation → Metrics
    ↓         ↓               ↓                ↓
Fallback ← Disabled     Error Occurred    Performance
    ↓                        ↓              Recording
Python Implementation → Success/Failure
```

### Feature Flag Decision
```
Request ID → Hash → Percentage → Enable/Disable
              ↓
    Consistent Rollout
```

## Performance Characteristics

| Component | Memory Usage | Latency Improvement | Concurrency |
|-----------|--------------|-------------------|-------------|
| Token Counting | ~10MB + cache | 5-20x | Lock-free |
| Request Routing | ~20MB | 3-8x | DashMap |
| Rate Limiting | ~5MB | 4-12x | Atomic ops |
| Connection Pool | ~15MB | 2-5x | Async |

## Thread Safety

- **Rust ownership model**: Prevents data races at compile time
- **Arc**: Shared ownership for thread-safe data structures
- **DashMap**: Lock-free concurrent HashMap
- **AtomicU64**: Lock-free counters and metrics
- **Async compatibility**: Full Tokio integration

## Error Handling Strategy

### Hierarchical Fallback
1. **Rust implementation** (primary path)
2. **Python implementation** (automatic fallback)
3. **Error propagation** (if both implementations fail)

### Error Categories
- **ImportError**: Rust unavailable → Use Python
- **RuntimeError**: Rust failure → Fallback to Python
- **ConfigError**: Invalid settings → Use safe defaults
- **ResourceError**: Limits exceeded → Graceful degradation

## Deployment Architecture

### Production Deployment Flow
1. **Canary deployment** (5-10% traffic)
2. **Metrics monitoring** (error rates, latency)
3. **Gradual rollout** (25% → 50% → 100%)
4. **Automatic rollback** (on threshold breaches)

### Configuration Management
- **Environment variables**: Simple feature control
- **JSON configuration**: Advanced settings and thresholds
- **Runtime updates**: Dynamic feature flag changes
- **External monitoring**: Metrics export for observability

This architecture ensures high performance while maintaining reliability, observability, and ease of deployment in production environments.