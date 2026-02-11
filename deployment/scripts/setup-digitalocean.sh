#!/bin/bash
set -e

echo "============================================"
echo "AutoMLOps Copilot - DigitalOcean Setup"
echo "============================================"

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "❌ doctl is not installed. Please install it first:"
    echo "   https://docs.digitalocean.com/reference/doctl/how-to/install/"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install it first:"
    echo "   https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

echo ""
echo "📋 Prerequisites Check:"
echo "  ✅ doctl installed"
echo "  ✅ kubectl installed"
echo ""

# Prompt for DigitalOcean API token
read -sp "Enter your DigitalOcean API Token: " DO_API_TOKEN
echo ""

# Authenticate with DigitalOcean
echo "🔐 Authenticating with DigitalOcean..."
doctl auth init --access-token "$DO_API_TOKEN"

echo ""
echo "✅ Authentication successful!"
echo ""

# Save configuration
cat > deployment/.env << ENVFILE
DO_API_TOKEN=$DO_API_TOKEN
CLUSTER_NAME=automlops-cluster
CLUSTER_REGION=nyc3
CLUSTER_VERSION=1.28.2-do.0
NODE_POOL_SIZE=s-4vcpu-8gb
NODE_POOL_COUNT=3
REGISTRY_NAME=automlops-registry
SPACES_NAME=automlops-models
SPACES_REGION=nyc3
DOMAIN=automlops.example.com
ENVFILE

echo "✅ Configuration saved to deployment/.env"
echo ""
echo "Next steps:"
echo "  1. Run: ./deployment/scripts/create-infrastructure.sh"
echo "  2. Run: ./deployment/scripts/deploy-services.sh"
