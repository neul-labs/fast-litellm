# Troubleshooting

Common issues and resolutions for Fast LiteLLM.

## Installation Issues

### `ModuleNotFoundError: fast_litellm._rust`

**Cause:** The Rust extension was not compiled or installed correctly.

**Solutions:**

1. Ensure the Rust toolchain is installed:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. Rebuild with maturin:
   ```bash
   uv run maturin develop
   ```

3. Verify the extension loads:
   ```bash
   uv run python -c "import fast_litellm._rust; print('OK')"
   ```

### `maturin develop` Fails with Compilation Errors

1. Update the Rust toolchain:
   ```bash
   rustup update stable
   ```

2. Clear the build cache and rebuild:
   ```bash
   cargo clean
   uv run maturin develop
   ```

3. Confirm Python 3.8+ is installed:
   ```bash
   python --version
   ```

### `ImportError: cannot import name X from fast_litellm`

**Cause:** Version mismatch or partial installation.

**Solution:** Reinstall the package:

```bash
uv run maturin develop --release
```

## Runtime Issues

### Rust Acceleration Not Being Applied

**Symptom:** Performance is similar to vanilla LiteLLM.

**Diagnosis:**

```python
import fast_litellm
print(fast_litellm.health_check())  # Expect rust_available: True
```

**Solutions:**

1. Import `fast_litellm` **before** `litellm`:
   ```python
   import fast_litellm  # must be first
   import litellm
   ```

2. Check feature flags:
   ```python
   from fast_litellm import get_feature_status
   print(get_feature_status())
   ```

3. Verify patch status:
   ```python
   from fast_litellm import get_patch_status
   print(get_patch_status())
   ```

### Feature Auto-Disabled Due to Errors

**Symptom:** Logs show "Feature disabled due to errors" or performance reverts to Python.

**Cause:** After 10 errors (default threshold), the circuit breaker disables the feature.

**Solution:** Reset error counts:

```python
from fast_litellm import reset_errors
reset_errors()                  # reset all features
reset_errors("rust_routing")    # reset a specific feature
```

### Slower Than Python for Small Inputs

**Cause:** FFI overhead dominates for small operations.

**Expected behavior.** Rust acceleration provides clear benefits for:

- Large text tokenization (1000+ characters)
- High-concurrency scenarios
- Connection pooling with many endpoints
- Rate limiting with high cardinality (many unique keys)

For tiny inputs (under ~100 tokens, simple routing with Python dicts), the FFI round-trip can exceed the Rust speedup. See [Benchmarks](../benchmarks.md) for measured break-even points.

### LiteLLM Import Fails on Python 3.9

**Symptom:** `TypeError` when importing LiteLLM on Python 3.9.

**Cause:** Some LiteLLM versions use Python 3.10+ syntax such as `str | List[str]`.

**Solutions:**

1. Upgrade to Python 3.10+.
2. Pin to an older LiteLLM release that still supports 3.9.
3. Fast LiteLLM swallows this error during patch application so its standalone APIs (`SimpleRateLimiter`, `SimpleConnectionPool`, etc.) keep working without LiteLLM.

## Full Health Snapshot

When opening an issue, run:

```python
import fast_litellm

print(f"Version: {fast_litellm.__version__}")
print(f"Rust available: {fast_litellm.RUST_ACCELERATION_AVAILABLE}")
print(fast_litellm.health_check())
print(fast_litellm.get_patch_status())
print(fast_litellm.get_feature_status())
print(fast_litellm.get_performance_stats())
```

## Getting Help

File issues at [github.com/neul-labs/fast-litellm/issues](https://github.com/neul-labs/fast-litellm/issues). Include:

- Python version (`python --version`)
- Platform (`uname -a` or Windows version)
- Fast LiteLLM version (`fast_litellm.__version__`)
- Output of `fast_litellm.health_check()`
- Minimal reproduction steps
