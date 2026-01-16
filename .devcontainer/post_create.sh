#!/bin/bash

# Development container setup script for constitutional-qa-agent project
set -e

echo "🚀 Setting up constitutional-qa-agent development environment..."

# Ensure uv is in PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Install project dependencies
echo "📦 Installing Python dependencies..."
cd /workspaces/constitutional-qa-agent

# Check if uv is available, if not install it
if ! command -v uv &> /dev/null; then
    echo "🐍 Installing uv (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Sync dependencies
uv sync

# Install pre-commit hooks (if .pre-commit-config.yaml exists)
if [ -f ".pre-commit-config.yaml" ]; then
    echo "🪝 Installing pre-commit hooks..."
    uv run pre-commit install
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p runs
mkdir -p .vscode

# Set proper permissions
echo "🔒 Setting permissions..."
chmod +x /workspaces/constitutional-qa-agent/.devcontainer/post_create.sh

# Create a sample .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔐 Creating .env file from template..."
    cp .env.template .env
fi

# Install npm dependencies for the UI
echo "📦 Installing npm dependencies..."
npm install

echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Configure your .env file with actual credentials"
echo "2. Run 'uv run python -m eval.main --help' to see available commands"
echo "3. Run tests with 'uv run pytest'"
echo "4. Start coding! 🚀"
echo ""
echo "📝 Available commands:"
echo "  - uv sync                    # Install/update dependencies"
echo "  - uv run pytest            # Run tests"
echo "  - uv run ruff check        # Lint code"
echo "  - uv run ruff format       # Format code"
echo "  - uv run pyright           # Type checking"
echo "  - uv run python -m eval.main  # Run evaluation"