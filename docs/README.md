# LiteLLM Rust Documentation

Comprehensive documentation for LiteLLM Rust acceleration.

## Quick Links

- [🏠 Main README](../README.md) - Project overview and quick start
- [📚 API Reference](api.md) - Complete API documentation
- [🏗️ Architecture Guide](architecture.md) - Technical implementation details
- [🎛️ Feature Flags](feature-flags.md) - Configuration and rollout strategies
- [📊 Performance Monitoring](monitoring.md) - Metrics and optimization
- [⚙️ Configuration](configuration.md) - Environment and JSON configuration
- [🤝 Contributing](contributing.md) - Development guidelines

## Documentation Structure

### For Users

- **[API Reference](api.md)**: Complete function and class documentation
- **[Configuration](configuration.md)**: Environment variables and JSON config
- **[Feature Flags](feature-flags.md)**: Gradual rollout and deployment strategies
- **[Performance Monitoring](monitoring.md)**: Metrics, alerts, and optimization

### For Developers

- **[Architecture Guide](architecture.md)**: Technical implementation details
- **[Contributing](contributing.md)**: Development setup and guidelines

## Getting Started

1. **Installation**: See [main README](../README.md#quick-start)
2. **Basic Usage**: Check [API Reference](api.md#core-functions)
3. **Configuration**: Read [Configuration Guide](configuration.md)
4. **Monitoring**: Set up [Performance Monitoring](monitoring.md)

## Key Concepts

### Rust Acceleration

LiteLLM Rust provides high-performance implementations of critical LiteLLM components:

- **Token Counting**: 5-20x faster with batch processing
- **Request Routing**: 3-8x faster with lock-free data structures
- **Rate Limiting**: 4-12x faster with async operations
- **Connection Pooling**: 2-5x faster with intelligent reuse

### Feature Flags

Safe deployment through gradual rollout:

- **Canary**: Small percentage testing (5-15%)
- **Gradual Rollout**: Progressive deployment (25% → 50% → 100%)
- **Shadow Mode**: Background execution without affecting responses
- **Automatic Fallback**: Error-based degradation to Python

### Performance Monitoring

Production-ready observability:

- **Real-time Metrics**: Latency, throughput, error rates
- **Statistical Analysis**: P50, P95, P99 percentiles
- **Alert System**: Configurable thresholds and notifications
- **Optimization Engine**: Automated recommendations

## Examples

### Basic Usage

```python
import litellm_rust  # Automatic acceleration applied
import litellm

response = litellm.completion(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Feature Flag Control

```python
# Check if features are enabled
routing_enabled = litellm_rust.is_enabled("rust_routing")
token_enabled = litellm_rust.is_enabled("rust_token_counting")

# Get comprehensive status
status = litellm_rust.get_feature_status()
```

### Performance Monitoring

```python
# Record custom metrics
litellm_rust.record_performance(
    component="rust_token_counting",
    operation="count_tokens",
    duration_ms=15.5,
    success=True
)

# Get performance statistics
stats = litellm_rust.get_performance_stats()
recommendations = litellm_rust.get_recommendations()
```

### Configuration

```bash
# Environment variables
export LITELLM_RUST_RUST_ROUTING=true
export LITELLM_RUST_BATCH_TOKEN_COUNTING=canary:10

# JSON configuration file
export LITELLM_RUST_FEATURE_CONFIG=/path/to/config.json
```

## Deployment Guide

### Development
1. Enable all features for testing
2. Use debug logging (`RUST_LOG=debug`)
3. Monitor performance with local dashboard

### Staging
1. Test gradual rollout strategies
2. Validate monitoring and alerting
3. Performance test under load

### Production
1. Start with canary deployment (5-10%)
2. Monitor metrics closely
3. Gradual rollout over 2-4 weeks
4. Full observability and alerting

## Support

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community support
- **Documentation**: Comprehensive guides and examples

## Contributing

We welcome contributions! See our [Contributing Guide](contributing.md) for:

- Development setup instructions
- Code style guidelines
- Testing requirements
- Pull request process

---

For the most up-to-date information, visit the [GitHub repository](https://github.com/your-username/litellm-rust).