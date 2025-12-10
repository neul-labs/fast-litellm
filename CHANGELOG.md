# Changelog

All notable changes to Fast LiteLLM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-12-10

### Added
- Initial release of Fast LiteLLM - high-performance Rust acceleration for LiteLLM
- Advanced routing with multiple strategies (simple_shuffle, least_busy, latency_based, cost_based)
- Token counting using tiktoken-rs with model-specific encodings (cl100k, o200k, p50k, r50k)
- Thread-safe rate limiting with token bucket and sliding window algorithms
- Connection pooling with health tracking and lifecycle management
- Feature flag system for gradual rollout and canary deployments
- Comprehensive performance monitoring with real-time metrics
- Automatic fallback to Python implementations on errors
- Lock-free data structures using DashMap for concurrent operations
- Zero-configuration automatic acceleration on import
- Complete type hints and type stubs
- Comprehensive documentation and examples
- Memory pressure benchmarks for high-cardinality workloads

### Performance (vs production-grade Python with thread-safety)
- **3.2x faster** connection pooling (DashMap lock-free)
- **1.6x faster** rate limiting (atomic operations)
- **1.5-1.7x faster** large text tokenization
- **42x more memory efficient** for high-cardinality rate limiting (1000+ keys)
- **1.2x faster** concurrent connection pool operations