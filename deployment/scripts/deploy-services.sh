#!/bin/bash
set -e

source deployment/.env

echo "============================================"
echo "Deploying AutoMLOps Services"
echo "============================================"
echo ""

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f k8s-manifests/namespace/namespace.yaml

echo ""
echo "✅ Namespace created!"
echo ""

# Create secrets
echo "🔐 Creating secrets..."

# Docker registry secret
kubectl create secret docker-registry do-registry-secret \
  --docker-server=registry.digitalocean.com \
  --docker-username=$DO_API_TOKEN \
  --docker-password=$DO_API_TOKEN \
  --namespace=automlops \
  --dry-run=client -o yaml | kubectl apply -f -

# S3/Spaces credentials
kubectl create secret generic s3-credentials \
  --from-literal=access-key-id=$SPACES_ACCESS_KEY \
  --from-literal=secret-access-key=$SPACES_SECRET_KEY \
  --namespace=automlops \
  --dry-run=client -o yaml | kubectl apply -f -

# Database connection string (get from doctl)
DB_HOST=$(doctl databases get automlops-db --output json | jq -r '.[0].connection.host')
DB_PORT=$(doctl databases get automlops-db --output json | jq -r '.[0].connection.port')
DB_USER=$(doctl databases get automlops-db --output json | jq -r '.[0].connection.user')
DB_PASSWORD=$(doctl databases get automlops-db --output json | jq -r '.[0].connection.password')
DB_NAME="automlops"

kubectl create secret generic postgres-credentials \
  --from-literal=host=$DB_HOST \
  --from-literal=port=$DB_PORT \
  --from-literal=user=$DB_USER \
  --from-literal=password=$DB_PASSWORD \
  --from-literal=database=$DB_NAME \
  --namespace=automlops \
  --dry-run=client -o yaml | kubectl apply -f -

# Redis connection
REDIS_HOST=$(doctl databases get automlops-redis --output json | jq -r '.[0].connection.host')
REDIS_PORT=$(doctl databases get automlops-redis --output json | jq -r '.[0].connection.port')
REDIS_PASSWORD=$(doctl databases get automlops-redis --output json | jq -r '.[0].connection.password')

kubectl create secret generic redis-credentials \
  --from-literal=host=$REDIS_HOST \
  --from-literal=port=$REDIS_PORT \
  --from-literal=password=$REDIS_PASSWORD \
  --namespace=automlops \
  --dry-run=client -o yaml | kubectl apply -f -

# Groq API Key
read -sp "Enter your Groq API Key: " GROQ_API_KEY
echo ""

kubectl create secret generic llm-credentials \
  --from-literal=groq-api-key=$GROQ_API_KEY \
  --namespace=automlops \
  --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "✅ Secrets created!"
echo ""

# Deploy build infrastructure
echo "🔨 Deploying build infrastructure..."
kubectl apply -f k8s-manifests/build/docker-builder-rbac.yaml
kubectl apply -f k8s-manifests/build/build-config.yaml

echo ""
echo "✅ Build infrastructure deployed!"
echo ""

# Deploy training infrastructure
echo "🎓 Deploying training infrastructure..."
kubectl apply -f k8s-manifests/training/training-config.yaml
kubectl apply -f k8s-manifests/training/gpu-node-config.yaml

echo ""
echo "✅ Training infrastructure deployed!"
echo ""

# Deploy inference infrastructure
echo "⚡ Deploying inference infrastructure..."
kubectl apply -f k8s-manifests/inference/inference-config.yaml

echo ""
echo "✅ Inference infrastructure deployed!"
echo ""

# Deploy orchestrator
echo "🎯 Deploying orchestrator..."
cat > /tmp/orchestrator-deployment.yaml << YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator
  namespace: automlops
spec:
  replicas: 2
  selector:
    matchLabels:
      app: orchestrator
  template:
    metadata:
      labels:
        app: orchestrator
    spec:
      containers:
        - name: orchestrator
          image: $REGISTRY_URL/orchestrator:latest
          ports:
            - containerPort: 8080
          env:
            - name: SERVER_PORT
              value: "8080"
            - name: DB_HOST
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: host
            - name: DB_PORT
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: port
            - name: DB_USER
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: user
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: password
            - name: DB_NAME
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: database
            - name: REDIS_HOST
              valueFrom:
                secretKeyRef:
                  name: redis-credentials
                  key: host
            - name: REDIS_PORT
              valueFrom:
                secretKeyRef:
                  name: redis-credentials
                  key: port
            - name: REDIS_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: redis-credentials
                  key: password
            - name: DO_SPACES_KEY
              valueFrom:
                secretKeyRef:
                  name: s3-credentials
                  key: access-key-id
            - name: DO_SPACES_SECRET
              valueFrom:
                secretKeyRef:
                  name: s3-credentials
                  key: secret-access-key
            - name: DO_SPACES_REGION
              value: "nyc3"
            - name: DO_SPACES_BUCKET
              value: "automlops-models"
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: orchestrator
  namespace: automlops
spec:
  type: ClusterIP
  selector:
    app: orchestrator
  ports:
    - port: 8080
      targetPort: 8080
YAML

kubectl apply -f /tmp/orchestrator-deployment.yaml

echo ""
echo "✅ Orchestrator deployed!"
echo ""

# Deploy worker
echo "🤖 Deploying worker..."
cat > /tmp/worker-deployment.yaml << YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker
  namespace: automlops
spec:
  replicas: 3
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      serviceAccountName: docker-builder
      containers:
        - name: worker
          image: $REGISTRY_URL/worker:latest
          env:
            - name: REDIS_HOST
              valueFrom:
                secretKeyRef:
                  name: redis-credentials
                  key: host
            - name: REDIS_PORT
              valueFrom:
                secretKeyRef:
                  name: redis-credentials
                  key: port
            - name: REDIS_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: redis-credentials
                  key: password
            - name: ORCHESTRATOR_URL
              value: "http://orchestrator.automlops.svc.cluster.local:8080"
            - name: ENABLE_K8S_BUILD
              value: "true"
            - name: ENABLE_TRAINING
              value: "true"
            - name: ENABLE_DEPLOYMENT
              value: "true"
            - name: ENABLE_S3_UPLOAD
              value: "true"
            - name: REGISTRY_URL
              value: "$REGISTRY_URL"
            - name: S3_BUCKET
              value: "$SPACES_NAME"
            - name: S3_ENDPOINT
              value: "$SPACES_REGION.digitaloceanspaces.com"
            - name: DO_SPACES_KEY
              valueFrom:
                secretKeyRef:
                  name: s3-credentials
                  key: access-key-id
            - name: DO_SPACES_SECRET
              valueFrom:
                secretKeyRef:
                  name: s3-credentials
                  key: secret-access-key
            - name: GROQ_API_KEY
              valueFrom:
                secretKeyRef:
                  name: llm-credentials
                  key: groq-api-key
            - name: LLM_PROVIDER
              value: "groq"
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
            limits:
              cpu: "2000m"
              memory: "4Gi"
YAML

kubectl apply -f /tmp/worker-deployment.yaml

echo ""
echo "✅ Worker deployed!"
echo ""

# Deploy frontend
echo "🎨 Deploying frontend..."
cat > /tmp/frontend-deployment.yaml << YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: automlops
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: frontend
          image: $REGISTRY_URL/frontend:latest
          ports:
            - containerPort: 3000
          env:
            - name: NEXT_PUBLIC_API_URL
              value: "http://orchestrator.automlops.svc.cluster.local:8080"
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "250m"
              memory: "256Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: automlops
spec:
  type: LoadBalancer
  selector:
    app: frontend
  ports:
    - port: 80
      targetPort: 3000
YAML

kubectl apply -f /tmp/frontend-deployment.yaml

echo ""
echo "✅ Frontend deployed!"
echo ""

echo "============================================"
echo "Deployment Complete!"
echo "============================================"
echo ""
echo "📋 Services Status:"
kubectl get deployments -n automlops
echo ""
kubectl get services -n automlops
echo ""

echo "⏳ Waiting for LoadBalancer IP..."
sleep 10

FRONTEND_IP=$(kubectl get svc frontend -n automlops -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo ""
echo "============================================"
echo "🎉 AutoMLOps Copilot is Live!"
echo "============================================"
echo ""
echo "🌐 Frontend: http://$FRONTEND_IP"
echo "🎯 API: http://orchestrator.automlops.svc.cluster.local:8080"
echo ""
echo "Next steps:"
echo "  1. Visit http://$FRONTEND_IP"
echo "  2. Create your first job!"
echo "  3. Monitor: kubectl get pods -n automlops -w"
