#!/usr/bin/env python3
"""
Performance diagnostic to identify why Rust is slower than Python.
"""

import sys
import os
import time
import cProfile
import pstats
from concurrent.futures import ThreadPoolExecutor

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def profile_python_implementation():
    """Profile the pure Python implementation to understand its performance characteristics."""
    print("=== Profiling Pure Python Implementation ===")
    
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
    router = SimplePythonRouter()
    
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
    
    router.add_deployment(deployment_data)
    
    # Test request
    test_request = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello, world!"}]
    }
    
    # Warm up
    print("Warming up...")
    for i in range(1000):
        result = router.route_request("gpt-3.5-turbo", test_request)
    
    # Profile single operation
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Test routing
    iterations = 100000
    for i in range(iterations):
        result = router.route_request("gpt-3.5-turbo", test_request)
    
    profiler.disable()
    
    # Print stats
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
    
    print(f"✓ Profiled {iterations} Python routing operations")
    
    return True

def profile_rust_implementation():
    """Profile the Rust implementation to understand its performance characteristics."""
    print("\n=== Profiling Rust Implementation ===")
    
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
            "gpt-3.5-turbo",
            litellm_params,
            model_info
        )
        
        # Add deployment to router
        router.add_deployment(deployment)
        
        # Test request
        test_request = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello, world!"}]
        }
        
        # Warm up
        print("Warming up...")
        for i in range(1000):
            result = router.route_request("gpt-3.5-turbo", test_request)
        
        # Profile single operation (timed approach since we can't easily profile Rust from Python)
        iterations = 100000
        print(f"Timing {iterations} Rust routing operations...")
        
        start_time = time.time()
        for i in range(iterations):
            result = router.route_request("gpt-3.5-turbo", test_request)
        rust_time = time.time() - start_time
        
        print(f"✓ Timed {iterations} Rust routing operations: {rust_time:.4f}s")
        print(f"  Avg time per call: {rust_time/iterations*1000:.4f}ms")
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_core: {e}")
        return False
    except Exception as e:
        print(f"✗ Error profiling Rust implementation: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_bridge_overhead():
    """Analyze the PyO3 bridge overhead specifically."""
    print("\n=== Analyzing PyO3 Bridge Overhead ===")
    
    try:
        # Import the Rust module
        import litellm_core
        
        print("✓ Successfully imported litellm_core")
        
        # Create a simple function to measure bridge overhead
        def measure_bridge_overhead():
            # Measure the cost of just calling a simple Rust function
            start_time = time.time()
            for i in range(100000):
                result = litellm_core.health_check()
            bridge_time = time.time() - start_time
            
            print(f"✓ Bridge overhead for 100,000 health_check calls: {bridge_time:.4f}s")
            print(f"  Avg bridge overhead per call: {bridge_time/100000*1000:.4f}ms")
            
            return bridge_time
        
        bridge_overhead = measure_bridge_overhead()
        
        # Compare with pure Python function call overhead
        def simple_python_function():
            return True
        
        start_time = time.time()
        for i in range(100000):
            result = simple_python_function()
        python_overhead = time.time() - start_time
        
        print(f"✓ Python function call overhead for 100,000 calls: {python_overhead:.4f}s")
        print(f"  Avg Python overhead per call: {python_overhead/100000*1000:.4f}ms")
        
        if python_overhead > 0:
            overhead_ratio = bridge_overhead / python_overhead
            print(f"✓ PyO3 bridge overhead is {overhead_ratio:.2f}x that of Python function calls")
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_core: {e}")
        return False
    except Exception as e:
        print(f"✗ Error analyzing bridge overhead: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all diagnostics to understand the performance gap."""
    print("LiteLLM Rust vs Python Performance Diagnostic\n")
    
    # Profile Python implementation
    profile_python_implementation()
    
    # Profile Rust implementation
    profile_rust_implementation()
    
    # Analyze bridge overhead
    analyze_bridge_overhead()
    
    print("\n=== Performance Diagnostic Summary ===")
    print("🔍 Analysis complete. The diagnostics should reveal:")
    print("  1. Where the performance bottleneck lies")
    print("  2. If it's in the PyO3 bridge or the Rust implementation")
    print("  3. How to optimize for better performance")
    
    return True

if __name__ == "__main__":
    print("Running LiteLLM Performance Diagnostic\n")
    
    success = main()
    
    if success:
        print("\n🎉 Performance diagnostic completed!")
        sys.exit(0)
    else:
        print("\n💥 Performance diagnostic failed!")
        sys.exit(1)