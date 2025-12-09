#!/usr/bin/env python3
"""
Basic usage example of Fast LiteLLM.

This example shows how to:
1. Enable Rust acceleration
2. Check acceleration status
3. Use LiteLLM with acceleration
4. Monitor performance
"""

import litellm

# IMPORTANT: Import fast_litellm FIRST to enable acceleration
import fast_litellm


def main():
    print("Fast LiteLLM - Basic Usage Example")
    print("=" * 50)
    print()

    # 1. Check Rust acceleration status
    print("1. Checking Rust Acceleration Status")
    print("-" * 50)

    if fast_litellm.RUST_ACCELERATION_AVAILABLE:
        print("✓ Rust acceleration is AVAILABLE")
    else:
        print("✗ Rust acceleration is NOT available")
        print("  Build with: maturin develop --release")
        return

    # Get health status
    health = fast_litellm.health_check()
    print(f"✓ Status: {health.get('status', 'unknown')}")
    if "components" in health:
        print(f"✓ Components: {', '.join(health['components'])}")
    print()

    # 2. Check which features are enabled
    print("2. Feature Status")
    print("-" * 50)

    features = fast_litellm.get_feature_status()
    for feature_name, feature_status in features.items():
        enabled = feature_status.get("enabled", False)
        status_symbol = "✓" if enabled else "○"
        print(f"{status_symbol} {feature_name}: {'enabled' if enabled else 'disabled'}")
    print()

    # 3. Use LiteLLM with acceleration (token counting)
    print("3. Token Counting with Rust Acceleration")
    print("-" * 50)

    # Example 1: Encode text to tokens
    text = "Hello, world! This is a test of Fast LiteLLM."
    tokens = litellm.encode(model="gpt-3.5-turbo", text=text)
    print(f"✓ Text: '{text}'")
    print(f"✓ Tokens: {len(tokens)}")
    print(f"✓ First few tokens: {tokens[:5]}")
    print()

    # Example 2: Count tokens in messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2+2?"},
    ]
    token_count = litellm.token_counter(model="gpt-3.5-turbo", messages=messages)
    print(f"✓ Messages: {len(messages)} messages")
    print(f"✓ Total tokens: {token_count}")
    print()

    # 4. Check model information (uses accelerated lookups)
    print("4. Model Information Lookups")
    print("-" * 50)

    model_info = litellm.get_model_info("gpt-3.5-turbo")
    print(f"✓ Model: gpt-3.5-turbo")
    print(f"✓ Max tokens: {model_info.get('max_tokens', 'unknown')}")
    print(f"✓ Max input tokens: {model_info.get('max_input_tokens', 'unknown')}")
    print()

    # 5. Performance statistics
    print("5. Performance Statistics")
    print("-" * 50)

    stats = fast_litellm.get_performance_stats()
    if stats:
        print("✓ Performance data collected:")
        for key, value in list(stats.items())[:5]:
            print(f"  {key}: {value}")
    else:
        print("○ No performance data yet (run more operations)")
    print()

    print("=" * 50)
    print("✓ Example completed successfully!")
    print()
    print("Next steps:")
    print("  - Check docs/acceleration.md for details on what's accelerated")
    print("  - Run tests: ./scripts/test_rust.sh")
    print("  - See docs/testing.md for testing guide")


if __name__ == "__main__":
    main()
