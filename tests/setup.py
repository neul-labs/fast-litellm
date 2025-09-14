import os
from setuptools import setup
from setuptools_rust import RustExtension, Binding

# Read the README for the long description
with open("README_pypi.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define the Rust extensions
rust_extensions = [
    RustExtension(
        "litellm_rust.litellm_core",
        path="litellm-core/Cargo.toml",
        binding=Binding.PyO3,
    ),
    RustExtension(
        "litellm_rust.litellm_token",
        path="litellm-token/Cargo.toml",
        binding=Binding.PyO3,
    ),
    RustExtension(
        "litellm_rust.litellm_connection_pool",
        path="litellm-connection-pool/Cargo.toml",
        binding=Binding.PyO3,
    ),
    RustExtension(
        "litellm_rust.litellm_rate_limiter",
        path="litellm-rate-limiter/Cargo.toml",
        binding=Binding.PyO3,
    ),
]

setup(
    name="litellm-rust",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="High-performance Rust acceleration for LiteLLM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/litellm-rust",
    packages=["litellm_rust"],
    rust_extensions=rust_extensions,
    zip_safe=False,  # Required for Rust extensions
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Rust",
    ],
    python_requires=">=3.8",
    install_requires=[
        "litellm>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-benchmark>=3.4",
        ],
    },
)