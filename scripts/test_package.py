#!/usr/bin/env python3
"""
Test script for fast-litellm package build and installation
"""

import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, cwd=cwd, check=check, capture_output=True, text=True
        )
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr and result.returncode != 0:
            print(f"STDERR:\n{result.stderr}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        raise


def test_package_build():
    """Test building the package"""
    print("=" * 60)
    print("TESTING PACKAGE BUILD")
    print("=" * 60)

    # Get project root
    project_root = Path(__file__).parent.parent

    # Clean any existing build artifacts
    build_dirs = [
        project_root / "build",
        project_root / "dist",
        project_root / "target",
    ]

    for build_dir in build_dirs:
        if build_dir.exists():
            print(f"Cleaning {build_dir}")
            run_command(["rm", "-rf", str(build_dir)])

    # Install maturin if not available
    try:
        run_command(["maturin", "--version"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing maturin...")
        run_command([sys.executable, "-m", "pip", "install", "maturin"])

    # Build the package
    print("Building package with maturin...")
    run_command(["maturin", "build", "--release"], cwd=project_root)

    # Check if wheel was created
    dist_dir = project_root / "dist"
    if not dist_dir.exists():
        raise RuntimeError("dist directory not created")

    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        raise RuntimeError("No wheel file found in dist/")

    print(f"✅ Successfully built wheel: {wheels[0].name}")
    return wheels[0]


def test_package_installation(wheel_path):
    """Test installing and importing the package"""
    print("=" * 60)
    print("TESTING PACKAGE INSTALLATION")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        venv_dir = Path(temp_dir) / "test_venv"

        # Create virtual environment
        print("Creating test virtual environment...")
        venv.create(venv_dir, with_pip=True)

        # Get python executable in venv
        if sys.platform == "win32":
            python_exe = venv_dir / "Scripts" / "python.exe"
            pip_exe = venv_dir / "Scripts" / "pip.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
            pip_exe = venv_dir / "bin" / "pip"

        # Upgrade pip
        run_command([str(pip_exe), "install", "--upgrade", "pip"])

        # Install dependencies first
        print("Installing dependencies...")
        run_command(
            [str(pip_exe), "install", "pydantic", "tiktoken", "aiohttp", "httpx"]
        )

        # Install our wheel
        print(f"Installing wheel: {wheel_path}")
        run_command([str(pip_exe), "install", str(wheel_path)])

        # Test importing the package
        print("Testing package import...")
        test_script = """
import sys
try:
    import fast_litellm
    print(f"✅ Successfully imported fast_litellm")
    print(f"Version: {getattr(fast_litellm, '__version__', 'unknown')}")
    print(f"Rust acceleration available: {getattr(fast_litellm, 'RUST_ACCELERATION_AVAILABLE', 'unknown')}")

    # Test basic functionality
    health = fast_litellm.health_check()
    print(f"Health check: {health}")

    status = fast_litellm.get_feature_status()
    print(f"Feature status: {status}")

    print("✅ All basic tests passed!")

except Exception as e:
    print(f"❌ Error testing package: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

        result = run_command([str(python_exe), "-c", test_script])
        if result.returncode == 0:
            print("✅ Package installation and import test passed!")
        else:
            print("❌ Package installation or import test failed!")
            return False

    return True


def main():
    """Main test function"""
    try:
        # Test building
        wheel_path = test_package_build()

        # Test installation
        success = test_package_installation(wheel_path)

        if success:
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED!")
            print("Package is ready for PyPI publishing")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ TESTS FAILED!")
            print("=" * 60)
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
