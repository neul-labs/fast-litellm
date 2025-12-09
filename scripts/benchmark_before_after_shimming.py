#!/usr/bin/env python3
"""
Compare LiteLLM performance before and after Fast LiteLLM shimming.

This script measures the exact same operations with and without Fast LiteLLM,
capturing the genuine performance difference that users will experience.
"""

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


@dataclass
class BenchmarkConfig:
    """Configuration for benchmarking"""

    iterations: int
    batch_size: int
    test_functions: List[str]
    feature_flags: Dict[str, str]


@dataclass
class BenchmarkRun:
    """Represents a single benchmark run"""

    name: str
    times: List[float]
    config: BenchmarkConfig
    metadata: Dict[str, Any]


def create_test_data() -> List[Tuple[str, str]]:
    """Create test data with various text samples and models"""
    texts = [
        "Hello, world!",
        "This is a longer text with more tokens to count.",
        "Artificial intelligence and machine learning are transforming technology.",
        "The quick brown fox jumps over the lazy dog. This is another sentence. Here's a third one.",
        "Large language models like GPT-4 and Claude are powerful tools for natural language processing. They can understand, generate, and manipulate human language with remarkable accuracy.",
        "Short.",
        "A" * 100,
        "Multiple sentences. This is sentence two. Here's number three! And #4? Yes, indeed.",
    ]

    models = ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"]

    # Create combinations
    test_data = []
    for text in texts:
        for model in models:
            test_data.append((text, model))

    return test_data


def run_benchmark_in_subprocess(
    use_fast_litellm: bool, test_data: List[Tuple[str, str]], iterations: int
) -> BenchmarkRun:
    """Run benchmark in a subprocess to ensure clean environment"""

    # Create a temporary script for the subprocess
    if use_fast_litellm:
        script_content = f"""
import time
import sys
import json

# Import Fast LiteLLM first to apply shims
import fast_litellm
print(f"Fast LiteLLM Rust Available: {{fast_litellm.RUST_ACCELERATION_AVAILABLE}}", file=sys.stderr)

# Now import LiteLLM (should be shimmed)
import litellm

# Prepare test data
test_data = {json.dumps([list(item) for item in test_data])}
iterations = {iterations}

# Warmup
for text, model in test_data[:3]:
    try:
        litellm.token_counter(model=model, messages=[{{"role": "user", "content": text}}])
    except:
        len(text)

times = []
for i in range(iterations):
    start = time.perf_counter()
    for text, model in test_data:
        try:
            litellm.token_counter(model=model, messages=[{{"role": "user", "content": text}}])
        except:
            len(text)
    end = time.perf_counter()
    times.append(end - start)

# Output results as JSON
import json
print(json.dumps(times))
"""
    else:
        # Benchmark without Fast LiteLLM
        script_content = f"""
import time
import sys
import json

# Import LiteLLM directly (no Fast LiteLLM)
import litellm

# Prepare test data
test_data = {json.dumps([list(item) for item in test_data])}
iterations = {iterations}

# Warmup
for text, model in test_data[:3]:
    try:
        litellm.token_counter(model=model, messages=[{{"role": "user", "content": text}}])
    except:
        len(text)

times = []
for i in range(iterations):
    start = time.perf_counter()
    for text, model in test_data:
        try:
            litellm.token_counter(model=model, messages=[{{"role": "user", "content": text}}])
        except:
            len(text)
    end = time.perf_counter()
    times.append(end - start)

# Output results as JSON
import json
print(json.dumps(times))
"""

    # Write temp script
    temp_script = Path("temp_benchmark.py")
    temp_script.write_text(script_content)

    try:
        # Run the subprocess
        result = subprocess.run(
            [sys.executable, str(temp_script)],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
        )

        if result.returncode != 0:
            print(f"Subprocess error: {result.stderr}")
            raise RuntimeError(f"Benchmark subprocess failed: {result.stderr}")

        # Parse the results
        times = json.loads(result.stdout.strip())

        return BenchmarkRun(
            name="Fast LiteLLM" if use_fast_litellm else "Baseline LiteLLM",
            times=times,
            config=BenchmarkConfig(
                iterations=iterations,
                batch_size=len(test_data),
                test_functions=["token_counter"],
                feature_flags={},
            ),
            metadata={"use_fast_litellm": use_fast_litellm, "success": True},
        )

    finally:
        # Clean up temp script
        if temp_script.exists():
            temp_script.unlink()


def run_direct_comparison_benchmark(
    test_data: List[Tuple[str, str]], iterations: int
) -> Tuple[BenchmarkRun, BenchmarkRun]:
    """Run both baseline and shimmed benchmarks"""

    print("🔬 Running direct comparison benchmark...")
    print("   This may take a minute. Each version runs in a separate Python process.")
    print()

    # Run baseline (without Fast LiteLLM)
    print("⏳ Running baseline benchmark (LiteLLM without Fast LiteLLM)...")
    baseline_run = run_benchmark_in_subprocess(
        use_fast_litellm=False, test_data=test_data, iterations=iterations
    )
    print(f"   Baseline complete: {baseline_run.config.iterations} iterations")

    # Run with Fast LiteLLM (shimmed)
    print("⏳ Running Fast LiteLLM benchmark (LiteLLM with shims)...")
    shimmed_run = run_benchmark_in_subprocess(
        use_fast_litellm=True, test_data=test_data, iterations=iterations
    )
    print(f"   Fast LiteLLM complete: {shimmed_run.config.iterations} iterations")

    return baseline_run, shimmed_run


def calculate_comparison_metrics(
    baseline_run: BenchmarkRun, shimmed_run: BenchmarkRun
) -> Dict[str, Any]:
    """Calculate performance comparison metrics"""

    baseline_avg = statistics.mean(baseline_run.times)
    shimmed_avg = statistics.mean(shimmed_run.times)

    if baseline_avg == 0:
        return {"error": "Baseline time is zero, cannot calculate comparison"}

    speedup = baseline_avg / shimmed_avg
    improvement = ((baseline_avg - shimmed_avg) / baseline_avg) * 100
    baseline_throughput = len(baseline_run.times) / sum(baseline_run.times)
    shimmed_throughput = len(shimmed_run.times) / sum(shimmed_run.times)
    throughput_improvement = (
        (shimmed_throughput - baseline_throughput) / baseline_throughput
    ) * 100

    return {
        "speedup": speedup,
        "improvement_percent": improvement,
        "baseline_avg_time": baseline_avg,
        "shimmed_avg_time": shimmed_avg,
        "baseline_throughput": baseline_throughput,
        "shimmed_throughput": shimmed_throughput,
        "throughput_improvement": throughput_improvement,
        # Additional metrics
        "baseline_min_time": min(baseline_run.times),
        "baseline_max_time": max(baseline_run.times),
        "shimmed_min_time": min(shimmed_run.times),
        "shimmed_max_time": max(shimmed_run.times),
    }


def print_detailed_comparison(
    baseline_run: BenchmarkRun, shimmed_run: BenchmarkRun, metrics: Dict[str, Any]
):
    """Print detailed comparison results"""

    if "error" in metrics:
        print(f"❌ {metrics['error']}")
        return

    print("\n" + "=" * 80)
    print("🔬 DETAILED PERFORMANCE COMPARISON (BEFORE vs AFTER SHIMMING)")
    print("=" * 80)

    print(f"{'Metric':<30} {'Baseline':<15} {'Fast LiteLLM':<15} {'Improvement':<15}")
    print("-" * 80)

    def format_time(seconds):
        return f"{seconds:.6f}s"

    def format_throughput(tps):
        return f"{tps:.2f}"

    def format_percentage(pct):
        sign = "+" if pct >= 0 else ""
        return f"{sign}{pct:.1f}%"

    def format_speedup(s):
        return f"{s:.2f}x"

    # Average time
    print(
        f"{'Avg Time per Batch':<30} {format_time(metrics['baseline_avg_time']):<15} {format_time(metrics['shimmed_avg_time']):<15} {format_percentage(metrics['improvement_percent']):<15}"
    )

    # Min time
    print(
        f"{'Min Time per Batch':<30} {format_time(metrics['baseline_min_time']):<15} {format_time(metrics['shimmed_min_time']):<15} {'N/A':<15}"
    )

    # Max time
    print(
        f"{'Max Time per Batch':<30} {format_time(metrics['baseline_max_time']):<15} {format_time(metrics['shimmed_max_time']):<15} {'N/A':<15}"
    )

    # Throughput
    print(
        f"{'Throughput (ops/s)':<30} {format_throughput(metrics['baseline_throughput']):<15} {format_throughput(metrics['shimmed_throughput']):<15} {format_percentage(metrics['throughput_improvement']):<15}"
    )

    # Speedup
    print(
        f"{'Speedup':<30} {'N/A':<15} {format_speedup(metrics['speedup']):<15} {'vs Baseline':<15}"
    )

    print("\n" + "-" * 80)
    print("📊 STATISTICAL ANALYSIS")
    print("-" * 80)

    baseline_std = statistics.stdev(baseline_run.times)
    shimmed_std = statistics.stdev(shimmed_run.times)

    print(f"Baseline Std Dev:     {format_time(baseline_std)}")
    print(f"Shimmed Std Dev:      {format_time(shimmed_std)}")
    print(f"Baseline Median:      {format_time(statistics.median(baseline_run.times))}")
    print(f"Shimmed Median:       {format_time(statistics.median(shimmed_run.times))}")

    # Performance rating
    print("\n" + "-" * 80)
    print("🎯 PERFORMANCE ASSESSMENT")
    print("-" * 80)

    if metrics["speedup"] >= 10:
        rating = "🚀 Outstanding! (10x+ speedup)"
        color = "GREEN"
    elif metrics["speedup"] >= 5:
        rating = "⚡ Excellent! (5x+ speedup)"
        color = "GREEN"
    elif metrics["speedup"] >= 2:
        rating = "✅ Very Good! (2x+ speedup)"
        color = "GREEN"
    elif metrics["speedup"] >= 1.5:
        rating = "👍 Good! (1.5x+ speedup)"
        color = "YELLOW"
    elif metrics["speedup"] >= 1.1:
        rating = "📊 Modest improvement"
        color = "YELLOW"
    elif metrics["speedup"] >= 1.0:
        rating = "⚠️  Minimal improvement"
        color = "YELLOW"
    else:
        rating = "❌ Performance regression"
        color = "RED"

    print(f"Overall Rating: {rating}")
    print(
        f"Shimmed performance is {metrics['speedup']:.2f}x {'faster' if metrics['speedup'] >= 1 else 'slower'} than baseline"
    )

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Compare LiteLLM performance before and after Fast LiteLLM shimming"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=30,
        help="Number of benchmark iterations per version (default: 30)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of operations per iteration (default: 10)",
    )
    parser.add_argument("--output", type=str, help="Output file for JSON results")

    args = parser.parse_args()

    print("🔬 Fast LiteLLM Direct Comparison Benchmark")
    print("=" * 80)
    print(f"Test iterations per version: {args.iterations}")
    print(f"Operations per iteration: {args.batch_size}")
    print("This compares:")
    print("  • LiteLLM without Fast LiteLLM (baseline)")
    print("  • LiteLLM with Fast LiteLLM (shimmed)")
    print("=" * 80)

    # Create test data
    all_test_data = create_test_data()
    test_data = all_test_data[: args.batch_size]

    print(f"Test data: {len(test_data)} operations per iteration")
    print()

    # Run direct comparison
    baseline_run, shimmed_run = run_direct_comparison_benchmark(
        test_data, args.iterations
    )

    # Calculate metrics
    metrics = calculate_comparison_metrics(baseline_run, shimmed_run)

    # Print detailed comparison
    print_detailed_comparison(baseline_run, shimmed_run, metrics)

    # Prepare results for JSON output
    full_results = {
        "benchmark_config": {
            "iterations": args.iterations,
            "batch_size": args.batch_size,
            "test_data_size": len(test_data),
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        },
        "baseline_results": {
            "name": baseline_run.name,
            "times": baseline_run.times,
            "summary": {
                "avg": statistics.mean(baseline_run.times),
                "min": min(baseline_run.times),
                "max": max(baseline_run.times),
                "std_dev": statistics.stdev(baseline_run.times),
                "median": statistics.median(baseline_run.times),
            },
            "config": {
                "iterations": baseline_run.config.iterations,
                "batch_size": baseline_run.config.batch_size,
            },
            "metadata": baseline_run.metadata,
        },
        "shimmed_results": {
            "name": shimmed_run.name,
            "times": shimmed_run.times,
            "summary": {
                "avg": statistics.mean(shimmed_run.times),
                "min": min(shimmed_run.times),
                "max": max(shimmed_run.times),
                "std_dev": statistics.stdev(shimmed_run.times),
                "median": statistics.median(shimmed_run.times),
            },
            "config": {
                "iterations": shimmed_run.config.iterations,
                "batch_size": shimmed_run.config.batch_size,
            },
            "metadata": shimmed_run.metadata,
        },
        "comparison": metrics,
    }

    # Output JSON results if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(full_results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")

    print(f"\n✅ Direct comparison benchmark completed!")


if __name__ == "__main__":
    main()
