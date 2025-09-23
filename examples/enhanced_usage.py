#!/usr/bin/env python3
"""
Enhanced usage example demonstrating the new LiteLLM Rust acceleration features.

This example shows:
- Feature flag management
- Performance monitoring
- Gradual rollout
- Automatic fallback
- Performance comparison
"""

import asyncio
import time
import random
from typing import List

import litellm_rust


def demonstrate_feature_flags():
    """Demonstrate feature flag functionality."""
    print("=== Feature Flag Management ===")

    # Check current feature status
    status = litellm_rust.get_feature_status()
    print(f"Total features: {status['global_status']['total_features']}")
    print(f"Enabled features: {status['global_status']['enabled_features']}")

    # Show individual feature status
    for feature_name, feature_data in status['features'].items():
        print(f"  {feature_name}: {feature_data['state']} ({feature_data['rollout_percentage']}%)")

    # Test feature flag checking
    print(f"\nRust routing enabled: {litellm_rust.is_enabled('rust_routing')}")
    print(f"Batch token counting enabled: {litellm_rust.is_enabled('batch_token_counting')}")
    print(f"Async routing enabled: {litellm_rust.is_enabled('async_routing')}")


def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring capabilities."""
    print("\n=== Performance Monitoring ===")

    # Simulate some operations with performance recording
    components = ['rust_routing', 'python_routing', 'rust_token_counting', 'python_token_counting']

    for i in range(50):
        component = random.choice(components)
        operation = "test_operation"

        # Simulate varying performance
        if component.startswith('rust'):
            duration = random.uniform(10, 50)  # Rust is faster
            success_rate = 0.98  # Rust is more reliable
        else:
            duration = random.uniform(50, 200)  # Python is slower
            success_rate = 0.95  # Python is less reliable

        success = random.random() < success_rate

        litellm_rust.record_performance(
            component=component,
            operation=operation,
            duration_ms=duration,
            success=success,
            input_size=random.randint(100, 1000),
            metadata={"test_run": i}
        )

    # Get performance statistics
    all_stats = litellm_rust.get_performance_stats()

    for component, stats in all_stats.items():
        print(f"\n{component}:")
        print(f"  Total calls: {stats['total_calls']}")
        print(f"  Average latency: {stats['avg_duration_ms']:.2f}ms")
        print(f"  Error rate: {stats['error_rate']:.2f}%")
        print(f"  Throughput: {stats['throughput_per_second']:.2f} ops/sec")

    # Compare implementations
    if 'rust_routing' in all_stats and 'python_routing' in all_stats:
        comparison = litellm_rust.compare_implementations('rust_routing', 'python_routing')
        if 'speed_improvement' in comparison:
            print(f"\nPerformance Comparison:")
            print(f"  Speed improvement: {comparison['speed_improvement']['avg_latency']:.2f}x")
            print(f"  Reliability improvement: {comparison['reliability']['reliability_improvement']:.2f}%")


def demonstrate_batch_processing():
    """Demonstrate batch processing capabilities."""
    print("\n=== Batch Processing ===")

    if not litellm_rust.RUST_ACCELERATION_AVAILABLE:
        print("Rust acceleration not available, skipping batch processing demo")
        return

    try:
        from litellm_rust.rust_extensions import litellm_token
        counter = litellm_token.SimpleTokenCounter(100)

        # Test single vs batch processing
        texts = [
            "This is a test message for token counting.",
            "Another message with different length and complexity.",
            "Short text.",
            "A much longer text that contains various words and should result in a higher token count when processed.",
            "Final test message for comparison."
        ]

        model = "gpt-3.5-turbo"

        # Single processing timing
        start_time = time.perf_counter()
        single_counts = []
        for text in texts:
            count = counter.count_tokens(text, model)
            single_counts.append(count)
        single_duration = (time.perf_counter() - start_time) * 1000

        # Batch processing timing
        start_time = time.perf_counter()
        batch_counts = counter.count_tokens_batch(texts, model)
        batch_duration = (time.perf_counter() - start_time) * 1000

        print(f"Single processing: {single_duration:.2f}ms")
        print(f"Batch processing: {batch_duration:.2f}ms")
        print(f"Speedup: {single_duration / batch_duration:.2f}x")
        print(f"Results match: {single_counts == batch_counts}")

    except Exception as e:
        print(f"Batch processing demo failed: {e}")


def demonstrate_gradual_rollout():
    """Demonstrate gradual rollout functionality."""
    print("\n=== Gradual Rollout Simulation ===")

    # Simulate multiple requests with consistent rollout
    requests = [f"request_{i}" for i in range(100)]

    enabled_count = 0
    for request_id in requests:
        if litellm_rust.is_enabled('rust_connection_pooling', request_id):
            enabled_count += 1

    print(f"Connection pooling enabled for {enabled_count}/100 requests ({enabled_count}%)")

    # Test canary rollout
    canary_enabled = 0
    for request_id in requests:
        if litellm_rust.is_enabled('batch_token_counting', request_id):
            canary_enabled += 1

    print(f"Batch token counting (canary) enabled for {canary_enabled}/100 requests ({canary_enabled}%)")


def demonstrate_recommendations():
    """Demonstrate optimization recommendations."""
    print("\n=== Optimization Recommendations ===")

    recommendations = litellm_rust.get_recommendations()

    if recommendations:
        for rec in recommendations:
            print(f"\n{rec['type'].upper()} - {rec['severity']}")
            print(f"  Component: {rec['component']}")
            print(f"  Message: {rec['message']}")
            print("  Suggestions:")
            for suggestion in rec['suggestions']:
                print(f"    - {suggestion}")
    else:
        print("No optimization recommendations at this time.")


def demonstrate_export_capabilities():
    """Demonstrate data export capabilities."""
    print("\n=== Data Export ===")

    # Export performance data as JSON
    json_data = litellm_rust.export_performance_data(format="json")
    print(f"JSON export size: {len(json_data)} characters")

    # Export as CSV
    csv_data = litellm_rust.export_performance_data(format="csv")
    print(f"CSV export size: {len(csv_data)} characters")

    # Show sample of JSON data
    import json
    try:
        data = json.loads(json_data)
        print(f"\nExported data contains:")
        print(f"  - {len(data.get('component_stats', {}))} component statistics")
        print(f"  - {len(data.get('alert_history', []))} alerts")
        print(f"  - {len(data.get('recommendations', []))} recommendations")
    except:
        print("Could not parse exported JSON data")


def demonstrate_patch_status():
    """Demonstrate patch status monitoring."""
    print("\n=== Patch Status ===")

    try:
        status = litellm_rust.get_patch_status()

        print(f"Total patches applied: {status['total_patches']}")

        for patch_key, patch_info in status['patched_functions'].items():
            print(f"\n{patch_key}:")
            print(f"  Feature flag: {patch_info['feature_flag']}")
            print(f"  Enabled: {patch_info['enabled']}")
            print(f"  Has original: {patch_info['has_original']}")
            print(f"  Has Rust: {patch_info['has_rust']}")

    except Exception as e:
        print(f"Could not get patch status: {e}")


async def demonstrate_async_features():
    """Demonstrate async-compatible features."""
    print("\n=== Async Features ===")

    # Simulate async operations
    async def async_operation(operation_id: int):
        await asyncio.sleep(0.01)  # Simulate async work

        # Record performance for async operation
        duration = random.uniform(5, 25)
        litellm_rust.record_performance(
            component="async_rust_routing",
            operation="async_route",
            duration_ms=duration,
            success=True,
            metadata={"operation_id": operation_id}
        )

        return f"Result {operation_id}"

    # Run multiple async operations
    tasks = [async_operation(i) for i in range(10)]
    results = await asyncio.gather(*tasks)

    print(f"Completed {len(results)} async operations")

    # Check async component stats
    async_stats = litellm_rust.get_performance_stats("async_rust_routing")
    if async_stats:
        print(f"Async routing average latency: {async_stats['avg_duration_ms']:.2f}ms")


def main():
    """Main demonstration function."""
    print("LiteLLM Rust Acceleration - Enhanced Features Demo")
    print("=" * 50)

    # Check if Rust acceleration is available
    if not litellm_rust.RUST_ACCELERATION_AVAILABLE:
        print("WARNING: Rust acceleration is not available!")
        print("This demo will show limited functionality.")

    # Run all demonstrations
    demonstrate_feature_flags()
    demonstrate_performance_monitoring()
    demonstrate_batch_processing()
    demonstrate_gradual_rollout()
    demonstrate_recommendations()
    demonstrate_export_capabilities()
    demonstrate_patch_status()

    # Run async demo
    print("\nRunning async demonstrations...")
    asyncio.run(demonstrate_async_features())

    print("\n" + "=" * 50)
    print("Demo completed! Check the output above for detailed results.")
    print("\nEnvironment variables you can use to control features:")
    print("  LITELLM_RUST_DISABLE_ALL=true          # Disable all Rust acceleration")
    print("  LITELLM_RUST_RUST_ROUTING=false        # Disable routing acceleration")
    print("  LITELLM_RUST_BATCH_TOKEN_COUNTING=canary:5  # Enable for 5% of traffic")
    print("  LITELLM_RUST_FEATURE_CONFIG=/path/to/config.json  # Load config from file")


if __name__ == "__main__":
    main()