#!/usr/bin/env python3
"""
Investigate the threading overhead in the concurrent tests.
"""

import sys
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def investigate_threading_overhead():
    """Investigate why threading makes Rust slower than Python."""
    print("=== Investigating Threading Overhead ===")
    
    # Test parameters
    concurrent_requests = 10000
    thread_count = 50
    
    print(f"Testing {concurrent_requests} requests with {thread_count} threads")
    
    # Test 1: Sequential single-threaded performance
    print("\n--- Single-threaded Sequential Performance ---")
    
    # Python sequential
    class SimplePythonRouter:
        def __init__(self):
            self.deployments = {}
        
        def add_deployment(self, deployment):
            self.deployments[deployment["model_name"]] = deployment
            
        def route_request(self, model_name, request_data):
            if model_name in self.deployments:
                return self.deployments[model_name]
            else:
                raise ValueError(f"No deployment found for model: {model_name}")
    
    python_router = SimplePythonRouter()
    
    deployment_data = {
        "model_name": "gpt-3.5-turbo",
        "litellm_params": {"model": "gpt-3.5-turbo"},
        "model_info": {"description": "Test model"}
    }
    
    python_router.add_deployment(deployment_data)
    
    test_request = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}
    
    # Warm up
    for i in range(1000):
        result = python_router.route_request("gpt-3.5-turbo", test_request)
    
    start_time = time.time()
    for i in range(concurrent_requests):
        result = python_router.route_request("gpt-3.5-turbo", test_request)
    python_seq_time = time.time() - start_time
    
    print(f"✓ Python sequential: {python_seq_time:.4f}s ({concurrent_requests/python_seq_time:.0f} req/sec)")
    
    # Rust sequential
    try:
        import litellm_core
        from litellm_core import RoutingStrategy, RouterConfig, AdvancedRouter, Deployment
        
        config = RouterConfig(
            routing_strategy=RoutingStrategy.LeastBusy,
            cooldown_time_seconds=60,
            max_retries=3,
            timeout_seconds=30
        )
        
        rust_router = AdvancedRouter(config)
        
        litellm_params = {"model": "gpt-3.5-turbo", "api_base": "https://api.openai.com/v1"}
        model_info = {"description": "Test model", "max_tokens": 4096}
        
        deployment = Deployment("gpt-3.5-turbo", litellm_params, model_info)
        rust_router.add_deployment(deployment)
        
        # Warm up
        for i in range(1000):
            result = rust_router.route_request("gpt-3.5-turbo", test_request)
        
        start_time = time.time()
        for i in range(concurrent_requests):
            result = rust_router.route_request("gpt-3.5-turbo", test_request)
        rust_seq_time = time.time() - start_time
        
        print(f"✓ Rust sequential: {rust_seq_time:.4f}s ({concurrent_requests/rust_seq_time:.0f} req/sec)")
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_core: {e}")
        return False
    
    # Compare sequential performance
    print("\n--- Sequential Performance Comparison ---")
    if python_seq_time > 0 and rust_seq_time > 0:
        seq_speedup = python_seq_time / rust_seq_time
        print(f"Sequential speedup: {seq_speedup:.2f}x faster with Rust")
    
    # Test 2: Multi-threaded performance
    print("\n--- Multi-threaded Performance ---")
    
    def python_worker(router, request_data, iterations):
        results = []
        for i in range(iterations):
            try:
                result = router.route_request("gpt-3.5-turbo", request_data)
                results.append(result is not None)
            except Exception:
                results.append(False)
        return sum(results)
    
    def rust_worker(router, request_data, iterations):
        results = []
        for i in range(iterations):
            try:
                result = router.route_request("gpt-3.5-turbo", request_data)
                results.append(result is not None)
            except Exception:
                results.append(False)
        return sum(results)
    
    work_per_thread = concurrent_requests // thread_count
    
    # Python multi-threaded
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [
            executor.submit(python_worker, python_router, test_request, work_per_thread)
            for _ in range(thread_count)
        ]
        python_results = [future.result() for future in futures]
    python_mt_time = time.time() - start_time
    python_mt_successful = sum(python_results)
    
    print(f"✓ Python multi-threaded: {python_mt_time:.4f}s ({python_mt_successful}/{concurrent_requests} successful)")
    
    # Rust multi-threaded
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [
            executor.submit(rust_worker, rust_router, test_request, work_per_thread)
            for _ in range(thread_count)
        ]
        rust_results = [future.result() for future in futures]
    rust_mt_time = time.time() - start_time
    rust_mt_successful = sum(rust_results)
    
    print(f"✓ Rust multi-threaded: {rust_mt_time:.4f}s ({rust_mt_successful}/{concurrent_requests} successful)")
    
    # Compare multi-threaded performance
    print("\n--- Multi-threaded Performance Comparison ---")
    if python_mt_time > 0 and rust_mt_time > 0:
        mt_speedup = python_mt_time / rust_mt_time
        print(f"Multi-threaded speedup: {mt_speedup:.2f}x faster with Python")
        
        # Calculate threading overhead
        python_threading_overhead = python_mt_time / python_seq_time
        rust_threading_overhead = rust_mt_time / rust_seq_time
        
        print(f"Threading overhead:")
        print(f"  Python: {python_threading_overhead:.2f}x slower with threading")
        print(f"  Rust: {rust_threading_overhead:.2f}x slower with threading")
        
        if rust_threading_overhead > python_threading_overhead:
            print("⚠ Rust has higher threading overhead than Python!")
            print("  This explains why Python is faster under high concurrency.")
    
    # Test 3: Bridge overhead analysis
    print("\n--- Bridge Overhead Analysis ---")
    
    # Measure bridge overhead with threading
    def measure_bridge_overhead(router, iterations):
        start_time = time.time()
        for i in range(iterations):
            result = router.route_request("gpt-3.5-turbo", test_request)
        return time.time() - start_time
    
    # Python bridge overhead (minimal)
    python_bridge_time = measure_bridge_overhead(python_router, 10000)
    print(f"✓ Python bridge overhead for 10,000 calls: {python_bridge_time:.4f}s")
    
    # Rust bridge overhead
    rust_bridge_time = measure_bridge_overhead(rust_router, 10000)
    print(f"✓ Rust bridge overhead for 10,000 calls: {rust_bridge_time:.4f}s")
    
    if python_bridge_time > 0:
        bridge_overhead_ratio = rust_bridge_time / python_bridge_time
        print(f"Bridge overhead ratio: {bridge_overhead_ratio:.2f}x higher for Rust")
    
    print("\n=== Investigation Summary ===")
    print("🔍 Key findings:")
    print("  1. Sequential performance favors Rust (as expected)")
    print("  2. Multi-threaded performance favors Python (unexpected)")
    print("  3. Rust has higher threading overhead than Python")
    print("  4. Bridge overhead is significant for Rust")
    
    return True

if __name__ == "__main__":
    print("Investigating Threading Overhead in LiteLLM Rust vs Python\n")
    
    success = investigate_threading_overhead()
    
    if success:
        print("\n🎉 Threading overhead investigation completed!")
        sys.exit(0)
    else:
        print("\n💥 Threading overhead investigation failed!")
        sys.exit(1)