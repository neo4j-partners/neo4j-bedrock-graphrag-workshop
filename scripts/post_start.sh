#!/bin/bash
# Post-start script for GitHub Codespaces
# Runs every time the container starts

echo "=================================="
echo "Neo4j and AWS Bedrock Workshop"
echo "Environment Setup"
echo "=================================="

# Create .env file from Codespace secrets if they exist
ENV_FILE=".env"

# Check if .env already exists
if [ -f "$ENV_FILE" ]; then
    echo "Found existing .env file"
else
    echo "Creating .env file from Codespace secrets..."

    # Start with the sample file
    if [ -f ".env.sample" ]; then
        cp .env.sample "$ENV_FILE"
    fi
fi

# Update .env with Codespace secrets if they exist
if [ -n "$NEO4J_URI" ]; then
    echo "Setting NEO4J_URI from Codespace secret"
    sed -i "s|^NEO4J_URI=.*|NEO4J_URI=$NEO4J_URI|" "$ENV_FILE" 2>/dev/null || true
fi

if [ -n "$NEO4J_USERNAME" ]; then
    echo "Setting NEO4J_USERNAME from Codespace secret"
    sed -i "s|^NEO4J_USERNAME=.*|NEO4J_USERNAME=$NEO4J_USERNAME|" "$ENV_FILE" 2>/dev/null || true
fi

if [ -n "$NEO4J_PASSWORD" ]; then
    echo "Setting NEO4J_PASSWORD from Codespace secret"
    sed -i "s|^NEO4J_PASSWORD=.*|NEO4J_PASSWORD=$NEO4J_PASSWORD|" "$ENV_FILE" 2>/dev/null || true
fi

# Configure AWS credentials if provided
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Configuring AWS credentials from Codespace secrets"
    mkdir -p ~/.aws
    cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = $AWS_ACCESS_KEY_ID
aws_secret_access_key = $AWS_SECRET_ACCESS_KEY
EOF

    # Set default region
    AWS_REGION=${AWS_REGION:-us-east-1}
    cat > ~/.aws/config << EOF
[default]
region = $AWS_REGION
output = json
EOF
fi

echo ""
echo "=================================="
echo "Environment Configuration Status"
echo "=================================="

# Check AWS credentials
if aws sts get-caller-identity &>/dev/null; then
    echo "[OK] AWS credentials configured"
    aws sts get-caller-identity --query 'Account' --output text | xargs -I {} echo "     Account: {}"
else
    echo "[!] AWS credentials not configured"
    echo "    Run: aws configure"
fi

# Check Neo4j configuration
if grep -q "^NEO4J_URI=neo4j" "$ENV_FILE" 2>/dev/null; then
    echo "[OK] Neo4j URI configured"
else
    echo "[!] Neo4j URI not configured"
    echo "    Update NEO4J_URI in .env file"
fi

if grep -q "^NEO4J_PASSWORD=." "$ENV_FILE" 2>/dev/null && ! grep -q "^NEO4J_PASSWORD=$" "$ENV_FILE" 2>/dev/null; then
    echo "[OK] Neo4j password configured"
else
    echo "[!] Neo4j password not configured"
    echo "    Update NEO4J_PASSWORD in .env file"
fi

echo ""
echo "=================================="
echo "Quick Start Commands"
echo "=================================="
echo ""
echo "  # Verify AWS access"
echo "  aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[?contains(modelId, \`titan-embed\`)].modelId'"
echo ""
echo "  # Deploy infrastructure (optional)"
echo "  cd infra/cdk && cdk deploy --all"
echo ""
echo "  # Start Jupyter"
echo "  jupyter lab"
echo ""
