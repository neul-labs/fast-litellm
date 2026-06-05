# Changelog

All notable changes to Fast LiteLLM. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The authoritative copy lives in [`CHANGELOG.md`](https://github.com/neul-labs/fast-litellm/blob/main/CHANGELOG.md) in the repository.

## Unreleased

No unreleased changes.

## 0.1.10 — 2026-05-07

### Fixed

- PyPI publish workflow: moved checksums out of `dist/` to prevent `InvalidDistribution` error.

## 0.1.9 — 2026-05-07

### Fixed

- Publish workflow now pins `PyO3/maturin-action` to `v1.51.0` (the `latest` tag does not exist).

## 0.1.8 — 2026-05-07

### Security

- Updated `aiohttp` to `>=3.13.4` to resolve multiple CVEs (CVE-2026-34513, CVE-2026-34515, CVE-2026-34516, CVE-2026-34517).

### Changed

- Updated Rust dependencies via `cargo update`, including `rand` 0.8.6, `bytes` 1.11.1, `tokio` 1.52.2, and other transitive updates.

## 0.1.7 — 2026-01-09

### Changed

- Updated acceleration of the LiteLLM proxy.
- Documentation improvements.

## 0.1.0 — 2024-12-10

### Added

- Initial release of Fast LiteLLM.
- Advanced routing with multiple strategies (`simple_shuffle`, `least_busy`, `latency_based`, `cost_based`).
- Token counting using tiktoken-rs with model-specific encodings (`cl100k`, `o200k`, `p50k`, `r50k`).
- Thread-safe rate limiting with token bucket and sliding window algorithms.
- Connection pooling with health tracking and lifecycle management.
- Feature flag system for gradual rollout and canary deployments.
- Performance monitoring with real-time metrics.
- Automatic fallback to Python implementations on errors.
- Lock-free data structures using DashMap for concurrent operations.
- Zero-configuration automatic acceleration on import.
- Complete type hints and type stubs.
- Memory pressure benchmarks for high-cardinality workloads.

### Performance (vs production-grade Python with thread-safety)

- 3.2x faster connection pooling (DashMap lock-free).
- 1.6x faster rate limiting (atomic operations).
- 1.5–1.7x faster large text tokenization.
- 42x more memory efficient for high-cardinality rate limiting (1000+ keys).
- 1.2x faster concurrent connection pool operations.
