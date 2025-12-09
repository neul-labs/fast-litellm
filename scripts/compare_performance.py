#!/usr/bin/env python3
"""
Compare LiteLLM test performance with and without Fast LiteLLM acceleration.

This script runs the same tests twice:
1. Without Fast LiteLLM (baseline)
2. With Fast LiteLLM (accelerated)

Then compares execution time, results, and generates a report.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Colors:
    """ANSI color codes for terminal output"""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text:^70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")


def print_section(text: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'-'*len(text)}{Colors.ENDC}")


def run_tests(
    test_path: str, with_acceleration: bool, litellm_dir: Path
) -> Tuple[int, float, Dict]:
    """Run tests and return exit code, duration, and stats"""
    print_section(
        f"Running tests {'WITH' if with_acceleration else 'WITHOUT'} Fast LiteLLM acceleration"
    )

    # Prepare environment
    env = subprocess.os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    # Create pytest command
    pytest_args = [
        "pytest",
        str(test_path),
        "-v",
        "--tb=short",
        "--disable-warnings",
        "-x",  # Stop on first failure
        "--json-report",
        "--json-report-file=.test_report.json",
    ]

    # Create conftest that either enables or disables fast_litellm
    conftest_content = f"""
import sys
import pytest

{'import fast_litellm' if with_acceleration else '# Fast LiteLLM disabled for baseline'}

def pytest_configure(config):
    marker = "{'ACCELERATED' if with_acceleration else 'BASELINE'}"
    print(f"\\n{marker} TEST RUN\\n")
"""

    conftest_path = litellm_dir / "conftest.py"
    conftest_path.write_text(conftest_content)

    # Run tests
    start_time = time.time()
    try:
        result = subprocess.run(
            pytest_args, cwd=str(litellm_dir), env=env, capture_output=True, text=True
        )
        exit_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except Exception as e:
        print(f"{Colors.RED}❌ Error running tests: {e}{Colors.ENDC}")
        exit_code = -1
        stdout = ""
        stderr = str(e)

    duration = time.time() - start_time

    # Parse results
    report_file = litellm_dir / ".test_report.json"
    stats = {}
    if report_file.exists():
        try:
            with open(report_file) as f:
                data = json.load(f)
                stats = data.get("summary", {})
        except:
            pass
        report_file.unlink()

    # Cleanup conftest
    if conftest_path.exists():
        conftest_path.unlink()

    # Print results
    status = f"{Colors.GREEN}✅ PASSED" if exit_code == 0 else f"{Colors.RED}❌ FAILED"
    print(f"\n{status}{Colors.ENDC}")
    print(f"Duration: {duration:.2f}s")
    if stats:
        print(
            f"Tests: {stats.get('total', 0)} total, "
            f"{stats.get('passed', 0)} passed, "
            f"{stats.get('failed', 0)} failed"
        )

    return exit_code, duration, stats


def print_comparison(baseline: Tuple, accelerated: Tuple):
    """Print comparison between baseline and accelerated runs"""
    baseline_exit, baseline_time, baseline_stats = baseline
    accel_exit, accel_time, accel_stats = accelerated

    print_header("PERFORMANCE COMPARISON")

    # Execution time comparison
    speedup = baseline_time / accel_time if accel_time > 0 else 0
    improvement = (
        ((baseline_time - accel_time) / baseline_time * 100) if baseline_time > 0 else 0
    )

    print(f"{'Metric':<30} {'Baseline':<15} {'Accelerated':<15} {'Improvement':<15}")
    print(f"{'-'*30} {'-'*15} {'-'*15} {'-'*15}")

    print(
        f"{'Execution Time':<30} {baseline_time:>12.2f}s  {accel_time:>12.2f}s  ",
        end="",
    )
    if speedup > 1:
        print(f"{Colors.GREEN}{speedup:>10.2f}x faster{Colors.ENDC}")
    elif speedup < 1 and speedup > 0:
        print(f"{Colors.RED}{1/speedup:>10.2f}x slower{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}N/A{Colors.ENDC}")

    # Test results comparison
    baseline_passed = baseline_stats.get("passed", 0)
    accel_passed = accel_stats.get("passed", 0)

    print(f"{'Tests Passed':<30} {baseline_passed:>15} {accel_passed:>15}  ", end="")
    if accel_passed == baseline_passed:
        print(f"{Colors.GREEN}✓ Same{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Different{Colors.ENDC}")

    # Exit codes
    print(f"{'Exit Code':<30} {baseline_exit:>15} {accel_exit:>15}  ", end="")
    if accel_exit == baseline_exit == 0:
        print(f"{Colors.GREEN}✓ Both passed{Colors.ENDC}")
    elif accel_exit == baseline_exit:
        print(f"{Colors.YELLOW}⚠ Both failed{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Different{Colors.ENDC}")

    # Summary
    print_section("Summary")
    if accel_exit == 0 and baseline_exit == 0:
        if speedup > 1:
            print(
                f"{Colors.GREEN}✅ Fast LiteLLM provides {speedup:.2f}x speedup without breaking tests!{Colors.ENDC}"
            )
        else:
            print(
                f"{Colors.YELLOW}⚠️  Tests passed but no speedup detected (might need more iterations){Colors.ENDC}"
            )
    elif accel_exit == baseline_exit != 0:
        print(
            f"{Colors.YELLOW}⚠️  Both runs failed - might be LiteLLM test issues, not acceleration{Colors.ENDC}"
        )
    else:
        print(
            f"{Colors.RED}❌ Fast LiteLLM acceleration caused test failures!{Colors.ENDC}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Compare LiteLLM test performance with/without Fast LiteLLM"
    )
    parser.add_argument(
        "test_path",
        nargs="?",
        default="tests/",
        help="Path to LiteLLM tests to run (default: tests/)",
    )
    parser.add_argument(
        "--litellm-dir",
        type=Path,
        default=None,
        help="Path to LiteLLM directory (default: .litellm)",
    )
    parser.add_argument(
        "--skip-baseline",
        action="store_true",
        help="Skip baseline run (only run with acceleration)",
    )

    args = parser.parse_args()

    # Check if we're in a virtual environment
    if not subprocess.os.environ.get("VIRTUAL_ENV"):
        # Check if .venv exists
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        venv_dir = project_root / ".venv"

        if venv_dir.exists():
            print(
                f"{Colors.YELLOW}⚠️  Virtual environment exists but not activated{Colors.ENDC}"
            )
            print(f"\nPlease activate it:")
            print(f"  source .venv/bin/activate")
            print(f"  {' '.join(subprocess.sys.argv)}")
            sys.exit(1)
        else:
            print(f"{Colors.YELLOW}⚠️  No virtual environment detected{Colors.ENDC}")
            print(f"\nPlease run setup first:")
            print(f"  ./scripts/setup_litellm.sh")
            sys.exit(1)

    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    litellm_dir = args.litellm_dir or project_root / ".litellm"

    # Check if LiteLLM exists
    if not litellm_dir.exists():
        print(f"{Colors.RED}❌ LiteLLM not found at: {litellm_dir}{Colors.ENDC}")
        print(f"\nPlease run setup first:")
        print(f"  ./scripts/setup_litellm.sh")
        sys.exit(1)

    print_header("Fast LiteLLM Performance Comparison")
    print(f"LiteLLM Directory: {litellm_dir}")
    print(f"Test Path: {args.test_path}")

    # Run baseline tests
    if not args.skip_baseline:
        baseline = run_tests(
            args.test_path, with_acceleration=False, litellm_dir=litellm_dir
        )
    else:
        print_section("Skipping baseline run")
        baseline = (0, 0, {})

    # Run accelerated tests
    accelerated = run_tests(
        args.test_path, with_acceleration=True, litellm_dir=litellm_dir
    )

    # Compare results
    if not args.skip_baseline:
        print_comparison(baseline, accelerated)
    else:
        _, duration, stats = accelerated
        print_section("Accelerated Test Results")
        print(f"Duration: {duration:.2f}s")
        print(f"Exit Code: {accelerated[0]}")
        if stats:
            print(
                f"Tests: {stats.get('total', 0)} total, "
                f"{stats.get('passed', 0)} passed, "
                f"{stats.get('failed', 0)} failed"
            )

    # Exit with appropriate code
    sys.exit(accelerated[0])


if __name__ == "__main__":
    main()
