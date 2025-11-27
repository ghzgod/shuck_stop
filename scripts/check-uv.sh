#!/bin/bash
# Preflight check script for uv

set -e

echo "Checking uv installation..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv is not installed."
    echo ""
    echo "Install uv using one of these methods:"
    echo "  Linux/macOS: curl -sSL https://install.uv.sh | bash"
    echo "  macOS (Homebrew): brew install uv"
    echo "  Windows: use WSL or the PowerShell installer"
    echo ""
    echo "See https://docs.astral.sh/uv/getting-started/installation/ for details."
    exit 1
fi

# Check uv version (require at least 0.4.0)
UV_VERSION=$(uv --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
echo "Found uv version: $UV_VERSION"

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo "ERROR: pyproject.toml not found. Are you in the project root?"
    exit 1
fi

# Run uv sync in dry-run mode to verify dependencies
echo "Verifying dependency lock file..."
uv sync --frozen --dry-run 2>/dev/null || {
    echo "WARNING: Lock file may need updating. Run 'uv sync' to update."
}

echo "✓ All preflight checks passed!"

