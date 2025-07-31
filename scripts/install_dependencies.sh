#!/bin/bash

# Dependency installation script for Python 3.13 compatibility
# This script handles the installation of dependencies with proper workarounds

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
print_info "Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip and setuptools first
print_info "Upgrading pip and setuptools..."
pip install --upgrade pip setuptools wheel

# Install numpy first (required for many other packages)
print_info "Installing numpy first..."
pip install "numpy>=1.26.0"

# Install core dependencies one by one to handle compatibility
print_info "Installing core dependencies..."

# Install Google Cloud libraries first
pip install google-cloud-pubsub==2.18.4
pip install google-cloud-bigquery==3.13.0
pip install google-cloud-functions==1.16.0
pip install google-cloud-logging==3.8.0
pip install google-cloud-storage==2.10.0

# Install Pydantic
pip install "pydantic>=2.5.0"

# Install Claude API
pip install anthropic==0.7.8

# Install data processing libraries
pip install "pandas>=2.2.0"
pip install "pyarrow>=15.0.0"

# Install configuration and utilities
pip install python-dotenv==1.0.0
pip install pyyaml==6.0.1
pip install requests==2.31.0
pip install click==8.1.7
pip install jsonschema==4.20.0

# Install logging
pip install structlog==23.2.0

# Install testing dependencies
pip install pytest==7.4.3
pip install pytest-asyncio==0.21.1
pip install pytest-mock==3.12.0

# Install development tools
pip install black==23.11.0
pip install flake8==6.1.0
pip install mypy==1.7.1

# Install Apache Beam with compatibility flags
print_info "Installing Apache Beam (this may take a while)..."
pip install "apache-beam[gcp]>=2.54.0" --no-deps

# Install remaining Apache Beam dependencies
pip install "apache-beam[gcp]>=2.54.0"

print_success "All dependencies installed successfully!"

# Verify installation
print_info "Verifying installation..."
python3 -c "
import apache_beam as beam
import google.cloud.pubsub_v1
import google.cloud.bigquery
import pydantic
import anthropic
import pandas
import numpy
print('✅ All core dependencies imported successfully')
"

print_success "Dependency installation completed!" 