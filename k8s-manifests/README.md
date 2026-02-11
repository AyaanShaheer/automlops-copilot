This directory contains all Kubernetes manifests for deploying AutoMLOps Copilot.

## Directory Structure

- `namespace/` - Namespace definition
- `build/` - Docker image building (Kaniko)
- `training/` - Model training jobs
- `inference/` - Inference API deployment
- `monitoring/` - Prometheus & Grafana

## Setup Instructions

### 1. Create Namespace
```bash
kubectl apply -f namespace/namespace.yaml
```

### 2. Configure Docker Registry
Create a secret for your Docker registry:
```bash
# For DigitalOcean Container Registry
kubectl create secret docker-registry do-registry-secret \
  --docker-server=registry.digitalocean.com \
  --docker-username=$DO_API_TOKEN \
  --docker-password=$DO_API_TOKEN \
  --namespace=automlops
```

### 3. Deploy Build System
```bash
kubectl apply -f build/docker-builder-rbac.yaml
kubectl apply -f build/build-config.yaml

```

### 4. Deploy Training System
```bash
# Replace {{JOB_ID}} with actual job ID
kubectl apply -f build/kaniko-build-job-template.yaml
```

Status
✅ Build pipeline configured

🚧 Training pipeline (TODO)

🚧 Inference deployment (TODO)

🚧 Monitoring (TODO)

# Training Pipeline

This directory contains Kubernetes manifests for model training with GPU support.

## Features

- ✅ GPU support (NVIDIA)
- ✅ Paperspace Gradient integration
- ✅ DigitalOcean Spaces for model storage
- ✅ Automatic artifact upload
- ✅ Training metrics collection

## Prerequisites

1. Kubernetes cluster with GPU nodes
2. Paperspace Gradient GPU integration
3. DigitalOcean Spaces bucket
4. Docker images built and pushed to registry

## Setup

### 1. Create S3 Credentials Secret
```bash
kubectl create secret generic s3-credentials \
  --from-literal=access-key-id=$DO_SPACES_KEY \
  --from-literal=secret-access-key=$DO_SPACES_SECRET \
  --namespace=automlops
```

### 2. Apply Training Configuration
```bash
kubectl apply -f training-config.yaml
kubectl apply -f gpu-node-config.yaml
```

### 3. Test Training Job
```bash
kubectl apply -f training-job-template.yaml
```

### 4. GPU Configuration
The training pipeline supports:
NVIDIA V100 (16GB) - $2.30/hour
NVIDIA A100 (40GB) - $3.09/hour
RTX 5000 (16GB) - $0.82/hour

### 5.Monitoring
View training logs:
```bash
kubectl logs -f job/train-<JOB_ID> -n automlops
```
Check training status:
```bash
kubectl get jobs -n automlops -l app=automlops-training
```

### 6. Model Storage
Trained models are automatically uploaded to:
```bash
s3://<bucket>/jobs/<job-id>/model.pkl
```
Access via presigned URL or download directly.


