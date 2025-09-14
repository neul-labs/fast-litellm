#!/usr/bin/env python3
"""
Concurrent performance benchmark to compare Rust vs Python routing performance under high concurrency.
This test will demonstrate the GIL bottleneck in Python vs true parallelism in Rust.
"""

import sys
import os
import time
import json
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def benchmark_concurrent_rust_routing():
    """Benchmark the Rust routing implementation under high concurrency."""
    print("=== Benchmarking Rust Routing Under High Concurrency ===")
    
    try:
        # Import the Rust module
        import litellm_core
        
        print("✓ Successfully imported litellm_core")
        
        # Create router and deployment
        from litellm_core import RoutingStrategy, RouterConfig, AdvancedRouter, Deployment
        
        # Create router config
        config = RouterConfig(
            routing_strategy=RoutingStrategy.LeastBusy,
            cooldown_time_seconds=60,
            max_retries=3,
            timeout_seconds=30
        )
        
        # Create advanced router
        router = AdvancedRouter(config)
        
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
            "test-model",
            litellm_params,
            model_info
        )
        
        # Add deployment to router
        router.add_deployment(deployment)
        
        # Test routing with Python dict
        test_request = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello, world! This is a test message for concurrent routing."}]
        }
        
        # Warm up
        print("Warming up...")
        for i in range(1000):
            result = router.route_request("test-model", test_request)
        
        # Concurrent benchmarking
        concurrent_requests = 10000
        thread_count = 50  # High concurrency to stress test GIL
        
        print(f"Benchmarking {concurrent_requests} concurrent routing operations with {thread_count} threads...")
        
        def worker_rust(router_instance, request_data, iterations):
            """Worker function for Rust routing."""
            results = []
            for i in range(iterations):
                try:
                    result = router_instance.route_request("test-model", request_data)
                    results.append(result)
                except Exception as e:
                    results.append(None)
            return len([r for r in results if r is not None])
        
        # Test with ThreadPoolExecutor (GIL-bound)
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            # Distribute work among threads
            work_per_thread = concurrent_requests // thread_count
            futures = [
                executor.submit(worker_rust, router, test_request, work_per_thread)
                for _ in range(thread_count)
            ]
            
            # Wait for all threads to complete
            results = [future.result() for future in futures]
        
        rust_thread_time = time.time() - start_time
        total_successful = sum(results)
        
        print(f"✓ Rust routing with {thread_count} threads: {rust_thread_time:.4f}s")
        print(f"  Successful requests: {total_successful}/{concurrent_requests}")
        print(f"  Throughput: {concurrent_requests/rust_thread_time:.2f} req/sec")
        print(f"  Avg latency: {rust_thread_time/concurrent_requests*1000:.4f}ms per request")
        
        # Get router statistics
        stats = router.get_stats()
        print(f"  Router statistics: {stats}")
        
        return rust_thread_time, total_successful, concurrent_requests
        
    except Exception as e:
        print(f"✗ Error benchmarking concurrent Rust routing: {e}")
        import traceback
        traceback.print_exc()
        return None, 0, 0

def benchmark_concurrent_python_routing():
    """Benchmark Python routing implementation under high concurrency."""
    print("\n=== Benchmarking Python Routing Under High Concurrency ===")
    
    # Simple Python equivalent
    class SimplePythonRouter:
        def __init__(self):
            self.deployments = {}
        
        def add_deployment(self, deployment):
            self.deployments[deployment.model_name] = deployment
            
        def route_request(self, model_name, request_data):
            if model_name in self.deployments:
                return self.deployments[model_name]
            else:
                raise ValueError(f"No deployment found for model: {model_name}")
    
    class SimplePythonDeployment:
        def __init__(self, model_name, litellm_params, model_info):
            self.model_name = model_name
            self.litellm_params = litellm_params
            self.model_info = model_info
    
    # Create router and deployment
    router = SimplePythonRouter()
    
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
    
    deployment = SimplePythonDeployment("test-model", litellm_params, model_info)
    router.add_deployment(deployment)
    
    # Test routing
    test_request = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello, world! This is a test message for concurrent routing."}]
    }
    
    # Warm up
    print("Warming up...")
    for i in range(1000):
        result = router.route_request("test-model", test_request)
    
    # Concurrent benchmarking
    concurrent_requests = 10000
    thread_count = 50  # High concurrency to stress test GIL
    
    print(f"Benchmarking {concurrent_requests} concurrent routing operations with {thread_count} threads...")
    
    def worker_python(router_instance, request_data, iterations):
        """Worker function for Python routing."""
        results = []
        for i in range(iterations):
            try:
                result = router_instance.route_request("test-model", request_data)
                results.append(result)
            except Exception as e:
                results.append(None)
        return len([r for r in results if r is not None])
    
    # Test with ThreadPoolExecutor (GIL-bound)
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        # Distribute work among threads
        work_per_thread = concurrent_requests // thread_count
        futures = [
            executor.submit(worker_python, router, test_request, work_per_thread)
            for _ in range(thread_count)
        ]
        
        # Wait for all threads to complete
        results = [future.result() for future in futures]
    
    python_thread_time = time.time() - start_time
    total_successful = sum(results)
    
    print(f"✓ Python routing with {thread_count} threads: {python_thread_time:.4f}s")
    print(f"  Successful requests: {total_successful}/{concurrent_requests}")
    print(f"  Throughput: {concurrent_requests/python_thread_time:.2f} req/sec")
    print(f"  Avg latency: {python_thread_time/concurrent_requests*1000:.4f}ms per request")
    
    return python_thread_time, total_successful, concurrent_requests

def benchmark_multiprocess_rust_vs_python():
    """Benchmark Rust vs Python under true multiprocessing (bypassing GIL)."""
    print("\n=== Benchmarking Rust vs Python Under True Multiprocessing ===")
    
    # For multiprocessing, we need to be careful since Rust modules might not pickle well
    # We'll run separate processes for each
    
    test_request = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello, world! This is a test message for concurrent routing."}]
    }
    
    concurrent_requests = 1000
    process_count = 10
    
    print(f"Benchmarking {concurrent_requests} requests with {process_count} processes...")
    
    # Test Python multiprocessing (will be limited by GIL in each process)
    def python_process_worker(requests_per_process):
        """Worker function for Python multiprocessing."""
        # Simple Python router for each process
        class SimplePythonRouter:
            def __init__(self):
                self.deployments = {}
            
            def add_deployment(self, deployment):
                self.deployments[deployment.model_name] = deployment
                
            def route_request(self, model_name, request_data):
                if model_name in self.deployments:
                    return self.deployments[model_name]
                else:
                    raise ValueError(f"No deployment found for model: {model_name}")
        
        class SimplePythonDeployment:
            def __init__(self, model_name, litellm_params, model_info):
                self.model_name = model_name
                self.litellm_params = litellm_params
                self.model_info = model_info
        
        # Create router and deployment for this process
        router = SimplePythonRouter()
        
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
        
        deployment = SimplePythonDeployment("test-model", litellm_params, model_info)
        router.add_deployment(deployment)
        
        # Test routing
        test_req = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello, world! This is a test message for concurrent routing."}]
        }
        
        # Warm up
        for i in range(10):
            result = router.route_request("test-model", test_req)
        
        # Process requests
        start_time = time.time()
        for i in range(requests_per_process):
            try:
                result = router.route_request("test-model", test_req)
            except Exception as e:
                pass
        process_time = time.time() - start_time
        
        return process_time
    
    print("Testing Python multiprocessing...")
    start_time = time.time()
    with ProcessPoolExecutor(max_workers=process_count) as executor:
        requests_per_process = concurrent_requests // process_count
        futures = [
            executor.submit(python_process_worker, requests_per_process)
            for _ in range(process_count)
        ]
        
        # Wait for all processes to complete
        results = [future.result() for future in futures]
    
    python_process_time = time.time() - start_time
    print(f"✓ Python multiprocessing: {python_process_time:.4f}s")
    print(f"  Individual process times: {[f'{t:.4f}s' for t in results]}")
    
    # Test Rust multiprocessing (should show better true parallelism)
    def rust_process_worker(requests_per_process):
        """Worker function for Rust multiprocessing."""
        try:
            # Import the Rust module in this process
            import litellm_core
            
            # Create router and deployment for this process
            from litellm_core import RoutingStrategy, RouterConfig, AdvancedRouter, Deployment
            
            # Create router config
            config = RouterConfig(
                routing_strategy=RoutingStrategy.LeastBusy,
                cooldown_time_seconds=60,
                max_retries=3,
                timeout_seconds=30
            )
            
            # Create advanced router
            router = AdvancedRouter(config)
            
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
                "test-model",
                litellm_params,
                model_info
            )
            
            # Add deployment to router
            router.add_deployment(deployment)
            
            # Test routing
            test_req = {
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello, world! This is a test message for concurrent routing."}]
            }
            
            # Warm up
            for i in range(10):
                result = router.route_request("test-model", test_req)
            
            # Process requests
            start_time = time.time()
            for i in range(requests_per_process):
                try:
                    result = router.route_request("test-model", test_req)
                except Exception as e:
                    pass
            process_time = time.time() - start_time
            
            return process_time
            
        except Exception as e:
            print(f"Error in Rust process worker: {e}")
            return float('inf')
    
    print("Testing Rust multiprocessing...")
    start_time = time.time()
    with ProcessPoolExecutor(max_workers=process_count) as executor:
        requests_per_process = concurrent_requests // process_count
        futures = [
            executor.submit(rust_process_worker, requests_per_process)
            for _ in range(process_count)
        ]
        
        # Wait for all processes to complete
        results = [future.result() for future in futures]
    
    rust_process_time = time.time() - start_time
    print(f"✓ Rust multiprocessing: {rust_process_time:.4f}s")
    print(f"  Individual process times: {[f'{t:.4f}s' for t in results]}")
    
    return python_process_time, rust_process_time

def main():
    """Run all concurrent benchmarks and compare results."""
    print("LiteLLM Rust vs Python Concurrent Routing Performance Benchmark\n")
    print("This benchmark will demonstrate the GIL bottleneck in Python vs true parallelism in Rust.\n")
    
    # Benchmark concurrent Rust routing
    rust_thread_time, rust_successful, rust_total = benchmark_concurrent_rust_routing()
    
    # Benchmark concurrent Python routing
    python_thread_time, python_successful, python_total = benchmark_concurrent_python_routing()
    
    # Benchmark multiprocessing
    python_process_time, rust_process_time = benchmark_multiprocess_rust_vs_python()
    
    # Compare results
    print("\n=== Concurrent Performance Comparison ===")
    
    if rust_thread_time is not None and python_thread_time is not None:
        print(f"Thread-based concurrency ({rust_total} requests with {50} threads):")
        print(f"  Rust routing: {rust_thread_time:.4f}s ({rust_successful}/{rust_total} successful)")
        print(f"  Python routing: {python_thread_time:.4f}s ({python_successful}/{python_total} successful)")
        
        if python_thread_time > 0 and rust_thread_time > 0:
            thread_speedup = python_thread_time / rust_thread_time
            print(f"  Speedup: {thread_speedup:.2f}x faster with Rust under threading")
        
        print()
    
    if python_process_time > 0 and rust_process_time > 0:
        print(f"Process-based concurrency ({1000} requests with {10} processes):")
        print(f"  Rust multiprocessing: {rust_process_time:.4f}s")
        print(f"  Python multiprocessing: {python_process_time:.4f}s")
        
        process_speedup = python_process_time / rust_process_time
        print(f"  Speedup: {process_speedup:.2f}x faster with Rust under multiprocessing")
        print()
    
    print("🎉 Concurrent performance benchmarking completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)