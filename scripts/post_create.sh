#!/bin/bash
# Post-create script for GitHub Codespaces
# Runs once when the container is first created

set -e

echo "=================================="
echo "Neo4j and AWS Bedrock Workshop"
echo "Post-Create Setup"
echo "=================================="

# Install uv package manager
echo ""
echo "Installing uv package manager..."
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH for this session
export PATH="$HOME/.local/bin:$PATH"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
uv sync

# Install AWS CDK globally
echo ""
echo "Installing AWS CDK..."
npm install -g aws-cdk

# Register Jupyter kernel
echo ""
echo "Registering Jupyter kernel..."
uv run python -m ipykernel install --user --name neo4j-aws-workshop --display-name "Neo4j AWS Workshop"

echo ""
echo "=================================="
echo "Post-Create Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Configure AWS credentials (see GUIDE_DEV_CONTAINERS.md)"
echo "  2. Configure Neo4j credentials"
echo "  3. Run: source scripts/post_start.sh"
