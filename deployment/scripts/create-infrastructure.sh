#!/bin/bash
set -e

source deployment/.env

echo "============================================"
echo "Creating DigitalOcean Infrastructure"
echo "============================================"
echo ""

# Create DOKS Cluster
echo "🚀 Creating Kubernetes cluster: $CLUSTER_NAME"
echo "   Region: $CLUSTER_REGION"
echo "   Version: $CLUSTER_VERSION"
echo "   Node pool: $NODE_POOL_COUNT x $NODE_POOL_SIZE"
echo ""

doctl kubernetes cluster create $CLUSTER_NAME \
  --region $CLUSTER_REGION \
  --version $CLUSTER_VERSION \
  --size $NODE_POOL_SIZE \
  --count $NODE_POOL_COUNT \
  --auto-upgrade=true \
  --maintenance-window "saturday=02:00" \
  --wait

echo ""
echo "✅ Cluster created successfully!"
echo ""

# Get cluster credentials
echo "🔑 Configuring kubectl..."
doctl kubernetes cluster kubeconfig save $CLUSTER_NAME

echo ""
echo "✅ kubectl configured!"
echo ""

# Create Container Registry
echo "🐳 Creating Container Registry: $REGISTRY_NAME"
doctl registry create $REGISTRY_NAME --subscription-tier basic

echo ""
echo "✅ Container Registry created!"
echo ""

# Create Spaces bucket
echo "☁️ Creating Spaces bucket: $SPACES_NAME"
doctl compute space create $SPACES_NAME --region $SPACES_REGION

echo ""
echo "✅ Spaces bucket created!"
echo ""

# Create Managed PostgreSQL Database
echo "🗄️ Creating Managed PostgreSQL Database..."
doctl databases create automlops-db \
  --engine pg \
  --region $CLUSTER_REGION \
  --size db-s-1vcpu-1gb \
  --version 15

echo ""
echo "✅ PostgreSQL Database created!"
echo ""

# Create Managed Redis
echo "📦 Creating Managed Redis..."
doctl databases create automlops-redis \
  --engine redis \
  --region $CLUSTER_REGION \
  --size db-s-1vcpu-1gb \
  --version 7

echo ""
echo "✅ Redis created!"
echo ""

# Get Spaces access keys
echo "🔑 Generating Spaces access keys..."
SPACES_KEY=$(doctl compute space access-key create --output json | jq -r '.[0].access_key_id')
SPACES_SECRET=$(doctl compute space access-key create --output json | jq -r '.[0].secret_access_key')

# Save credentials
cat >> deployment/.env << ENVFILE

# Generated Credentials
SPACES_ACCESS_KEY=$SPACES_KEY
SPACES_SECRET_KEY=$SPACES_SECRET
REGISTRY_URL=registry.digitalocean.com/$REGISTRY_NAME
ENVFILE

echo ""
echo "✅ Credentials saved!"
echo ""

echo "============================================"
echo "Infrastructure Setup Complete!"
echo "============================================"
echo ""
echo "📋 Summary:"
echo "  ✅ Kubernetes Cluster: $CLUSTER_NAME"
echo "  ✅ Container Registry: registry.digitalocean.com/$REGISTRY_NAME"
echo "  ✅ Spaces Bucket: $SPACES_NAME"
echo "  ✅ PostgreSQL Database: automlops-db"
echo "  ✅ Redis: automlops-redis"
echo ""
echo "Next: Run ./deployment/scripts/deploy-services.sh"
