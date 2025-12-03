#!/bin/bash
# Setup LiteLLM for integration testing
# This script clones LiteLLM and sets up the environment for testing

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LITELLM_DIR="${PROJECT_ROOT}/.litellm"
LITELLM_REPO="https://github.com/BerriAI/litellm.git"
LITELLM_BRANCH="${LITELLM_BRANCH:-main}"

# Detect CI environment
CI_MODE="${CI:-false}"
if [[ "$CI_MODE" == "true" ]] || [[ -n "$GITHUB_ACTIONS" ]] || [[ -n "$GITLAB_CI" ]]; then
    CI_MODE="true"
fi

echo "========================================="
echo "Fast LiteLLM - LiteLLM Integration Setup"
echo "========================================="
echo ""

# Check if uv is available
check_uv() {
    if command -v uv &> /dev/null; then
        echo "Found uv: $(uv --version)"
        return 0
    else
        return 1
    fi
}

# Install uv if not present
install_uv() {
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    if ! command -v uv &> /dev/null; then
        echo "Error: Failed to install uv. Please install it manually from https://docs.astral.sh/uv/"
        exit 1
    fi
    echo "uv installed successfully"
}

# Check if we're in a virtual environment
check_venv() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo "Virtual environment detected: $VIRTUAL_ENV"
        return 0
    else
        return 1
    fi
}

# Setup virtual environment if needed
setup_venv() {
    local venv_dir="$PROJECT_ROOT/.venv"

    if [ -d "$venv_dir" ]; then
        echo "Virtual environment already exists at: $venv_dir"
        if [[ "$CI_MODE" == "true" ]]; then
            source "$venv_dir/bin/activate" 2>/dev/null || true
            echo "Activated existing virtual environment"
            return 0
        fi
        read -p "Do you want to use it? (Y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            source "$venv_dir/bin/activate"
            echo "Activated existing virtual environment"
            return 0
        fi
    fi

    echo "Creating virtual environment at: $venv_dir"
    uv venv "$venv_dir" || {
        echo "Error: Failed to create virtual environment"
        exit 1
    }

    source "$venv_dir/bin/activate"
    echo "Created and activated virtual environment"

    # Install essential build tools
    echo "Installing build tools (maturin, pytest)..."
    uv add --dev maturin pytest pytest-asyncio
}

# Check for uv, install if needed
if ! check_uv; then
    echo "uv not found"
    if [[ "$CI_MODE" == "true" ]]; then
        install_uv
    else
        read -p "Install uv? (Y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            install_uv
        else
            echo "Please install uv manually from https://docs.astral.sh/uv/"
            exit 1
        fi
    fi
fi

# Check virtual environment
if ! check_venv; then
    echo "No virtual environment detected"
    if [[ "$CI_MODE" == "true" ]]; then
        setup_venv
    else
        echo ""
        read -p "Create virtual environment? (Y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            setup_venv
        fi
    fi
fi

# Check if LiteLLM directory exists
if [ -d "$LITELLM_DIR" ]; then
    echo "LiteLLM directory exists at: $LITELLM_DIR"
    if [[ "$CI_MODE" == "true" ]]; then
        echo "Updating LiteLLM..."
        cd "$LITELLM_DIR"
        git fetch origin
        git checkout "$LITELLM_BRANCH"
        git pull origin "$LITELLM_BRANCH" || true
    else
        read -p "Do you want to update it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Updating LiteLLM..."
            cd "$LITELLM_DIR"
            git fetch origin
            git checkout "$LITELLM_BRANCH"
            git pull origin "$LITELLM_BRANCH"
        else
            echo "Using existing LiteLLM installation"
        fi
    fi
else
    echo "Cloning LiteLLM from $LITELLM_REPO..."
    git clone --branch "$LITELLM_BRANCH" --depth 1 "$LITELLM_REPO" "$LITELLM_DIR"
fi

echo ""
echo "Installing LiteLLM dependencies..."
cd "$LITELLM_DIR"

# Try to install LiteLLM with proxy support, fall back to minimal
if uv add --editable ".[proxy]" 2>/dev/null; then
    echo "LiteLLM installed with proxy support"
elif uv add --editable . 2>/dev/null; then
    echo "LiteLLM installed (minimal)"
else
    echo "Error: Failed to install LiteLLM"
    echo ""
    echo "This might be due to missing system dependencies."
    echo "Try installing them manually:"
    echo "  cd $LITELLM_DIR"
    echo "  uv add --editable ."
    exit 1
fi

echo ""
echo "LiteLLM setup complete!"
echo ""
echo "LiteLLM Location: $LITELLM_DIR"
echo "Branch: $(cd "$LITELLM_DIR" && git branch --show-current)"
echo "Commit: $(cd "$LITELLM_DIR" && git rev-parse --short HEAD)"

if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "Virtual Environment: $VIRTUAL_ENV"
fi

echo ""
echo "Next steps:"
echo "  1. Build Fast LiteLLM: uv run maturin develop"
echo "  2. Run integration tests: ./scripts/run_litellm_tests.sh"
echo "  3. Or run specific test: ./scripts/run_litellm_tests.sh tests/test_completion.py"
echo ""
