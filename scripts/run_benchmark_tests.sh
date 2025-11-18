#!/bin/bash
# Run LiteLLM benchmarks with Fast LiteLLM acceleration enabled
# This validates performance improvements while ensuring functionality remains intact

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LITELLM_DIR="${PROJECT_ROOT}/.litellm"

echo "============================================="
echo "Fast LiteLLM - Benchmark Test Runner"
echo "============================================="
echo ""

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    # Check if .venv exists
    if [ -d "$PROJECT_ROOT/.venv" ]; then
        echo "⚠️  Virtual environment detected but not activated"
        echo ""
        echo "Activating virtual environment..."
        source "$PROJECT_ROOT/.venv/bin/activate"
        echo "✅ Virtual environment activated"
        echo ""
    else
        echo "⚠️  No virtual environment detected"
        echo ""
        echo "Please run setup first:"
        echo "  ./scripts/setup_litellm.sh"
        echo ""
        echo "Or activate your virtual environment:"
        echo "  source .venv/bin/activate"
        exit 1
    fi
fi

# Check if LiteLLM is set up
if [ ! -d "$LITELLM_DIR" ]; then
    echo "❌ LiteLLM not found at: $LITELLM_DIR"
    echo ""
    echo "Please run setup first:"
    echo "  ./scripts/setup_litellm.sh"
    exit 1
fi

# Check if pytest and pytest-benchmark are installed
echo "🔍 Checking for benchmark dependencies..."
if ! python -c "import pytest" &> /dev/null; then
    echo "📦 Installing pytest..."
    pip install pytest pytest-asyncio || {
        echo "❌ Failed to install pytest"
        exit 1
    }
fi

if ! python -c "import pytest_benchmark" &> /dev/null; then
    echo "📦 Installing pytest-benchmark..."
    pip install pytest-benchmark || {
        echo "❌ Failed to install pytest-benchmark"
        exit 1
    }
fi

# Check if Fast LiteLLM is built
echo "🔍 Checking Fast LiteLLM build..."
if ! python -c "import fast_litellm._rust" 2>/dev/null; then
    echo "⚠️  Fast LiteLLM Rust extensions not found. Building..."

    # Check if maturin is installed
    if ! command -v maturin &> /dev/null; then
        echo "📦 Installing maturin..."
        pip install maturin || {
            echo "❌ Failed to install maturin"
            exit 1
        }
    fi

    cd "$PROJECT_ROOT"
    maturin develop || {
        echo "❌ Failed to build Fast LiteLLM"
        echo ""
        echo "This could be due to:"
        echo "  • Missing Rust toolchain (install from https://rustup.rs)"
        echo "  • Missing system dependencies"
        echo ""
        echo "To install Rust:"
        echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
        exit 1
    }
fi

echo "✅ Fast LiteLLM is built and ready"
echo ""

# Function to parse command-line arguments
parse_args() {
    local test_path="tests/"
    local benchmark_mode="normal"  # normal, compare, profile
    local benchmark_min_rounds=5
    local benchmark_max_time=1.0
    local additional_args=()

    while [[ $# -gt 0 ]]; do
        case $1 in
            --benchmark-mode)
                benchmark_mode="$2"
                shift 2
                ;;
            --benchmark-min-rounds)
                benchmark_min_rounds="$2"
                shift 2
                ;;
            --benchmark-max-time)
                benchmark_max_time="$2"
                shift 2
                ;;
            --test-path)
                test_path="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                additional_args+=("$1")
                shift
                ;;
        esac
    done

    # Remaining arguments can be passed to pytest
    for arg in "${additional_args[@]}"; do
        # If not specific to this script, pass to pytest
        if [[ ! "$arg" =~ ^--benchmark ]]; then
            test_path="$arg"
            break
        fi
    done

    echo "$test_path|$benchmark_mode|$benchmark_min_rounds|$benchmark_max_time"
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS] [TEST_PATH]"
    echo ""
    echo "Run LiteLLM benchmarks with Fast LiteLLM acceleration."
    echo ""
    echo "Options:"
    echo "  --benchmark-mode MODE     Benchmark mode: normal, compare, profile"
    echo "  --benchmark-min-rounds N  Minimum number of benchmark rounds (default: 5)"
    echo "  --benchmark-max-time S    Maximum time per benchmark in seconds (default: 1.0)"
    echo "  --test-path PATH          Test path to run (default: tests/)"
    echo "  --help, -h               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                      # Run default benchmarks"
    echo "  $0 --benchmark-mode compare             # Compare with baseline"
    echo "  $0 tests/unit/test_embedding.py         # Run specific test file"
    echo "  $0 --benchmark-min-rounds 10 tests/     # Run with custom rounds"
}

# Parse arguments
args_str=$(parse_args "$@")
IFS='|' read -r TEST_PATH BENCHMARK_MODE BENCHMARK_MIN_ROUNDS BENCHMARK_MAX_TIME <<< "$args_str"

# Get additional pytest arguments
PYTEST_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --benchmark-mode|--benchmark-min-rounds|--benchmark-max-time|--test-path|--help|-h)
            shift 2
            ;;
        *)
            PYTEST_ARGS+=("$1")
            shift
            ;;
    esac
done

echo "📋 Benchmark Configuration:"
echo "  LiteLLM Path: $LITELLM_DIR"
echo "  Test Path: $TEST_PATH"
echo "  Benchmark Mode: $BENCHMARK_MODE"
echo "  Min Rounds: $BENCHMARK_MIN_ROUNDS"
echo "  Max Time: $BENCHMARK_MAX_TIME"
echo "  Fast LiteLLM: $(python -c "import fast_litellm; print(fast_litellm.__version__)")"
echo "  LiteLLM: $(cd "$LITELLM_DIR" && python -c "import litellm; print(litellm.__version__)" 2>/dev/null || echo "unknown")"
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "  Virtual Env: $VIRTUAL_ENV"
fi
echo ""

# Ensure fast_litellm is in PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Change to LiteLLM directory
cd "$LITELLM_DIR"

# Create a conftest.py to enable fast_litellm and configure benchmarks
cat > conftest.py << EOF
"""
Pytest configuration to enable Fast LiteLLM acceleration and benchmarking
"""
import sys
import pytest
import json
import os

# Import fast_litellm before any tests run
import fast_litellm

def pytest_configure(config):
    """Configure pytest with Fast LiteLLM and benchmark settings"""
    print("\n" + "="*60)
    print("Fast LiteLLM Benchmark Test Session")
    print("="*60)
    print(f"Fast LiteLLM Version: {fast_litellm.__version__}")
    print(f"Rust Acceleration: {fast_litellm.RUST_ACCELERATION_AVAILABLE}")
    print(f"Benchmark Mode: ${BENCHMARK_MODE}")

    if fast_litellm.RUST_ACCELERATION_AVAILABLE:
        try:
            status = fast_litellm.get_patch_status()
            print(f"Patches Applied: {status.get('applied', False)}")
            
            # Enable performance monitoring
            fast_litellm.record_performance("benchmark_init", "setup", 0.0, True)
        except Exception as e:
            print(f"Warning: Could not get patch status: {e}")
    print("="*60 + "\n")

def pytest_sessionfinish(session, exitstatus):
    """Print performance stats and benchmark results after tests complete"""
    try:
        import fast_litellm
        if fast_litellm.RUST_ACCELERATION_AVAILABLE:
            print("\n" + "="*60)
            print("Fast LiteLLM Performance Summary")
            print("="*60)
            try:
                stats = fast_litellm.get_performance_stats()
                print(f"Performance data collected: {len(stats)} components")

                # Export detailed performance data
                perf_data = fast_litellm.export_performance_data(None, "json")
                with open("fast_litellm_benchmark_results.json", "w") as f:
                    f.write(perf_data)
                print(f"Performance data exported to: fast_litellm_benchmark_results.json")

                recommendations = fast_litellm.get_recommendations()
                if recommendations:
                    print("\nOptimization Recommendations:")
                    for i, rec in enumerate(recommendations[:5]):  # Show top 5
                        print(f"  • {rec.get('message', rec)}")

                # Show feature status
                feature_status = fast_litellm.get_feature_status()
                print(f"\nActive Features: {sum(1 for name, status in feature_status['features'].items() if status['state'] != 'disabled')}")
                
            except Exception as e:
                print(f"Could not retrieve performance stats: {e}")
            print("="*60 + "\n")
    except Exception as e:
        print(f"Could not print performance summary: {e}")

# Add benchmark configuration
def pytest_benchmark_update_json(config, benchmarks, output_json):
    # Add Fast LiteLLM metadata to benchmark output
    output_json['metadata'] = {
        'fast_litellm_version': fast_litellm.__version__,
        'rust_available': fast_litellm.RUST_ACCELERATION_AVAILABLE,
        'benchmark_mode': '${BENCHMARK_MODE}',
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }
EOF

# Function to run baseline test (without acceleration)
run_baseline() {
    echo "⏱️  Running baseline test (without Fast LiteLLM acceleration)..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Create temp conftest for baseline
    cat > baseline_conftest.py << 'EOF'
"""
Pytest configuration for baseline test (without Fast LiteLLM)
"""
import sys
import os

# Temporarily disable Fast LiteLLM by setting environment variable
os.environ['LITELLM_RUST_DISABLE_ALL'] = 'true'

def pytest_configure(config):
    """Configure pytest without Fast LiteLLM acceleration"""
    print("\n" + "="*60)
    print("LiteLLM Baseline Test Session (without Fast LiteLLM)")
    print("="*60)
    try:
        import fast_litellm
        print(f"Fast LiteLLM Version: {fast_litellm.__version__}")
        print(f"Rust Acceleration Available: {fast_litellm.RUST_ACCELERATION_AVAILABLE}")
        print(f"Fast LiteLLM acceleration: {'DISABLED' if fast_litellm.RUST_ACCELERATION_AVAILABLE else 'NOT AVAILABLE'}")
    except ImportError:
        print("Fast LiteLLM: Not available")
    print("="*60 + "\n")
EOF

    # Run baseline test
    export LITELLM_RUST_DISABLE_ALL=true
    python -m pytest "$TEST_PATH" \
        -v \
        --tb=short \
        --disable-warnings \
        --import-mode=importlib \
        --benchmark-only \
        --benchmark-min-rounds=${BENCHMARK_MIN_ROUNDS} \
        --benchmark-max-time=${BENCHMARK_MAX_TIME} \
        --benchmark-skip \
        --benchmark-json=baseline_benchmark_results.json \
        "${PYTEST_ARGS[@]}" || {
            local exit_code=$?
            unset LITELLM_RUST_DISABLE_ALL
            rm -f baseline_conftest.py
            return $exit_code
        }
    
    unset LITELLM_RUST_DISABLE_ALL
    rm -f baseline_conftest.py
    
    # Rename results file
    if [ -f baseline_benchmark_results.json ]; then
        mv baseline_benchmark_results.json baseline_results.json
        echo "✅ Baseline results saved to: baseline_results.json"
    fi
}

# Function to run accelerated test
run_accelerated() {
    echo "🚀 Running accelerated test (with Fast LiteLLM acceleration)..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Verify imports work from this directory
    echo "🔍 Verifying imports..."
    python -c "import sys; sys.path.insert(0, '$PROJECT_ROOT'); import fast_litellm; print(f'✅ fast_litellm {fast_litellm.__version__} accessible')" || {
        echo "❌ Cannot import fast_litellm"
        echo ""
        echo "PYTHONPATH: $PYTHONPATH"
        echo "Python path:"
        python -c "import sys; print('\n'.join(sys.path))"
        exit 1
    }

    echo ""
    
    # Run benchmark test
    python -m pytest "$TEST_PATH" \
        -v \
        --tb=short \
        --disable-warnings \
        --import-mode=importlib \
        --benchmark-only \
        --benchmark-min-rounds=${BENCHMARK_MIN_ROUNDS} \
        --benchmark-max-time=${BENCHMARK_MAX_TIME} \
        --benchmark-json=accelerated_benchmark_results.json \
        "${PYTEST_ARGS[@]}"
    
    local exit_code=$?
    
    # Rename results file
    if [ -f accelerated_benchmark_results.json ]; then
        mv accelerated_benchmark_results.json accelerated_results.json
        echo "✅ Accelerated results saved to: accelerated_results.json"
    fi
    
    return $exit_code
}

# Function to run comparison
run_comparison() {
    echo "📊 Comparison Mode: Running both baseline and accelerated tests..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # First run baseline
    run_baseline || {
        echo "❌ Baseline test failed, cannot proceed with comparison"
        # Still cleanup and continue with accelerated test
    }
    
    # Then run accelerated
    run_accelerated || {
        echo "❌ Accelerated test failed"
        return 1
    }
    
    # Generate comparison if both exist
    if [ -f baseline_results.json ] && [ -f accelerated_results.json ]; then
        echo ""
        echo "📈 Generating performance comparison..."
        
        python -c "
import json
import sys

def safe_load_json(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        return None

baseline = safe_load_json('baseline_results.json')
accelerated = safe_load_json('accelerated_results.json')

if baseline and accelerated:
    print('Performance Comparison Results:')
    print('=' * 60)
    
    baseline_benchmarks = baseline.get('benchmarks', [])
    accelerated_benchmarks = accelerated.get('benchmarks', [])
    
    print(f'Baseline benchmarks: {len(baseline_benchmarks)}')
    print(f'Accelerated benchmarks: {len(accelerated_benchmarks)}')
    
    # Simple comparison of average times (if available)
    if baseline_benchmarks and accelerated_benchmarks:
        baseline_time = sum(b.get('stats', {}).get('mean', 0) for b in baseline_benchmarks) / len(baseline_benchmarks)
        accelerated_time = sum(b.get('stats', {}).get('mean', 0) for b in accelerated_benchmarks) / len(accelerated_benchmarks)
        
        if baseline_time > 0 and accelerated_time > 0:
            speedup = baseline_time / accelerated_time
            improvement = ((baseline_time - accelerated_time) / baseline_time * 100)
            
            print(f'Average baseline time: {baseline_time:.6f}s')
            print(f'Average accelerated time: {accelerated_time:.6f}s')
            print(f'Speedup: {speedup:.2f}x')
            print(f'Improvement: {improvement:.1f}%')
    
    print('Detailed results saved to:')
    print('  - baseline_results.json')
    print('  - accelerated_results.json')
else:
    print('❌ Could not load both benchmark results for comparison')
"
    fi
}

# Function to run profiling mode
run_profile() {
    echo "🔍 Profile Mode: Detailed performance analysis..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Enable all profiling-related features
    export LITELLM_RUST_PERFORMANCE_MONITORING=enabled
    export LITELLM_RUST_BATCH_TOKEN_COUNTING=canary:100
    
    run_accelerated || {
        local exit_code=$?
        unset LITELLM_RUST_PERFORMANCE_MONITORING
        unset LITELLM_RUST_BATCH_TOKEN_COUNTING
        return $exit_code
    }
    
    unset LITELLM_RUST_PERFORMANCE_MONITORING
    unset LITELLM_RUST_BATCH_TOKEN_COUNTING
    
    # Run additional performance analysis
    echo ""
    echo "⚙️  Running additional performance analysis..."
    python -c "
import json
import fast_litellm

print('Fast LiteLLM Performance Analysis:')
print('=' * 40)

# Get feature status
status = fast_litellm.get_feature_status()
print(f'Active features: {status[\"global_status\"][\"enabled_features\"]}/{status[\"global_status\"][\"total_features\"]}')

# Get performance stats
perf_stats = fast_litellm.get_performance_stats()
print(f'Performance components tracked: {len(perf_stats)}')

# Export detailed data
detailed_data = fast_litellm.export_performance_data(None, 'json')
print('Detailed performance data exported to: fast_litellm_detailed.json')

# Save to file
with open('fast_litellm_detailed.json', 'w') as f:
    f.write(detailed_data)

# Get recommendations
recommendations = fast_litellm.get_recommendations()
print(f'Optimization recommendations available: {len(recommendations)}')
"
}

# Execute based on benchmark mode
case "$BENCHMARK_MODE" in
    "compare")
        run_comparison
        ;;
    "profile")
        run_profile
        ;;
    "normal")
        run_accelerated
        ;;
    *)
        echo "Unknown benchmark mode: $BENCHMARK_MODE"
        echo "Supported modes: normal, compare, profile"
        exit 1
        ;;
esac

EXIT_CODE=$?

# Check for any errors and provide summary
if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Benchmark tests completed successfully!"
    echo ""
    echo "Results:"
    if [ -f accelerated_results.json ]; then
        echo "  - Accelerated results: accelerated_results.json"
    fi
    if [ -f baseline_results.json ]; then
        echo "  - Baseline results: baseline_results.json"
    fi
    if [ -f fast_litellm_benchmark_results.json ]; then
        echo "  - Fast LiteLLM performance data: fast_litellm_benchmark_results.json"
    fi
    echo ""
    echo "Next steps:"
    echo "  - Analyze performance data files for detailed metrics"
    echo "  - Compare results between baseline and accelerated runs"
    echo "  - Check optimization recommendations from Fast LiteLLM"
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Benchmark tests failed with exit code: $EXIT_CODE"
    echo ""
    echo "This could indicate:"
    echo "  • Fast LiteLLM performance optimization issues"
    echo "  • Benchmark configuration problems"
    echo "  • Test environment issues"
    echo ""
    echo "To debug:"
    echo "  1. Check benchmark configuration parameters"
    echo "  2. Ensure LiteLLM tests are compatible with benchmarking"
    echo "  3. Verify Fast LiteLLM installation and build"
fi

# Cleanup
rm -f conftest.py

exit $EXIT_CODE