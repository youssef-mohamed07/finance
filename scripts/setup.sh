#!/bin/bash

# Setup script for Finance Analyzer development environment

set -e

echo "🔧 Setting up Finance Analyzer development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
if [ -f requirements-dev.txt ]; then
    echo "🛠️ Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️ Please update .env file with your actual API keys and configuration"
fi

# Install system dependencies (Ubuntu/Debian)
if command -v apt-get &> /dev/null; then
    echo "🔧 Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y ffmpeg libmagic1
fi

# Install system dependencies (macOS)
if command -v brew &> /dev/null; then
    echo "🔧 Installing system dependencies..."
    brew install ffmpeg libmagic
fi

# Generate secret key
echo "🔐 Generating secret key..."
secret_key=$(python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s/your_super_secret_key_here_generate_with_openssl_rand_hex_32/$secret_key/" .env

echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your AssemblyAI API key"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the application: python main.py"
echo "4. Visit http://localhost:8000"