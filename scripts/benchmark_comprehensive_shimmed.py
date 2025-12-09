#!/usr/bin/env python3
"""
Comprehensive benchmark for all Fast LiteLLM shimmed functions.

This script benchmarks all the performance-critical functions that Fast LiteLLM
monkeypatches, providing a complete performance overview.
"""

import argparse
import json
import os
import statistics
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple


@dataclass
class BenchmarkResult:
    """Represents the result of a single benchmark run"""

    name: str
    function: str
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
        if module_name in sys.modules:
            del sys.modules[module_name]

    # Also remove fast_litellm modules
    modules_to_remove = [
        name for name in sys.modules.keys() if name.startswith("fast_litellm")
    ]
    for module_name in modules_to_remove:
        if module_name in sys.modules:
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


def create_test_data() -> Dict[str, Any]:
    """Create comprehensive test data for all shimmable functions"""
    texts = [
        "Hello, world!",
        "This is a longer text with more tokens to count.",
        "Artificial intelligence and machine learning are transforming technology.",
        "Large language models like GPT-4 and Claude are powerful tools for natural language processing.",
        "A" * 100,  # Long repetitive text
    ]

    messages = [
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ],
        [{"role": "user", "content": text} for text in texts[:3]],
    ]

    models = ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"]

    # Prepare routing test data
    model_list = [
        {"model_name": "gpt-3.5-turbo", "litellm_params": {"model": "gpt-3.5-turbo"}},
        {"model_name": "gpt-4", "litellm_params": {"model": "gpt-4"}},
        {
            "model_name": "claude-3-sonnet",
            "litellm_params": {"model": "claude-3-sonnet"},
        },
    ]

    return {
        "texts": texts,
        "messages": messages,
        "models": models,
        "model_list": model_list,
        "prompts": [
            "Translate this to French: Hello world",
            "Summarize: This is a long text that needs summarization",
        ],
    }


def benchmark_baseline_function(
    func_name: str, test_data: Dict[str, Any], iterations: int
) -> BenchmarkResult:
    """Benchmark a specific function without Fast LiteLLM shims"""

    with isolated_litellm_import():
        import litellm

    times = []

    # Define function-specific warmup and test logic based on actual shims
    if func_name == "token_counter":
        # Warmup
        for text, model in zip(test_data["texts"][:2], test_data["models"][:2]):
            try:
                import litellm

                litellm.utils.token_counter(
                    model=model, messages=[{"role": "user", "content": text}]
                )
            except:
                len(text.split())  # Fallback

        # Benchmark
        for i in range(iterations):
            start_time = time.perf_counter()
            for text, model in zip(test_data["texts"], test_data["models"]):
                try:
                    import litellm

                    litellm.utils.token_counter(
                        model=model, messages=[{"role": "user", "content": text}]
                    )
                except:
                    len(text.split())  # Fallback
            end_time = time.perf_counter()
            times.append(end_time - start_time)

    elif func_name == "count_tokens_batch":
        # Warmup
        try:
            import litellm

            if hasattr(litellm.utils, "count_tokens_batch"):
                litellm.utils.count_tokens_batch(
                    test_data["texts"][:2], test_data["models"][0]
                )
            else:
                # Fallback for batch processing
                for text in test_data["texts"][:2]:
                    len(text.split())
        except:
            pass  # Fallback

        # Benchmark
        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                import litellm

                if hasattr(litellm.utils, "count_tokens_batch"):
                    litellm.utils.count_tokens_batch(
                        test_data["texts"], test_data["models"][0]
                    )
                else:
                    # Fallback for batch processing
                    for text in test_data["texts"]:
                        len(text.split())
            except:
                # Fallback
                for text in test_data["texts"]:
                    len(text.split())
            end_time = time.perf_counter()
            times.append(end_time - start_time)

    elif func_name == "router":
        # For router, we'll test router creation and basic functionality
        # Warmup - try to import and use router
        try:
            import litellm

            if hasattr(litellm, "Router"):
                # Simple router test
                router = litellm.Router(test_data["model_list"][:1])
                str(router)  # Basic operation
        except:
            pass  # Fallback

        # Benchmark
        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                import litellm

                if hasattr(litellm, "Router"):
                    router = litellm.Router(test_data["model_list"])
                    # Perform a basic operation on the router
                    _ = len(router.model_list) if hasattr(router, "model_list") else 0
            except:
                pass  # Fallback
            end_time = time.perf_counter()
            times.append(end_time - start_time)

    elif func_name == "rate_limiter":
        # For rate limiter, test creation and basic functionality
        # Warmup
        try:
            import litellm

            if hasattr(litellm, "SimpleRateLimiter"):
                rate_limiter = litellm.SimpleRateLimiter()
                # Basic check
                hasattr(rate_limiter, "is_allowed")
        except:
            pass  # Fallback

        # Benchmark
        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                import litellm

                if hasattr(litellm, "SimpleRateLimiter"):
                    rate_limiter = litellm.SimpleRateLimiter()
                    # Perform a basic operation
                    _ = hasattr(rate_limiter, "is_allowed")
            except:
                pass  # Fallback
            end_time = time.perf_counter()
            times.append(end_time - start_time)

    elif func_name == "connection_pool":
        # For connection pool, test creation and basic functionality
        # Warmup
        try:
            import litellm

            if hasattr(litellm, "SimpleConnectionPool"):
                pool = litellm.SimpleConnectionPool()
                # Basic check
                hasattr(pool, "get_connection")
        except:
            pass  # Fallback

        # Benchmark
        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                import litellm

                if hasattr(litellm, "SimpleConnectionPool"):
                    pool = litellm.SimpleConnectionPool()
                    # Perform a basic operation
                    _ = hasattr(pool, "get_connection")
            except:
                pass  # Fallback
            end_time = time.perf_counter()
            times.append(end_time - start_time)

    else:
        # Fallback for unknown function - just measure text processing time
        for i in range(iterations):
            start_time = time.perf_counter()
            for text in test_data["texts"]:
                len(text)  # Basic operation
            end_time = time.perf_counter()
            times.append(end_time - start_time)

    return BenchmarkResult(
        name=f"Baseline {func_name}",
        function=func_name,
        iterations=iterations,
        total_time=sum(times),
        avg_time=statistics.mean(times),
        min_time=min(times),
        max_time=max(times),
        times=times,
        config={"fast_litellm": False, "function": func_name},
    )


def benchmark_shimmed_function(
    func_name: str, test_data: Dict[str, Any], iterations: int
) -> BenchmarkResult:
    """Benchmark a specific function with Fast LiteLLM shims applied"""

    # Import Fast LiteLLM first to apply shims
    import fast_litellm

    print(
        f"   Fast LiteLLM Rust: {fast_litellm.RUST_ACCELERATION_AVAILABLE} for {func_name}"
    )

    # Import LiteLLM after Fast LiteLLM to get shims
    import litellm

    times = []

    # Define function-specific warmup and test logic based on actual shims
    if func_name == "token_counter":
        # Warmup
        for text, model in zip(test_data["texts"][:2], test_data["models"][:2]):
            try:
                # This goes through the shimmed path if available
                litellm.utils.token_counter(
                    model=model, messages=[{"role": "user", "content": text}]
                )
            except:
                len(text.split())  # Fallback

        # Benchmark - this goes through the full shim path
        for i in range(iterations):
            start_time = time.perf_counter()
            for text, model in zip(test_data["texts"], test_data["models"]):
                try:
                    # This goes through: litellm.utils.token_counter -> PerformanceWrapper -> feature_flag_check -> rust_func -> metric_recording
                    litellm.utils.token_counter(
                        model=model, messages=[{"role": "user", "content": text}]
                    )
                except:
                    len(text.split())  # Fallback
            end_time = time.perf_counter()
            times.append(end_time - start_time)

    elif func_name == "count_tokens_batch":
        # Warmup
        try:
            # This should go through the shimmed path if available
            if hasattr(litellm.utils, "count_tokens_batch"):
                litellm.utils.count_tokens_batch(
                    test_data["texts"][:2], test_data["models"][0]
                )
            else:
                # Fallback for batch processing
                for text in test_data["texts"][:2]:
                    len(text.split())
        except:
            pass  # Fallback

        # Benchmark
        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                # This should go through the shimmed path if available
                if hasattr(litellm.utils, "count_tokens_batch"):
                    litellm.utils.count_tokens_batch(
                        test_data["texts"], test_data["models"][0]
                    )
                else:
                    # Fallback for batch processing
                    for text in test_data["texts"]:
                        len(text.split())
            except:
                # Fallback
                for text in test_data["texts"]:
                    len(text.split())
            end_time = time.perf_counter()
            times.append(end_time - start_time)

    elif func_name == "router":
        # For router, we'll test router creation and basic functionality
        # Warmup - try to use the shimmed router if available
        try:
            if hasattr(litellm, "Router"):
                router = litellm.Router(test_data["model_list"][:1])
                str(router)  # Basic operation
        except:
            pass  # Fallback

        # Benchmark - test the shimmed router
        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                if hasattr(litellm, "Router"):
                    router = litellm.Router(test_data["model_list"])
                    # Perform a basic operation on the router
                    _ = len(router.model_list) if hasattr(router, "model_list") else 0
            except:
                pass  # Fallback
            end_time = time.perf_counter()
            times.append(end_time - start_time)

    elif func_name == "rate_limiter":
        # For rate limiter, test creation and basic functionality
        # Warmup
        try:
            if hasattr(litellm, "SimpleRateLimiter"):
                rate_limiter = litellm.SimpleRateLimiter()
                # Basic check
                hasattr(rate_limiter, "is_allowed")
        except:
            pass  # Fallback

        # Benchmark
        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                if hasattr(litellm, "SimpleRateLimiter"):
                    rate_limiter = litellm.SimpleRateLimiter()
                    # Perform a basic operation
                    _ = hasattr(rate_limiter, "is_allowed")
            except:
                pass  # Fallback
            end_time = time.perf_counter()
            times.append(end_time - start_time)

    elif func_name == "connection_pool":
        # For connection pool, test creation and basic functionality
        # Warmup
        try:
            if hasattr(litellm, "SimpleConnectionPool"):
                pool = litellm.SimpleConnectionPool()
                # Basic check
                hasattr(pool, "get_connection")
        except:
            pass  # Fallback

        # Benchmark
        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                if hasattr(litellm, "SimpleConnectionPool"):
                    pool = litellm.SimpleConnectionPool()
                    # Perform a basic operation
                    _ = hasattr(pool, "get_connection")
            except:
                pass  # Fallback
            end_time = time.perf_counter()
            times.append(end_time - start_time)

    else:
        # Fallback for unknown function
        for i in range(iterations):
            start_time = time.perf_counter()
            for text in test_data["texts"]:
                len(text)  # Basic operation
            end_time = time.perf_counter()
            times.append(end_time - start_time)

    return BenchmarkResult(
        name=f"Shimmed {func_name}",
        function=func_name,
        iterations=iterations,
        total_time=sum(times),
        avg_time=statistics.mean(times),
        min_time=min(times),
        max_time=max(times),
        times=times,
        config={
            "fast_litellm": True,
            "function": func_name,
            "includes_shim_overhead": True,
        },
    )


def calculate_comparison_metrics(
    baseline_result: BenchmarkResult, shimmed_result: BenchmarkResult
) -> Dict[str, Any]:
    """Calculate performance comparison metrics"""
    if baseline_result.avg_time == 0:
        return {
            "error": f"Baseline time is zero for {baseline_result.function}, cannot calculate comparison"
        }

    speedup = baseline_result.avg_time / shimmed_result.avg_time
    improvement = (
        (baseline_result.avg_time - shimmed_result.avg_time) / baseline_result.avg_time
    ) * 100
    baseline_throughput = baseline_result.iterations / baseline_result.total_time
    shimmed_throughput = shimmed_result.iterations / shimmed_result.total_time
    throughput_improvement = (
        (shimmed_throughput - baseline_throughput) / baseline_throughput
    ) * 100

    return {
        "function": baseline_result.function,
        "speedup": speedup,
        "improvement_percent": improvement,
        "baseline_avg_time": baseline_result.avg_time,
        "shimmed_avg_time": shimmed_result.avg_time,
        "baseline_throughput": baseline_throughput,
        "shimmed_throughput": shimmed_throughput,
        "throughput_improvement": throughput_improvement,
    }


def print_benchmark_results(result: BenchmarkResult):
    """Print formatted benchmark results"""
    print(f"\n📊 {result.name}")
    print(f"  Function: {result.function}")
    print(f"  Configuration: {result.config}")
    print(f"  Iterations: {result.iterations}")
    print(f"  Total Time: {result.total_time:.4f}s")
    print(f"  Avg Time: {result.avg_time:.6f}s")
    print(f"  Min Time: {result.min_time:.6f}s")
    print(f"  Max Time: {result.max_time:.6f}s")
    print(f"  Std Dev: {statistics.stdev(result.times):.6f}s")
    print(f"  Throughput: {result.iterations / result.total_time:.2f} ops/s")


def print_summary_table(
    all_baselines: List[BenchmarkResult], all_shimmeds: List[BenchmarkResult]
):
    """Print a summary table comparing all functions"""

    print("\n" + "=" * 100)
    print("📋 COMPREHENSIVE FUNCTION PERFORMANCE SUMMARY")
    print("=" * 100)

    print(
        f"{'Function':<20} {'Baseline Time':<15} {'Shimmed Time':<15} {'Speedup':<10} {'Improvement':<12} {'Status':<10}"
    )
    print("-" * 100)

    for baseline, shimmed in zip(all_baselines, all_shimmeds):
        speedup = baseline.avg_time / shimmed.avg_time if baseline.avg_time > 0 else 0
        improvement = (
            ((baseline.avg_time - shimmed.avg_time) / baseline.avg_time) * 100
            if baseline.avg_time > 0
            else 0
        )

        # Determine status
        if speedup > 1.0:
            status = "✅"
        elif speedup >= 0.95:  # Within 5% - acceptable
            status = "⚠️"
        else:
            status = "❌"

        print(
            f"{baseline.function:<20} "
            f"{baseline.avg_time:.6f}s{'':<4} "
            f"{shimmed.avg_time:.6f}s{'':<4} "
            f"{speedup:.2f}x{'':<7} "
            f"{improvement:>+6.1f}%{'':<5} "
            f"{status}"
        )

    print("=" * 100)


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive benchmark for all Fast LiteLLM shimmed functions"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=30,
        help="Number of benchmark iterations per function (default: 30)",
    )
    parser.add_argument("--output", type=str, help="Output file for JSON results")
    parser.add_argument(
        "--functions",
        nargs="+",
        default=[
            "token_counter",
            "count_tokens_batch",
            "router",
            "rate_limiter",
            "connection_pool",
        ],
        help="Functions to benchmark (default: token_counter count_tokens_batch router rate_limiter connection_pool)",
    )

    args = parser.parse_args()

    print("🚀 Fast LiteLLM Comprehensive Shim Benchmark")
    print("=" * 80)
    print(f"Test iterations per function: {args.iterations}")
    print(f"Functions to test: {', '.join(args.functions)}")
    print("This tests ALL functions that Fast LiteLLM shims according to source code")
    print("=" * 80)

    # Create test data
    test_data = create_test_data()
    print(
        f"Test data: {len(test_data['texts'])} text samples, {len(test_data['models'])} models, {len(test_data['model_list'])} routing configs"
    )
    print()

    # Run benchmarks for each function
    all_baselines = []
    all_shimmeds = []

    for func_name in args.functions:
        print(f"\n🔬 Testing function: {func_name}")
        print("-" * 50)

        # Run baseline benchmark (without Fast LiteLLM)
        print("⏳ Running baseline benchmark...")
        baseline_result = benchmark_baseline_function(
            func_name, test_data, args.iterations
        )
        print_benchmark_results(baseline_result)
        all_baselines.append(baseline_result)

        # Run shimmed benchmark (with Fast LiteLLM)
        print("⏳ Running shimmed benchmark...")
        shimmed_result = benchmark_shimmed_function(
            func_name, test_data, args.iterations
        )
        print_benchmark_results(shimmed_result)
        all_shimmeds.append(shimmed_result)

        # Compare this specific function
        comparison = calculate_comparison_metrics(baseline_result, shimmed_result)
        if "error" not in comparison:
            print(
                f"\n📈 {func_name} comparison: {comparison['speedup']:.2f}x speedup ({comparison['improvement_percent']:+.1f}%)"
            )
        else:
            print(f"\n❌ {comparison['error']}")

    # Print summary table
    print_summary_table(all_baselines, all_shimmeds)

    # Prepare results for JSON output
    comparisons = []
    for baseline, shimmed in zip(all_baselines, all_shimmeds):
        comparison = calculate_comparison_metrics(baseline, shimmed)
        if "error" not in comparison:
            comparisons.append(comparison)

    full_results = {
        "benchmark_config": {
            "iterations": args.iterations,
            "functions_benchmarked": args.functions,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        },
        "baseline_results": [
            {
                "function": result.function,
                "name": result.name,
                "avg_time": result.avg_time,
                "total_time": result.total_time,
                "throughput": result.iterations / result.total_time,
            }
            for result in all_baselines
        ],
        "shimmed_results": [
            {
                "function": result.function,
                "name": result.name,
                "avg_time": result.avg_time,
                "total_time": result.total_time,
                "throughput": result.iterations / result.total_time,
            }
            for result in all_shimmeds
        ],
        "comparisons": comparisons,
    }

    # Output JSON results if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(full_results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")

    print(f"\n✅ Comprehensive benchmark completed!")


if __name__ == "__main__":
    main()
