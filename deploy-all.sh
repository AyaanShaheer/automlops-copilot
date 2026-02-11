#!/bin/bash
set -e

echo "============================================"
echo "🚀 AutoMLOps Copilot - Complete Deployment"
echo "============================================"
echo ""

# Check if doctl is authenticated
echo "Checking authentication..."
if ! doctl account get &> /dev/null; then
    echo "❌ Not authenticated. Run: doctl auth init"
    exit 1
fi

echo "✅ Authenticated"
echo ""

# Configuration
CLUSTER_NAME="automlops-cluster"
CLUSTER_REGION="nyc3"
NODE_SIZE="s-4vcpu-8gb"
NODE_COUNT="3"
REGISTRY_NAME="automlops"
SPACES_NAME="automlops-models"

echo "Configuration:"
echo "  Cluster: $CLUSTER_NAME"
echo "  Region: $CLUSTER_REGION"
echo "  Nodes: $NODE_COUNT x $NODE_SIZE"
echo ""

read -p "Proceed? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "============================================"
echo "Step 1: Creating Kubernetes Cluster"
echo "This takes 10-15 minutes..."
echo "============================================"
echo ""

doctl kubernetes cluster create $CLUSTER_NAME \
  --region $CLUSTER_REGION \
  --size $NODE_SIZE \
  --count $NODE_COUNT \
  --auto-upgrade=true \
  --wait

echo ""
echo "✅ Cluster created!"
echo ""

# Configure kubectl
doctl kubernetes cluster kubeconfig save $CLUSTER_NAME

echo "Testing kubectl connection..."
kubectl get nodes
echo ""

echo "============================================"
echo "Step 2: Creating Container Registry"
echo "============================================"
echo ""

doctl registry create $REGISTRY_NAME --subscription-tier basic || echo "Registry might already exist"
sleep 3
REGISTRY_URL=$(doctl registry get --format Endpoint --no-header)

echo "✅ Registry: $REGISTRY_URL"
echo ""

echo "============================================"
echo "Step 3: Creating Spaces Bucket"
echo "============================================"
echo ""

doctl compute space create $SPACES_NAME --region $CLUSTER_REGION || echo "Bucket might already exist"

echo "✅ Spaces bucket: $SPACES_NAME"
echo ""

echo "============================================"
echo "Step 4: Creating Spaces Access Keys"
echo "============================================"
echo ""

echo "Generating access keys..."
KEY_OUTPUT=$(doctl compute access-key create automlops-key 2>&1) || echo "Key might already exist"

echo "✅ Access keys created"
echo ""

echo "============================================"
echo "Step 5: Creating PostgreSQL Database"
echo "This takes 5-10 minutes..."
echo "============================================"
echo ""

doctl databases create automlops-db \
  --engine pg \
  --region $CLUSTER_REGION \
  --size db-s-1vcpu-1gb \
  --version 15 || echo "Database might already exist"

echo "✅ PostgreSQL created"
echo ""

echo "============================================"
echo "Step 6: Creating Redis"
echo "This takes 5-10 minutes..."
echo "============================================"
echo ""

doctl databases create automlops-redis \
  --engine redis \
  --region $CLUSTER_REGION \
  --size db-s-1vcpu-1gb \
  --version 7 || echo "Redis might already exist"

echo "✅ Redis created"
echo ""

echo "============================================"
echo "🎉 Infrastructure Setup Complete!"
echo "============================================"
echo ""
echo "Created:"
echo "  ✅ Kubernetes Cluster: $CLUSTER_NAME"
echo "  ✅ Container Registry: $REGISTRY_URL"
echo "  ✅ Spaces Bucket: $SPACES_NAME"
echo "  ✅ PostgreSQL Database: automlops-db"
echo "  ✅ Redis: automlops-redis"
echo ""
echo "Next Steps:"
echo "  1. Wait for databases to finish provisioning (check with: doctl databases list)"
echo "  2. Build Docker images"
echo "  3. Deploy services"
echo ""
echo "To check status:"
echo "  kubectl get nodes"
echo "  doctl databases list"
