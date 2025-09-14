#!/usr/bin/env python3
"""
Simple concurrent benchmark to demonstrate the key difference between Rust and Python under high concurrency.
This focuses on showing the GIL bottleneck in Python.
"""

import sys
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def simple_concurrent_benchmark():
    """Simple concurrent benchmark comparing Rust and Python under high thread count."""
    print("=== Simple Concurrent Benchmark (High Thread Count) ===")
    
    # Test parameters
    concurrent_requests = 50000
    thread_count = 100  # High enough to stress the GIL
    
    print(f"Testing {concurrent_requests} requests with {thread_count} threads")
    print("This will demonstrate the GIL bottleneck in Python vs true parallelism in Rust\n")
    
    # Test Python equivalent first
    print("--- Python Equivalent (GIL-bound) ---")
    
    # Simple Python router
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
    
    # Create router and deployment
    python_router = SimplePythonRouter()
    
    deployment_data = {
        "model_name": "gpt-3.5-turbo",
        "litellm_params": {
            "model": "gpt-3.5-turbo",
            "api_base": "https://api.openai.com/v1"
        },
        "model_info": {
            "description": "GPT-3.5 Turbo model",
            "max_tokens": 4096,
            "input_cost_per_token": 0.0000015,
            "output_cost_per_token": 0.000002
        }
    }
    
    python_router.add_deployment(deployment_data)
    
    # Test request
    test_request = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello, world!"}]
    }
    
    # Warm up
    print("Warming up Python...")
    for i in range(1000):
        result = python_router.route_request("gpt-3.5-turbo", test_request)
    
    # Worker function for Python
    def python_worker(router, request_data, iterations):
        results = []
        for i in range(iterations):
            try:
                result = router.route_request("gpt-3.5-turbo", request_data)
                results.append(result is not None)
            except Exception:
                results.append(False)
        return sum(results)
    
    # Benchmark Python with high thread count
    work_per_thread = concurrent_requests // thread_count
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [
            executor.submit(python_worker, python_router, test_request, work_per_thread)
            for _ in range(thread_count)
        ]
        
        python_results = [future.result() for future in futures]
    
    python_time = time.time() - start_time
    python_successful = sum(python_results)
    python_throughput = concurrent_requests / python_time if python_time > 0 else 0
    
    print(f"✓ Python routing: {python_time:.4f}s")
    print(f"  Successful: {python_successful}/{concurrent_requests}")
    print(f"  Throughput: {python_throughput:.2f} req/sec")
    print(f"  Avg latency: {python_time/concurrent_requests*1000:.4f}ms per request")
    
    # Test Rust implementation
    print("\n--- Rust Implementation (True Parallelism) ---")
    
    try:
        import litellm_core
        from litellm_core import RoutingStrategy, RouterConfig, AdvancedRouter, Deployment
        
        # Create router config
        config = RouterConfig(
            routing_strategy=RoutingStrategy.LeastBusy,
            cooldown_time_seconds=60,
            max_retries=3,
            timeout_seconds=30
        )
        
        # Create advanced router
        rust_router = AdvancedRouter(config)
        
        # Create deployment
        litellm_params = {
            "model": "gpt-3.5-turbo",
            "api_base": "https://api.openai.com/v1"
        }
        
        model_info = {
            "description": "GPT-3.5 Turbo model",
            "max_tokens": 4096,
            "input_cost_per_token": 0.0000015,
            "output_cost_per_token": 0.000002
        }
        
        deployment = Deployment(
            "gpt-3.5-turbo",
            litellm_params,
            model_info
        )
        
        # Add deployment to router
        rust_router.add_deployment(deployment)
        
        # Warm up
        print("Warming up Rust...")
        for i in range(1000):
            result = rust_router.route_request("gpt-3.5-turbo", test_request)
        
        # Worker function for Rust
        def rust_worker(router, request_data, iterations):
            results = []
            for i in range(iterations):
                try:
                    result = router.route_request("gpt-3.5-turbo", request_data)
                    results.append(result is not None)
                except Exception:
                    results.append(False)
            return sum(results)
        
        # Benchmark Rust with high thread count
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = [
                executor.submit(rust_worker, rust_router, test_request, work_per_thread)
                for _ in range(thread_count)
            ]
            
            rust_results = [future.result() for future in futures]
        
        rust_time = time.time() - start_time
        rust_successful = sum(rust_results)
        rust_throughput = concurrent_requests / rust_time if rust_time > 0 else 0
        
        print(f"✓ Rust routing: {rust_time:.4f}s")
        print(f"  Successful: {rust_successful}/{concurrent_requests}")
        print(f"  Throughput: {rust_throughput:.2f} req/sec")
        print(f"  Avg latency: {rust_time/concurrent_requests*1000:.4f}ms per request")
        
        # Compare results
        print("\n=== Performance Comparison ===")
        print(f"Concurrent requests: {concurrent_requests}")
        print(f"Thread count: {thread_count}")
        
        if python_time > 0 and rust_time > 0:
            speedup = python_time / rust_time
            print(f"Speedup: {speedup:.2f}x faster with Rust")
            
            if speedup > 1:
                print("🎉 Rust is faster under high concurrency!")
                print("   This demonstrates the benefit of true parallelism without GIL contention.")
            else:
                print("⚠ Rust is slower in this test.")
                print("   This is likely due to PyO3 bridge overhead or other factors.")
        else:
            print("⚠ Unable to calculate speedup (zero time recorded)")
        
        print(f"\nThroughput comparison:")
        print(f"  Python: {python_throughput:.2f} req/sec")
        print(f"  Rust: {rust_throughput:.2f} req/sec")
        
        if python_throughput > 0 and rust_throughput > 0:
            throughput_ratio = rust_throughput / python_throughput
            print(f"  Throughput ratio: {throughput_ratio:.2f}x")
        
        # Test with even higher concurrency
        print("\n--- High Concurrency Stress Test ---")
        ultra_concurrent_requests = 100000
        ultra_thread_count = 200
        
        print(f"Testing {ultra_concurrent_requests} requests with {ultra_thread_count} threads")
        
        # Python high concurrency test
        work_per_thread = ultra_concurrent_requests // ultra_thread_count
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=ultra_thread_count) as executor:
            futures = [
                executor.submit(python_worker, python_router, test_request, work_per_thread)
                for _ in range(ultra_thread_count)
            ]
            
            python_results = [future.result() for future in futures]
        
        python_ultra_time = time.time() - start_time
        python_ultra_successful = sum(python_results)
        python_ultra_throughput = ultra_concurrent_requests / python_ultra_time if python_ultra_time > 0 else 0
        
        print(f"✓ Python high concurrency: {python_ultra_time:.4f}s")
        print(f"  Successful: {python_ultra_successful}/{ultra_concurrent_requests}")
        print(f"  Throughput: {python_ultra_throughput:.2f} req/sec")
        
        # Rust high concurrency test
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=ultra_thread_count) as executor:
            futures = [
                executor.submit(rust_worker, rust_router, test_request, work_per_thread)
                for _ in range(ultra_thread_count)
            ]
            
            rust_results = [future.result() for future in futures]
        
        rust_ultra_time = time.time() - start_time
        rust_ultra_successful = sum(rust_results)
        rust_ultra_throughput = ultra_concurrent_requests / rust_ultra_time if rust_ultra_time > 0 else 0
        
        print(f"✓ Rust high concurrency: {rust_ultra_time:.4f}s")
        print(f"  Successful: {rust_ultra_successful}/{ultra_concurrent_requests}")
        print(f"  Throughput: {rust_ultra_throughput:.2f} req/sec")
        
        # High concurrency comparison
        print("\n=== High Concurrency Comparison ===")
        if python_ultra_time > 0 and rust_ultra_time > 0:
            ultra_speedup = python_ultra_time / rust_ultra_time
            print(f"Ultra high concurrency speedup: {ultra_speedup:.2f}x")
            
            if ultra_speedup > 1:
                print("🎉 Rust shows greater benefits under ultra-high concurrency!")
                print("   This demonstrates the true advantage of avoiding GIL contention.")
            else:
                print("⚠ Rust still slower under ultra-high concurrency.")
                print("   PyO3 bridge overhead may be dominating.")
        
        print(f"\nUltra-high concurrency throughput:")
        print(f"  Python: {python_ultra_throughput:.2f} req/sec")
        print(f"  Rust: {rust_ultra_throughput:.2f} req/sec")
        
        if python_ultra_throughput > 0 and rust_ultra_throughput > 0:
            ultra_throughput_ratio = rust_ultra_throughput / python_ultra_throughput
            print(f"  Throughput ratio: {ultra_throughput_ratio:.2f}x")
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_core: {e}")
        print("This is expected if the module isn't properly built or in the Python path")
        return False
    except Exception as e:
        print(f"✗ Error in Rust benchmark: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("LiteLLM Rust vs Python Concurrent Routing Performance Test\n")
    print("This test demonstrates the GIL bottleneck in Python vs true parallelism in Rust.\n")
    
    success = simple_concurrent_benchmark()
    
    if success:
        print("\n🎉 Concurrent routing performance test completed!")
        sys.exit(0)
    else:
        print("\n💥 Concurrent routing performance test failed!")
        sys.exit(1)