#!/usr/bin/env python3
"""
Benchmark Fast LiteLLM shimmed performance vs baseline LiteLLM performance.

This script measures the actual performance that users experience when using
Fast LiteLLM - comparing the performance of LiteLLM functions before and after
they are shimmed with Rust acceleration.
"""

import argparse
import json
import os
import statistics
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class BenchmarkResult:
    """Represents the result of a single benchmark run"""

    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    times: List[float]
    config: Dict[str, Any]


@contextmanager
def isolated_litellm_import():
    """
    Context manager that provides a clean import environment for LiteLLM
    without Fast LiteLLM interference.
    """
    # Remove any existing LiteLLM modules from sys.modules
    modules_to_remove = [
        name for name in sys.modules.keys() if name.startswith("litellm")
    ]
    for module_name in modules_to_remove:
        del sys.modules[module_name]

    # Also remove fast_litellm modules
    modules_to_remove = [
        name for name in sys.modules.keys() if name.startswith("fast_litellm")
    ]
    for module_name in modules_to_remove:
        del sys.modules[module_name]

    try:
        yield
    finally:
        # Clean up again after use
        modules_to_remove = [
            name
            for name in sys.modules.keys()
            if name.startswith("litellm") or name.startswith("fast_litellm")
        ]
        for module_name in modules_to_remove:
            if module_name in sys.modules:
                del sys.modules[module_name]


def create_test_data() -> List[Tuple[str, str]]:
    """Create test data with various text samples and models"""
    texts = [
        "Hello, world!",
        "This is a longer text with more tokens to count.",
        "Artificial intelligence and machine learning are transforming technology.",
        "The quick brown fox jumps over the lazy dog. This is another sentence. Here's a third one.",
        "Large language models like GPT-4 and Claude are powerful tools for natural language processing. They can understand, generate, and manipulate human language with remarkable accuracy. These models have been trained on vast amounts of text data and can perform various tasks like question answering, text summarization, translation, and creative writing.",
        "Short.",
        "A" * 100,  # Long repetitive text
        "Multiple sentences. This is sentence two. Here's number three! And #4? Yes, indeed.",
    ]

    models = ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"]

    # Create combinations
    test_data = []
    for text in texts:
        for model in models:
            test_data.append((text, model))

    return test_data


def benchmark_baseline_litellm(
    test_data: List[Tuple[str, str]], iterations: int
) -> BenchmarkResult:
    """Benchmark LiteLLM performance without Fast LiteLLM acceleration"""
    print("🧪 Running baseline LiteLLM benchmark (without Fast LiteLLM)...")

    # Import LiteLLM in isolation
    with isolated_litellm_import():
        import litellm

    times = []

    # Warmup
    for text, model in test_data[: min(3, len(test_data))]:
        with isolated_litellm_import():
            import litellm

            try:
                # Use the original token_counter function
                litellm.token_counter(
                    model=model, messages=[{"role": "user", "content": text}]
                )
            except Exception:
                # Fallback for basic functionality
                len(text.split())

    # Actual benchmark
    for i in range(iterations):
        start_time = time.perf_counter()

        with isolated_litellm_import():
            import litellm

            for text, model in test_data:
                try:
                    # Call the original function
                    litellm.token_counter(
                        model=model, messages=[{"role": "user", "content": text}]
                    )
                except Exception:
                    # Fallback for basic functionality
                    len(text)

        end_time = time.perf_counter()
        times.append(end_time - start_time)

    return BenchmarkResult(
        name="LiteLLM Baseline (No Fast LiteLLM)",
        iterations=iterations,
        total_time=sum(times),
        avg_time=statistics.mean(times),
        min_time=min(times),
        max_time=max(times),
        times=times,
        config={"fast_litellm": False},
    )


def benchmark_shimmed_litellm(
    test_data: List[Tuple[str, str]],
    iterations: int,
    feature_flags: Optional[Dict[str, bool]] = None,
) -> BenchmarkResult:
    """Benchmark LiteLLM performance with Fast LiteLLM acceleration (shimmed functions)"""
    print("🚀 Running Fast LiteLLM benchmark (with shimmed functions)...")

    # Set up feature flags if provided
    if feature_flags:
        for flag_name, flag_value in feature_flags.items():
            os.environ[f"LITELLM_RUST_{flag_name.upper()}"] = str(flag_value).lower()

    # Import Fast LiteLLM first to apply shims
    import fast_litellm

    print(f"   Fast LiteLLM Rust: {fast_litellm.RUST_ACCELERATION_AVAILABLE}")

    times = []

    # Warmup - this should now use shimmed functions
    for text, model in test_data[: min(3, len(test_data))]:
        import litellm  # Now imports the shimmed version

        try:
            # This should use the shimmed function
            litellm.token_counter(
                model=model, messages=[{"role": "user", "content": text}]
            )
        except Exception:
            len(text)

    # Actual benchmark - using the shimmed functions
    for i in range(iterations):
        start_time = time.perf_counter()

        import litellm  # Use the same import (now shimmed)

        for text, model in test_data:
            try:
                # This should use the shimmed function with all overhead
                litellm.token_counter(
                    model=model, messages=[{"role": "user", "content": text}]
                )
            except Exception:
                len(text)

        end_time = time.perf_counter()
        times.append(end_time - start_time)

    # Clean up feature flags
    if feature_flags:
        for flag_name in feature_flags.keys():
            env_key = f"LITELLM_RUST_{flag_name.upper()}"
            if env_key in os.environ:
                del os.environ[env_key]

    return BenchmarkResult(
        name="LiteLLM with Fast LiteLLM Shims",
        iterations=iterations,
        total_time=sum(times),
        avg_time=statistics.mean(times),
        min_time=min(times),
        max_time=max(times),
        times=times,
        config={"fast_litellm": True, "feature_flags": feature_flags or {}},
    )


def benchmark_specific_shimmed_functions(
    test_data: List[Tuple[str, str]], iterations: int
) -> BenchmarkResult:
    """Benchmark specific shimmed functions to measure actual shim overhead"""
    print("🔧 Running detailed shimmed function benchmark...")

    # Import Fast LiteLLM first to apply shims
    import fast_litellm

    print(f"   Fast LiteLLM Rust: {fast_litellm.RUST_ACCELERATION_AVAILABLE}")

    times = []

    # Import LiteLLM after Fast LiteLLM to get shims
    import litellm

    # Warmup
    for text, model in test_data[: min(3, len(test_data))]:
        try:
            litellm.token_counter(
                model=model, messages=[{"role": "user", "content": text}]
            )
        except Exception:
            len(text)

    # Actual benchmark
    for i in range(iterations):
        start_time = time.perf_counter()

        for text, model in test_data:
            try:
                # This goes through the full shim:
                # litellm.token_counter -> PerformanceWrapper -> feature_flag_check -> rust_func -> metric_recording
                litellm.token_counter(
                    model=model, messages=[{"role": "user", "content": text}]
                )
            except Exception:
                len(text)

        end_time = time.perf_counter()
        times.append(end_time - start_time)

    return BenchmarkResult(
        name="Detailed Shimmed Functions",
        iterations=iterations,
        total_time=sum(times),
        avg_time=statistics.mean(times),
        min_time=min(times),
        max_time=max(times),
        times=times,
        config={
            "fast_litellm": True,
            "functions_benchmarked": ["token_counter"],
            "includes_shim_overhead": True,
        },
    )


def print_benchmark_results(result: BenchmarkResult):
    """Print formatted benchmark results"""
    print(f"\n📊 {result.name}")
    print(f"  Configuration: {result.config}")
    print(f"  Iterations: {result.iterations}")
    print(f"  Total Time: {result.total_time:.4f}s")
    print(f"  Avg Time: {result.avg_time:.6f}s")
    print(f"  Min Time: {result.min_time:.6f}s")
    print(f"  Max Time: {result.max_time:.6f}s")
    print(f"  Std Dev: {statistics.stdev(result.times):.6f}s")
    print(f"  Throughput: {result.iterations / result.total_time:.2f} ops/s")


def compare_results(
    baseline_result: BenchmarkResult, accelerated_result: BenchmarkResult
) -> Dict[str, Any]:
    """Compare two benchmark results and return comparison metrics"""
    if baseline_result.avg_time == 0:
        return {"error": "Baseline time is zero, cannot calculate comparison"}

    speedup = baseline_result.avg_time / accelerated_result.avg_time

    # Calculate performance improvement percentage
    improvement = (
        (baseline_result.avg_time - accelerated_result.avg_time)
        / baseline_result.avg_time
    ) * 100

    # Calculate throughput (iterations per second)
    baseline_throughput = baseline_result.iterations / baseline_result.total_time
    accelerated_throughput = (
        accelerated_result.iterations / accelerated_result.total_time
    )

    return {
        "speedup": speedup,
        "improvement_percent": improvement,
        "baseline_avg_time": baseline_result.avg_time,
        "accelerated_avg_time": accelerated_result.avg_time,
        "baseline_throughput": baseline_throughput,
        "accelerated_throughput": accelerated_throughput,
        "throughput_improvement": (
            (accelerated_throughput - baseline_throughput) / baseline_throughput
        )
        * 100,
    }


def print_comparison(comparison: Dict[str, Any]):
    """Print comparison results"""
    if "error" in comparison:
        print(f"\n❌ {comparison['error']}")
        return

    print("\n" + "=" * 60)
    print("📈 PERFORMANCE COMPARISON (SHIMMED vs BASELINE)")
    print("=" * 60)

    print(f"Shimmed vs Baseline Speedup: {comparison['speedup']:.2f}x")
    print(f"Performance Improvement: {comparison['improvement_percent']:.1f}%")
    print(f"Throughput Improvement: {comparison['throughput_improvement']:.1f}%")

    print(f"\nBaseline Average: {comparison['baseline_avg_time']:.6f}s per batch")
    print(f"Shimmed Average:  {comparison['accelerated_avg_time']:.6f}s per batch")

    print(f"\nBaseline Throughput: {comparison['baseline_throughput']:.2f} ops/s")
    print(f"Shimmed Throughput:  {comparison['accelerated_throughput']:.2f} ops/s")

    # Performance rating
    if comparison["speedup"] >= 10:
        rating = "🚀 Outstanding! (10x+ speedup)"
    elif comparison["speedup"] >= 5:
        rating = "⚡ Excellent! (5x+ speedup)"
    elif comparison["speedup"] >= 2:
        rating = "✅ Very Good! (2x+ speedup)"
    elif comparison["speedup"] >= 1.5:
        rating = "👍 Good! (1.5x+ speedup)"
    elif comparison["speedup"] >= 1.1:
        rating = "📊 Modest improvement"
    elif comparison["speedup"] >= 1.0:
        rating = "⚠️  Minimal improvement"
    else:
        rating = "❌ Performance regression"

    print(f"\n{'='*60}")
    print(f"🎯 PERFORMANCE RATING: {rating}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Fast LiteLLM shimmed performance vs baseline"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=50,
        help="Number of benchmark iterations (default: 50)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of text samples per iteration (default: 10)",
    )
    parser.add_argument("--output", type=str, help="Output file for JSON results")
    parser.add_argument(
        "--mode",
        choices=["shimmed", "compare", "detailed"],
        default="compare",
        help="Benchmark mode: shimmed (only accelerated), compare (with baseline), detailed (specific functions)",
    )

    args = parser.parse_args()

    print("🚀 Fast LiteLLM Shimmed Performance Benchmark")
    print("=" * 60)
    print(f"Test iterations: {args.iterations}")
    print(f"Batch size: {args.batch_size}")
    print(f"Mode: {args.mode}")

    # Create test data
    all_test_data = create_test_data()
    # Select subset based on batch size
    test_data = all_test_data[: args.batch_size]

    print(f"Test samples: {len(test_data)} different text/model combinations")
    print()

    if args.mode == "compare":
        # Run baseline benchmark
        baseline_result = benchmark_baseline_litellm(test_data, args.iterations)
        print_benchmark_results(baseline_result)

        # Run shimmed benchmark
        shimmed_result = benchmark_shimmed_litellm(test_data, args.iterations)
        print_benchmark_results(shimmed_result)

        # Compare results
        comparison = compare_results(baseline_result, shimmed_result)
        print_comparison(comparison)

        # Prepare full results for JSON output
        full_results = {
            "benchmark_config": {
                "mode": args.mode,
                "iterations": args.iterations,
                "batch_size": args.batch_size,
                "test_samples": len(test_data),
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            },
            "baseline_results": {
                "name": baseline_result.name,
                "iterations": baseline_result.iterations,
                "total_time": baseline_result.total_time,
                "avg_time": baseline_result.avg_time,
                "min_time": baseline_result.min_time,
                "max_time": baseline_result.max_time,
                "std_dev": statistics.stdev(baseline_result.times),
                "config": baseline_result.config,
            },
            "shimmed_results": {
                "name": shimmed_result.name,
                "iterations": shimmed_result.iterations,
                "total_time": shimmed_result.total_time,
                "avg_time": shimmed_result.avg_time,
                "min_time": shimmed_result.min_time,
                "max_time": shimmed_result.max_time,
                "std_dev": statistics.stdev(shimmed_result.times),
                "config": shimmed_result.config,
            },
            "comparison": comparison,
        }

    elif args.mode == "shimmed":
        # Only run shimmed version
        shimmed_result = benchmark_shimmed_litellm(test_data, args.iterations)
        print_benchmark_results(shimmed_result)

        full_results = {
            "benchmark_config": {
                "mode": args.mode,
                "iterations": args.iterations,
                "batch_size": args.batch_size,
                "test_samples": len(test_data),
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            },
            "shimmed_results": {
                "name": shimmed_result.name,
                "iterations": shimmed_result.iterations,
                "total_time": shimmed_result.total_time,
                "avg_time": shimmed_result.avg_time,
                "min_time": shimmed_result.min_time,
                "max_time": shimmed_result.max_time,
                "std_dev": statistics.stdev(shimmed_result.times),
                "config": shimmed_result.config,
            },
        }

    elif args.mode == "detailed":
        # Run detailed benchmark of specific shimmed functions
        detailed_result = benchmark_specific_shimmed_functions(
            test_data, args.iterations
        )
        print_benchmark_results(detailed_result)

        full_results = {
            "benchmark_config": {
                "mode": args.mode,
                "iterations": args.iterations,
                "batch_size": args.batch_size,
                "test_samples": len(test_data),
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            },
            "detailed_results": {
                "name": detailed_result.name,
                "iterations": detailed_result.iterations,
                "total_time": detailed_result.total_time,
                "avg_time": detailed_result.avg_time,
                "min_time": detailed_result.min_time,
                "max_time": detailed_result.max_time,
                "std_dev": statistics.stdev(detailed_result.times),
                "config": detailed_result.config,
            },
        }

    # Output JSON results if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(full_results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")

    print(f"\n✅ Benchmark completed!")


if __name__ == "__main__":
    main()
