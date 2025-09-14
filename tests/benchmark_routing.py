#!/usr/bin/env python3
"""
Performance benchmark to compare Rust vs Python routing performance.
"""

import sys
import os
import time
import json

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def benchmark_rust_routing():
    """Benchmark the Rust routing implementation."""
    print("=== Benchmarking Rust Routing Implementation ===")
    
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
            "messages": [{"role": "user", "content": "Hello, world!"}]
        }
        
        # Warm up
        print("Warming up...")
        for i in range(1000):
            result = router.route_request("test-model", test_request)
        
        # Benchmark routing with Python dict
        iterations = 100000
        print(f"Benchmarking {iterations} routing operations with Python dict...")
        
        start_time = time.time()
        for i in range(iterations):
            result = router.route_request("test-model", test_request)
        rust_dict_time = time.time() - start_time
        rust_dict_avg = rust_dict_time / iterations
        
        print(f"✓ Rust routing with Python dict: {rust_dict_time:.4f}s (avg: {rust_dict_avg*1000:.4f}ms per call)")
        
        # Benchmark routing with JSON string
        json_request = json.dumps(test_request)
        print(f"Benchmarking {iterations} routing operations with JSON string...")
        
        start_time = time.time()
        for i in range(iterations):
            result = router.route_request("test-model", json_request)
        rust_json_time = time.time() - start_time
        rust_json_avg = rust_json_time / iterations
        
        print(f"✓ Rust routing with JSON string: {rust_json_time:.4f}s (avg: {rust_json_avg*1000:.4f}ms per call)")
        
        # Get router statistics
        stats = router.get_stats()
        print(f"✓ Router statistics: {stats}")
        
        return rust_dict_time, rust_json_time, iterations
        
    except Exception as e:
        print(f"✗ Error benchmarking Rust routing: {e}")
        import traceback
        traceback.print_exc()
        return None, None, 0

def benchmark_python_routing_equivalent():
    """Benchmark a Python equivalent routing implementation."""
    print("\n=== Benchmarking Python Equivalent Routing ===")
    
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
        "messages": [{"role": "user", "content": "Hello, world!"}]
    }
    
    # Warm up
    print("Warming up...")
    for i in range(1000):
        result = router.route_request("test-model", test_request)
    
    # Benchmark
    iterations = 100000
    print(f"Benchmarking {iterations} routing operations...")
    
    start_time = time.time()
    for i in range(iterations):
        result = router.route_request("test-model", test_request)
    python_time = time.time() - start_time
    python_avg = python_time / iterations
    
    print(f"✓ Python equivalent routing: {python_time:.4f}s (avg: {python_avg*1000:.4f}ms per call)")
    
    return python_time, iterations

def main():
    """Run all benchmarks and compare results."""
    print("LiteLLM Rust vs Python Routing Performance Benchmark\n")
    
    # Benchmark Rust routing
    rust_dict_time, rust_json_time, rust_iterations = benchmark_rust_routing()
    
    # Benchmark Python equivalent
    python_time, python_iterations = benchmark_python_routing_equivalent()
    
    # Compare results
    if rust_dict_time is not None and python_time is not None:
        print("\n=== Performance Comparison ===")
        print(f"Test iterations: {rust_iterations}")
        print(f"Rust routing (dict): {rust_dict_time:.4f}s (avg: {rust_dict_time/rust_iterations*1000:.4f}ms per call)")
        print(f"Rust routing (JSON): {rust_json_time:.4f}s (avg: {rust_json_time/rust_iterations*1000:.4f}ms per call)")
        print(f"Python equivalent: {python_time:.4f}s (avg: {python_time/python_iterations*1000:.4f}ms per call)")
        
        if python_time > 0:
            dict_speedup = python_time / rust_dict_time
            json_speedup = python_time / rust_json_time
            print(f"\nPerformance Improvements:")
            print(f"✓ Rust routing (dict) is {dict_speedup:.2f}x faster than Python equivalent")
            print(f"✓ Rust routing (JSON) is {json_speedup:.2f}x faster than Python equivalent")
        
        print("\n🎉 Performance benchmarking completed!")
        return True
    else:
        print("\n💥 Performance benchmarking failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)