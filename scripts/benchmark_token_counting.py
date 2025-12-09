#!/usr/bin/env python3
"""
Benchmark token counting performance with and without Fast LiteLLM acceleration.

This script compares the performance of token counting between:
1. Pure Python implementation (baseline)
2. Rust-accelerated implementation (Fast LiteLLM)
"""

import argparse
import json
import statistics
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

try:
    import fast_litellm

    HAS_RUST = fast_litellm.RUST_ACCELERATION_AVAILABLE
except ImportError:
    HAS_RUST = False
    print("⚠️  Fast LiteLLM Rust extensions not available, using Python only")


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


def create_test_data() -> List[Tuple[str, str]]:
    """Create test data with various text samples and models"""
    texts = [
        "Hello, world!",
        "This is a longer text with more tokens to count.",
        "Artificial intelligence and machine learning are transforming technology.",
        "The quick brown fox jumps over the lazy dog. This is another sentence. And here's a third one.",
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


def benchmark_python_token_counting(
    test_data: List[Tuple[str, str]], iterations: int
) -> BenchmarkResult:
    """Benchmark token counting using Python implementation"""
    print("🧪 Running Python token counting benchmark...")

    times = []

    # Warmup
    for text, model in test_data[:2]:
        try:
            import litellm

            litellm.token_counter(
                model=model, messages=[{"role": "user", "content": text}]
            )
        except:
            # Fallback to simple string operations if litellm isn't available
            len(text.split())

    # Actual benchmark
    for _ in range(iterations):
        start_time = time.perf_counter()

        for text, model in test_data:
            try:
                import litellm

                litellm.token_counter(
                    model=model, messages=[{"role": "user", "content": text}]
                )
            except:
                # Fallback to simple character counting
                len(text)

        end_time = time.perf_counter()
        times.append(end_time - start_time)

    return BenchmarkResult(
        name="Python Implementation",
        iterations=iterations,
        total_time=sum(times),
        avg_time=statistics.mean(times),
        min_time=min(times),
        max_time=max(times),
        times=times,
    )


def benchmark_shimmed_token_counting(
    test_data: List[Tuple[str, str]], iterations: int
) -> BenchmarkResult:
    """Benchmark token counting using shimmed LiteLLM functions (actual user experience)"""
    if not HAS_RUST:
        raise RuntimeError("Rust extensions not available")

    print(
        "🚀 Running shimmed token counting benchmark (with monkeypatching overhead)..."
    )

    # Import Fast LiteLLM first to apply shims
    import fast_litellm

    print(f"   Fast LiteLLM Rust Available: {fast_litellm.RUST_ACCELERATION_AVAILABLE}")

    times = []

    # Import LiteLLM after Fast LiteLLM to get shims
    import litellm

    # Warmup - this should now use shimmed functions
    for text, model in test_data[:2]:
        try:
            # This should go through the full PerformanceWrapper with feature flags, metrics, etc.
            litellm.token_counter(
                model=model, messages=[{"role": "user", "content": text}]
            )
        except Exception:
            len(text)

    # Actual benchmark - using the shimmed functions (this is what users experience)
    for _ in range(iterations):
        start_time = time.perf_counter()

        for text, model in test_data:
            try:
                # This goes through the full shim path:
                # litellm.token_counter -> PerformanceWrapper -> feature_flag_check -> rust_func -> metric_recording
                litellm.token_counter(
                    model=model, messages=[{"role": "user", "content": text}]
                )
            except Exception:
                len(text)

        end_time = time.perf_counter()
        times.append(end_time - start_time)

    return BenchmarkResult(
        name="Shimmed Implementation (with overhead)",
        iterations=iterations,
        total_time=sum(times),
        avg_time=statistics.mean(times),
        min_time=min(times),
        max_time=max(times),
        times=times,
    )


def benchmark_rust_token_counting(
    test_data: List[Tuple[str, str]], iterations: int
) -> BenchmarkResult:
    """Benchmark token counting using direct Rust calls (no shimming overhead)"""
    if not HAS_RUST:
        raise RuntimeError("Rust extensions not available")

    print("🚀 Running direct Rust token counting benchmark (no shim overhead)...")

    times = []

    # Warmup
    for text, model in test_data[:2]:
        try:
            import fast_litellm

            # Use Rust token counting directly (no shimming)
            fast_litellm.count_tokens(text, model)
        except AttributeError:
            # Fallback to basic functionality
            len(text)

    # Actual benchmark
    for _ in range(iterations):
        start_time = time.perf_counter()

        for text, model in test_data:
            try:
                import fast_litellm

                # Use Rust token counting directly (no shimming)
                fast_litellm.count_tokens(text, model)
            except AttributeError:
                # Fallback to basic functionality
                len(text)

        end_time = time.perf_counter()
        times.append(end_time - start_time)

    return BenchmarkResult(
        name="Direct Rust Implementation (no overhead)",
        iterations=iterations,
        total_time=sum(times),
        avg_time=statistics.mean(times),
        min_time=min(times),
        max_time=max(times),
        times=times,
    )


def compare_results(
    python_result: BenchmarkResult, rust_result: BenchmarkResult
) -> Dict[str, Any]:
    """Compare two benchmark results and return comparison metrics"""
    speedup = python_result.avg_time / rust_result.avg_time

    # Calculate performance improvement percentage
    improvement = (
        (python_result.avg_time - rust_result.avg_time) / python_result.avg_time
    ) * 100

    # Calculate throughput (iterations per second)
    python_throughput = python_result.iterations / python_result.total_time
    rust_throughput = rust_result.iterations / rust_result.total_time

    return {
        "speedup": speedup,
        "improvement_percent": improvement,
        "python_avg_time": python_result.avg_time,
        "rust_avg_time": rust_result.avg_time,
        "python_throughput": python_throughput,
        "rust_throughput": rust_throughput,
        "throughput_improvement": (
            (rust_throughput - python_throughput) / python_throughput
        )
        * 100,
    }


def print_benchmark_results(result: BenchmarkResult):
    """Print formatted benchmark results"""
    print(f"\n📊 {result.name}")
    print(f"  Iterations: {result.iterations}")
    print(f"  Total Time: {result.total_time:.4f}s")
    print(f"  Avg Time: {result.avg_time:.6f}s")
    print(f"  Min Time: {result.min_time:.6f}s")
    print(f"  Max Time: {result.max_time:.6f}s")
    print(f"  Std Dev: {statistics.stdev(result.times):.6f}s")
    print(f"  Throughput: {result.iterations / result.total_time:.2f} ops/s")


def print_comparison(comparison: Dict[str, Any]):
    """Print comparison results"""
    print("\n" + "=" * 60)
    print("📈 PERFORMANCE COMPARISON")
    print("=" * 60)

    print(f"Rust vs Python Speedup: {comparison['speedup']:.2f}x faster")
    print(f"Performance Improvement: {comparison['improvement_percent']:.1f}%")
    print(f"Throughput Improvement: {comparison['throughput_improvement']:.1f}%")

    print(f"\nPython Average: {comparison['python_avg_time']:.6f}s per batch")
    print(f"Rust Average:   {comparison['rust_avg_time']:.6f}s per batch")

    print(f"\nPython Throughput: {comparison['python_throughput']:.2f} ops/s")
    print(f"Rust Throughput:   {comparison['rust_throughput']:.2f} ops/s")

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
    else:
        rating = "⚠️  Rust implementation slower"

    print(f"\n{'='*60}")
    print(f"🎯 PERFORMANCE RATING: {rating}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark token counting with Fast LiteLLM"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of benchmark iterations (default: 100)",
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
        choices=["direct", "shimmed", "compare"],
        default="compare",
        help="Benchmark mode: direct (Rust only), shimmed (with monkeypatching), compare (all)",
    )

    args = parser.parse_args()

    print("🚀 Fast LiteLLM Token Counting Benchmark")
    print("=" * 60)
    print(f"Test iterations: {args.iterations}")
    print(f"Batch size: {args.batch_size}")
    print(f"Mode: {args.mode}")
    print(f"Rust acceleration: {'✅ Available' if HAS_RUST else '❌ Not Available'}")

    # Create test data
    all_test_data = create_test_data()
    # Select subset based on batch size
    test_data = all_test_data[: args.batch_size]

    print(f"Test samples: {len(test_data)} different text/model combinations")
    print()

    # Run Python benchmark (baseline)
    python_result = benchmark_python_token_counting(test_data, args.iterations)
    print_benchmark_results(python_result)

    if HAS_RUST:
        if args.mode == "shimmed" or args.mode == "compare":
            # Run shimmed benchmark (what users actually experience)
            shimmed_result = benchmark_shimmed_token_counting(
                test_data, args.iterations
            )
            print_benchmark_results(shimmed_result)

        if args.mode == "direct" or args.mode == "compare":
            # Run direct Rust benchmark (no overhead)
            rust_result = benchmark_rust_token_counting(test_data, args.iterations)
            print_benchmark_results(rust_result)

        # Prepare results based on mode
        if args.mode == "compare" and HAS_RUST:
            # Compare all three: Python baseline, direct Rust, shimmed Rust
            comparison_shim_vs_python = compare_results(python_result, shimmed_result)
            comparison_direct_vs_python = compare_results(python_result, rust_result)

            print("\n" + "=" * 60)
            print("📈 SHIMMED vs PYTHON COMPARISON")
            print("=" * 60)
            print_comparison(comparison_shim_vs_python)

            print("\n" + "=" * 60)
            print("📈 DIRECT RUST vs PYTHON COMPARISON")
            print("=" * 60)
            print_comparison(comparison_direct_vs_python)

            if hasattr(rust_result, "avg_time") and hasattr(shimmed_result, "avg_time"):
                print("\n" + "=" * 60)
                print("📈 SHIMMED OVERHEAD ANALYSIS")
                print("=" * 60)
                overhead_time = shimmed_result.avg_time - rust_result.avg_time
                overhead_percentage = (
                    (overhead_time / rust_result.avg_time) * 100
                    if rust_result.avg_time > 0
                    else 0
                )
                print(f"Shimmed avg: {shimmed_result.avg_time:.6f}s")
                print(f"Direct Rust avg: {rust_result.avg_time:.6f}s")
                print(
                    f"Shim overhead: {overhead_time:.6f}s ({overhead_percentage:.1f}%)"
                )

            # Prepare full results for JSON output
            full_results = {
                "benchmark_config": {
                    "mode": args.mode,
                    "iterations": args.iterations,
                    "batch_size": args.batch_size,
                    "test_samples": len(test_data),
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                },
                "python_results": {
                    "name": python_result.name,
                    "iterations": python_result.iterations,
                    "total_time": python_result.total_time,
                    "avg_time": python_result.avg_time,
                    "min_time": python_result.min_time,
                    "max_time": python_result.max_time,
                    "std_dev": statistics.stdev(python_result.times),
                },
                "shimmed_results": {
                    "name": shimmed_result.name,
                    "iterations": shimmed_result.iterations,
                    "total_time": shimmed_result.total_time,
                    "avg_time": shimmed_result.avg_time,
                    "min_time": shimmed_result.min_time,
                    "max_time": shimmed_result.max_time,
                    "std_dev": statistics.stdev(shimmed_result.times),
                },
                "rust_results": {
                    "name": rust_result.name,
                    "iterations": rust_result.iterations,
                    "total_time": rust_result.total_time,
                    "avg_time": rust_result.avg_time,
                    "min_time": rust_result.min_time,
                    "max_time": rust_result.max_time,
                    "std_dev": statistics.stdev(rust_result.times),
                },
                "comparison_shim_vs_python": comparison_shim_vs_python,
                "comparison_direct_vs_python": comparison_direct_vs_python,
                "overhead_analysis": {
                    "shim_overhead_time": overhead_time,
                    "shim_overhead_percentage": overhead_percentage,
                },
                "fast_litellm_info": {
                    "version": getattr(
                        __import__("fast_litellm", fromlist=["__version__"]),
                        "__version__",
                        "unknown",
                    ),
                    "rust_available": HAS_RUST,
                },
            }
        elif args.mode == "shimmed" and HAS_RUST:
            # Compare shimmed vs Python only
            comparison = compare_results(python_result, shimmed_result)
            print_comparison(comparison)

            full_results = {
                "benchmark_config": {
                    "mode": args.mode,
                    "iterations": args.iterations,
                    "batch_size": args.batch_size,
                    "test_samples": len(test_data),
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                },
                "python_results": {
                    "name": python_result.name,
                    "iterations": python_result.iterations,
                    "total_time": python_result.total_time,
                    "avg_time": python_result.avg_time,
                    "min_time": python_result.min_time,
                    "max_time": python_result.max_time,
                    "std_dev": statistics.stdev(python_result.times),
                },
                "shimmed_results": {
                    "name": shimmed_result.name,
                    "iterations": shimmed_result.iterations,
                    "total_time": shimmed_result.total_time,
                    "avg_time": shimmed_result.avg_time,
                    "min_time": shimmed_result.min_time,
                    "max_time": shimmed_result.max_time,
                    "std_dev": statistics.stdev(shimmed_result.times),
                },
                "comparison": comparison,
                "fast_litellm_info": {
                    "version": getattr(
                        __import__("fast_litellm", fromlist=["__version__"]),
                        "__version__",
                        "unknown",
                    ),
                    "rust_available": HAS_RUST,
                },
            }
        elif args.mode == "direct" and HAS_RUST:
            # Compare direct Rust vs Python only
            comparison = compare_results(python_result, rust_result)
            print_comparison(comparison)

            full_results = {
                "benchmark_config": {
                    "mode": args.mode,
                    "iterations": args.iterations,
                    "batch_size": args.batch_size,
                    "test_samples": len(test_data),
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                },
                "python_results": {
                    "name": python_result.name,
                    "iterations": python_result.iterations,
                    "total_time": python_result.total_time,
                    "avg_time": python_result.avg_time,
                    "min_time": python_result.min_time,
                    "max_time": python_result.max_time,
                    "std_dev": statistics.stdev(python_result.times),
                },
                "rust_results": {
                    "name": rust_result.name,
                    "iterations": rust_result.iterations,
                    "total_time": rust_result.total_time,
                    "avg_time": rust_result.avg_time,
                    "min_time": rust_result.min_time,
                    "max_time": rust_result.max_time,
                    "std_dev": statistics.stdev(rust_result.times),
                },
                "comparison": comparison,
                "fast_litellm_info": {
                    "version": getattr(
                        __import__("fast_litellm", fromlist=["__version__"]),
                        "__version__",
                        "unknown",
                    ),
                    "rust_available": HAS_RUST,
                },
            }
    else:
        print("\n❌ Rust acceleration not available - cannot run Rust benchmarks")

        # Prepare partial results for JSON output
        full_results = {
            "benchmark_config": {
                "mode": args.mode,
                "iterations": args.iterations,
                "batch_size": args.batch_size,
                "test_samples": len(test_data),
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            },
            "python_results": {
                "name": python_result.name,
                "iterations": python_result.iterations,
                "total_time": python_result.total_time,
                "avg_time": python_result.avg_time,
                "min_time": python_result.min_time,
                "max_time": python_result.max_time,
                "std_dev": statistics.stdev(python_result.times),
            },
            "message": "Rust acceleration not available for comparison",
            "fast_litellm_info": {"rust_available": HAS_RUST},
        }

    # Output JSON results if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(full_results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")


if __name__ == "__main__":
    main()
