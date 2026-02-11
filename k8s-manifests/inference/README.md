# Inference Deployment

This directory contains Kubernetes manifests for deploying ML inference APIs with auto-scaling.

## Features

- ✅ FastAPI-based inference endpoints
- ✅ Automatic model loading from S3
- ✅ Horizontal Pod Autoscaling (HPA)
- ✅ LoadBalancer with public IP
- ✅ Health checks and readiness probes
- ✅ Resource management
- ✅ Multi-tenant support

## Architecture

```
User Request → LoadBalancer → Service → Pods (FastAPI)
                                          ↓
                                    Model (from S3)
```

## Setup

### 1. Apply Configuration
```bash
kubectl apply -f inference-config.yaml
```

### 2. Deploy Inference API
```bash
# Deployment is handled automatically by the worker
# Or manually with:
kubectl apply -f inference-deployment-template.yaml
kubectl apply -f inference-hpa-template.yaml
```

### 3. Check Deployment Status
```bash
kubectl get deployments -n automlops -l app=automlops-inference
kubectl get services -n automlops -l app=automlops-inference
kubectl get hpa -n automlops
```

### 4. Get API Endpoint
```bash
kubectl get svc inference-<JOB_ID> -n automlops
# Look for EXTERNAL-IP
```

## Usage

### Test Inference API
```bash
# Health check
curl http://<EXTERNAL-IP>/health

# Predict
curl -X POST http://<EXTERNAL-IP>/predict \
  -H "Content-Type: application/json" \
  -d '{"features": }' [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/71538723/aa5857de-9ce8-46fe-bf46-9b33d9acfac1/AutoMLOps_Copilot_Project_Blueprint.pdf)
```

## Auto-Scaling

The HPA will automatically scale pods based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)

Scaling behavior:
- Min replicas: 1
- Max replicas: 10
- Scale up: Aggressive (100% increase or +2 pods per 30s)
- Scale down: Conservative (50% decrease per 60s)

## Monitoring

View logs:
```bash
kubectl logs -f deployment/inference-<JOB_ID> -n automlops
```

Check metrics:
```bash
kubectl top pods -n automlops -l job-id=<JOB_ID>
```

## Cost Optimization

- Uses shared LoadBalancer for multiple APIs
- Auto-scales down during low traffic
- Resource limits prevent over-provisioning
- Model caching reduces S3 costs
EOF
```

***

## **✅ Phase 4 Complete!**

You've now built:
1. ✅ Complete inference deployment pipeline
2. ✅ Kubernetes Deployment + Service + HPA manifests
3. ✅ Automatic model loading from S3
4. ✅ LoadBalancer with public endpoint
5. ✅ Auto-scaling based on CPU/memory
6. ✅ Inference manager with full lifecycle management
7. ✅ Complete worker with all 5 phases

**Pipeline Summary:**
```
1. Analyze Repo (AI) → 2. Build Docker → 3. Train on GPU → 4. Upload to S3 → 5. Deploy API
```