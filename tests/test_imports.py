"""
Test suite for LiteLLM Rust acceleration.
"""
import pytest

def test_import():
    """Test that the package can be imported."""
    try:
        import litellm_rust
        assert litellm_rust.__version__ == "0.1.0"
    except ImportError:
        pytest.fail("Failed to import litellm_rust")

def test_rust_extensions_import():
    """Test that Rust extensions can be imported."""
    try:
        from litellm_rust import rust_extensions
        assert rust_extensions.RUST_ACCELERATION_AVAILABLE is not None
    except ImportError:
        pytest.fail("Failed to import rust_extensions")

def test_accelerator_import():
    """Test that the accelerator module can be imported."""
    try:
        from litellm_rust import accelerator
        assert accelerator is not None
    except ImportError:
        pytest.fail("Failed to import accelerator")

def test_diagnostics_import():
    """Test that the diagnostics module can be imported."""
    try:
        from litellm_rust import diagnostics
        assert diagnostics is not None
    except ImportError:
        pytest.fail("Failed to import diagnostics")

if __name__ == "__main__":
    test_import()
    test_rust_extensions_import()
    test_accelerator_import()
    test_diagnostics_import()
    print("All tests passed!")