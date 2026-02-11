#!/bin/bash
set -e

source deployment/.env

echo "============================================"
echo "⚠️  WARNING: This will delete all resources!"
echo "============================================"
echo ""
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "🗑️ Deleting Kubernetes cluster..."
doctl kubernetes cluster delete $CLUSTER_NAME --force

echo ""
echo "🗑️ Deleting Container Registry..."
doctl registry delete $REGISTRY_NAME --force

echo ""
echo "🗑️ Deleting Spaces bucket..."
doctl compute space delete $SPACES_NAME --force

echo ""
echo "🗑️ Deleting PostgreSQL database..."
doctl databases delete automlops-db --force

echo ""
echo "🗑️ Deleting Redis..."
doctl databases delete automlops-redis --force

echo ""
echo "✅ Cleanup complete!"
