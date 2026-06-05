# Compatibility

This page summarises the platforms and Python versions Fast LiteLLM supports, plus the most recently verified test matrix.

## Supported Platforms

Prebuilt wheels are published for every supported combination, so Rust is **not** required to install from PyPI.

| Platform | Architectures |
|----------|---------------|
| Linux | x86_64, aarch64 |
| macOS | x86_64, ARM64 (Apple Silicon) |
| Windows | x86_64 |

## Supported Python Versions

| Python | Status |
|--------|--------|
| 3.8 | Supported |
| 3.9 | Supported |
| 3.10 | Supported |
| 3.11 | Supported |
| 3.12 | Supported (recommended) |
| 3.13 | Supported |

## LiteLLM

Fast LiteLLM tracks the **latest stable LiteLLM release**. The most recently verified version is shown in the test matrix below.

If you are pinned to an older LiteLLM, Fast LiteLLM still installs and its standalone APIs (`SimpleRateLimiter`, `SimpleConnectionPool`, `SimpleTokenCounter`, `AdvancedRouter`) keep working. Only the monkey-patching of `litellm.*` is sensitive to LiteLLM's internal API.

## PyO3

| Component | Version |
|-----------|---------|
| PyO3 | 0.24+ |
| Rust toolchain (source builds only) | 1.70+ |

## Latest Verified Matrix

The matrix below is the most recently verified set of versions, taken from the upstream [`COMPATIBILITY.md`](https://github.com/neul-labs/fast-litellm/blob/main/COMPATIBILITY.md) (generated 2026-05-31).

| Platform | Python | Fast LiteLLM | LiteLLM | Rust | Status |
|----------|--------|--------------|---------|------|--------|
| Linux | 3.11.15 | 0.1.10 | 1.83.14 | Available | Pass |

## Reporting Compatibility Issues

If Fast LiteLLM fails to import or apply acceleration on a supported combination, please [open an issue](https://github.com/neul-labs/fast-litellm/issues) including:

- `python --version`
- `uname -a` (or Windows version)
- `pip show fast-litellm litellm`
- Output of `python -c "import fast_litellm; print(fast_litellm.health_check())"`
