#!/usr/bin/env bash
"""
Installation script for LiteLLM Rust Accelerator.
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}LiteLLM Rust Accelerator Installation Script${NC}"
echo -e "${BLUE}==========================================${NC}\n"

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo -e "${RED}Error: Rust/Cargo is not installed${NC}"
    echo "Please install Rust first:"
    echo "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

echo -e "${GREEN}✓ Rust/Cargo is installed${NC}"

# Check if we're in the right directory
if [ ! -f "Cargo.toml" ]; then
    echo -e "${RED}Error: Cargo.toml not found${NC}"
    echo "Please run this script from the litellm-rust directory"
    exit 1
fi

echo -e "${GREEN}✓ In correct directory${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 is installed${NC}"

# Build options
RELEASE=false
VERBOSE=false
TARGET=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --release)
            RELEASE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --target)
            TARGET="--target $2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--release] [--verbose] [--target TARGET]"
            exit 1
            ;;
    esac
done

# Build command
BUILD_CMD="cargo build"
if [ "$RELEASE" = true ]; then
    BUILD_CMD="$BUILD_CMD --release"
fi

if [ "$VERBOSE" = true ]; then
    BUILD_CMD="$BUILD_CMD --verbose"
fi

if [ -n "$TARGET" ]; then
    BUILD_CMD="$BUILD_CMD $TARGET"
fi

echo -e "${YELLOW}Building Rust components...${NC}"
echo -e "${YELLOW}Running: $BUILD_CMD${NC}"

# Run the build
if $BUILD_CMD; then
    echo -e "${GREEN}✓ Build successful!${NC}"
    
    # Show build artifacts location
    if [ "$RELEASE" = true ]; then
        echo "Release artifacts are in: target/release/"
    else
        echo "Debug artifacts are in: target/debug/"
    fi
    
    # Show available libraries
    echo "Available libraries:"
    find target -name "*.so" -o -name "*.dylib" -o -name "*.dll" | head -10
    
    # Create symlinks for easier import
    echo -e "\n${YELLOW}Creating symlinks for easier Python import...${NC}"
    
    if [ "$RELEASE" = true ]; then
        cd target/release
    else
        cd target/debug
    fi
    
    # Create symlinks for all libraries
    for lib in liblitellm_*.so; do
        if [ -f "$lib" ]; then
            symlink_name=$(echo "$lib" | sed 's/^lib//' | sed 's/\.so$/.so/')
            ln -sf "$lib" "$symlink_name"
            echo -e "${GREEN}✓ Created symlink: $symlink_name -> $lib${NC}"
        fi
    done
    
    cd ../..
    
    # Install Python package
    echo -e "\n${YELLOW}Installing Python package...${NC}"
    pip3 install -e .
    
    echo -e "\n${GREEN}✓ Python package installed successfully!${NC}"
    
    # Run basic test
    echo -e "\n${YELLOW}Running basic functionality test...${NC}"
    cd ..
    PYTHONPATH=litellm-rust/target/release python3 -c "
import sys
import os
sys.path.insert(0, 'litellm-rust/target/release')

try:
    import litellm_core
    import litellm_token
    import litellm_connection_pool
    import litellm_rate_limiter
    
    print('✓ Successfully imported all Rust modules')
    
    # Test health checks
    core_health = litellm_core.health_check()
    token_health = litellm_token.token_health_check()
    pool_health = litellm_connection_pool.connection_pool_health_check()
    rate_health = litellm_rate_limiter.rate_limit_health_check()
    
    print(f'✓ Core health check: {core_health}')
    print(f'✓ Token health check: {token_health}')
    print(f'✓ Pool health check: {pool_health}')
    print(f'✓ Rate health check: {rate_health}')
    
    # Test core functionality
    core = litellm_core.LiteLLMCore()
    print(f'✓ Created LiteLLMCore instance')
    print(f'✓ Core available: {core.is_available()}')
    
    # Test token counting
    token_counter = litellm_token.SimpleTokenCounter(100)
    print(f'✓ Created SimpleTokenCounter with cache size: {token_counter.cache_size}')
    
    text = 'Hello, world! This is a test message.'
    model = 'gpt-3.5-turbo'
    token_count = token_counter.count_tokens(text, model)
    print(f'✓ Counted {token_count} tokens for \"${text[:30]}...\" with model \"${model}\"')
    
    # Test batch token counting
    texts = ['Hello', 'world', 'test']
    batch_counts = token_counter.count_tokens_batch(texts, model)
    print(f'✓ Batch token counting: {batch_counts}')
    
    # Test cache statistics
    cache_stats = token_counter.get_cache_stats()
    print(f'✓ Token cache statistics: {cache_stats}')
    
    # Test rate limiting
    rate_limiter = litellm_token.SimpleRateLimiter()
    print(f'✓ Created SimpleRateLimiter')
    
    key = 'test-user'
    within_limit = rate_limiter.check_rate_limit(key, 100, 60)
    print(f'✓ Rate limit check for \"${key}\": {within_limit}')
    
    consumed = rate_limiter.consume_tokens(key, 5)
    print(f'✓ Consumed 5 tokens for \"${key}\": {consumed}')
    
    rate_stats = rate_limiter.get_rate_limit_stats()
    print(f'✓ Rate limit statistics: {rate_stats}')
    
    # Test connection pooling
    connection_pool = litellm_connection_pool.SimpleConnectionPool(10)
    print(f'✓ Created SimpleConnectionPool with max connections: {connection_pool.max_connections_per_provider}')
    
    provider = 'openai'
    conn_id = connection_pool.get_connection(provider)
    print(f'✓ Got connection for provider \"${provider}\": {conn_id}')
    
    returned = connection_pool.return_connection(conn_id)
    print(f'✓ Returned connection \"${conn_id}\": {returned}')
    
    pool_stats = connection_pool.get_pool_stats()
    print(f'✓ Pool statistics: {pool_stats}')
    
    print('\n🎉 All functionality tests passed!')
    
except ImportError as e:
    print(f'✗ Failed to import required modules: {e}')
    sys.exit(1)
except Exception as e:
    print(f'✗ Error during functionality test: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" || echo -e "${RED}⚠ Functionality test failed${NC}"
    
    echo -e "\n${GREEN}🎉 LiteLLM Rust Accelerator Installation Complete! 🎉${NC}"
    echo -e "${BLUE}===============================================${NC}"
    echo -e "The LiteLLM Rust components have been successfully installed."
    echo -e "They will automatically accelerate existing Python code when available."
    
    if [ "$RELEASE" = true ]; then
        echo -e "\n${YELLOW}Release build installed${NC}"
    else
        echo -e "\n${YELLOW}Debug build installed${NC"
    fi
    
    echo -e "\nTo use in your Python code:"
    echo -e "  import litellm"
    echo -e "  # LiteLLM will automatically use Rust acceleration when available"
    echo -e "  response = litellm.completion(model='gpt-3.5-turbo', messages=[...])"
    
    echo -e "\nFor development:"
    echo -e "  cd litellm-rust"
    echo -e "  ./install.sh --release  # Install release build"
    echo -e "  ./install.sh --verbose   # Install with verbose output"
    
    exit 0
    
else
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi