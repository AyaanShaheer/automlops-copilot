# Production Deployment to DigitalOcean

Complete guide to deploy AutoMLOps Copilot to production on DigitalOcean.

## Prerequisites

1. **DigitalOcean Account** with billing enabled
2. **doctl CLI** installed ([Installation Guide](https://docs.digitalocean.com/reference/doctl/how-to/install/))
3. **kubectl** installed
4. **Docker** installed
5. **DigitalOcean API Token** ([Create Token](https://cloud.digitalocean.com/account/api/tokens))

## Cost Estimate

| Resource | Specification | Monthly Cost |
|----------|--------------|--------------|
| DOKS Cluster | 3x s-4vcpu-8gb | ~$144 |
| Container Registry | Basic tier | $5 |
| Spaces | 250GB storage | $5 |
| PostgreSQL | db-s-1vcpu-1gb | $15 |
| Redis | db-s-1vcpu-1gb | $15 |
| LoadBalancer | 1 instance | $12 |
| **Total** | | **~$196/month** |

## Deployment Steps

### Step 1: Initial Setup
```bash
cd ~/automlops-copilot
./deployment/scripts/setup-digitalocean.sh
```

This will:
- Authenticate with DigitalOcean
- Save your API token securely
- Create configuration file

### Step 2: Create Infrastructure
```bash
./deployment/scripts/create-infrastructure.sh
```

This creates:
- ✅ DOKS Kubernetes cluster (3 nodes)
- ✅ Container Registry
- ✅ Spaces bucket for models
- ✅ Managed PostgreSQL database
- ✅ Managed Redis

**Time:** ~10-15 minutes

### Step 3: Build and Push Images
```bash
./deployment/docker/build-and-push.sh
```

This builds and pushes:
- ✅ Orchestrator (Go API)
- ✅ Worker (Python)
- ✅ Frontend (Next.js)

**Time:** ~5-10 minutes

### Step 4: Deploy Services
```bash
./deployment/scripts/deploy-services.sh
```

This deploys:
- ✅ All Kubernetes manifests
- ✅ Secrets and ConfigMaps
- ✅ Orchestrator service
- ✅ Worker pods
- ✅ Frontend with LoadBalancer

**Time:** ~5 minutes

### Step 5: Access Your Application
```bash
# Get frontend URL
kubectl get svc frontend -n automlops

# Visit http://<EXTERNAL-IP>
```

## Post-Deployment

### Monitor Services
```bash
# Watch pods
kubectl get pods -n automlops -w

# View logs
kubectl logs -f deployment/orchestrator -n automlops
kubectl logs -f deployment/worker -n automlops
kubectl logs -f deployment/frontend -n automlops
```

### Scale Workers
```bash
# Scale to 5 workers
kubectl scale deployment worker -n automlops --replicas=5
```

### Check Resource Usage
```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods -n automlops
```

## Production Optimizations

### 1. Add Custom Domain
```bash
# Update DNS A record
# Point domain to LoadBalancer IP

# Update ingress
kubectl apply -f k8s-manifests/inference/inference-ingress.yaml
```

### 2. Enable HTTPS with cert-manager
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f k8s-manifests/monitoring/cert-manager-issuer.yaml
```

### 3. Setup Monitoring (optional)
```bash
# Deploy Prometheus + Grafana
kubectl apply -f k8s-manifests/monitoring/
```

### 4. Enable Gradient GPU
```bash
# Add Gradient node pool
doctl kubernetes cluster node-pool create $CLUSTER_NAME \
  --name gpu-pool \
  --size gpu-h100x1-80gb \
  --count 1 \
  --tag gradient-gpu
```

## Troubleshooting

### Pods not starting
```bash
kubectl describe pod <pod-name> -n automlops
kubectl logs <pod-name> -n automlops
```

### LoadBalancer stuck in pending
```bash
kubectl get svc -n automlops
# Wait 2-3 minutes for DigitalOcean to provision
```

### Database connection issues
```bash
# Check secrets
kubectl get secret postgres-credentials -n automlops -o yaml

# Test connection
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql -h <DB_HOST> -U <DB_USER> -d automlops
```

## Cleanup

**⚠️ Warning: This deletes ALL resources**

```bash
./deployment/scripts/cleanup.sh
```

## Support

For issues, check:
1. Kubernetes events: `kubectl get events -n automlops --sort-by='.lastTimestamp'`
2. Service logs: `kubectl logs -f deployment/<service> -n automlops`
3. DigitalOcean status: https://status.digitalocean.com/

## Next Steps

- [ ] Setup custom domain
- [ ] Enable HTTPS
- [ ] Configure backups
- [ ] Setup monitoring/alerting
- [ ] Enable GPU training
- [ ] Configure CI/CD pipeline
EOF
```

***

## **Step 7: Create Complete Setup Guide**

```bash
cd ~/automlops-copilot

cat > DEPLOYMENT.md << 'EOF'
# 🚀 Complete Deployment Guide

## Quick Start (15 minutes)

```bash
# 1. Setup DigitalOcean
./deployment/scripts/setup-digitalocean.sh

# 2. Create infrastructure (10 min wait)
./deployment/scripts/create-infrastructure.sh

# 3. Build and push Docker images
./deployment/docker/build-and-push.sh

# 4. Deploy all services
./deployment/scripts/deploy-services.sh

# 5. Get your URL
kubectl get svc frontend -n automlops
```

## What You Get

✅ **Complete ML Pipeline**
- Analyze any GitHub ML repo
- Generate production code using AI
- Build Docker images automatically
- Train models on GPU (Gradient)
- Deploy inference APIs
- Auto-scaling and load balancing

✅ **Production Infrastructure**
- Kubernetes cluster (DOKS)
- Managed PostgreSQL database
- Managed Redis cache
- Container registry
- S3-compatible storage (Spaces)
- LoadBalancer with public IP

✅ **Enterprise Features**
- Horizontal auto-scaling
- Health checks and readiness probes
- Resource management
- Secrets management
- Multi-tenant support

## Architecture Diagram

```
Internet
   ↓
LoadBalancer (DigitalOcean)
   ↓
Frontend (Next.js)
   ↓
Orchestrator (Go API)
   ↓
Redis Queue
   ↓
Workers (Python) → Kubernetes Jobs
   ↓               ↓              ↓
AI Analysis    Docker Build   GPU Training → Spaces (S3)
                                 ↓
                           Inference API
                                 ↓
                           LoadBalancer
                                 ↓
                            Public URL
```

## Cost Breakdown

**Minimum Setup:** ~$196/month
- Perfect for hackathons and small projects
- Can handle 100+ jobs/day

**Recommended Production:** ~$400/month
- Larger node pool (5 nodes)
- GPU node pool for training
- Higher database tier

**Scale Up Options:**
- Add GPU nodes: +$1000/month per H100
- Increase database: +$50-$200/month
- More storage: +$0.02/GB/month

## Support & Next Steps

📚 See `deployment/README.md` for detailed docs
🐛 Troubleshooting guide included
🔧 Customization options available

**Need help?** Open an issue on GitHub!
EOF
```

***

## **✅ Phase 5 Complete!**

We now have:
1. ✅ Complete production deployment scripts
2. ✅ Infrastructure setup (DOKS, Registry, Spaces, Databases)
3. ✅ Automated Docker builds
4. ✅ One-command deployment
5. ✅ Comprehensive documentation
6. ✅ Monitoring and troubleshooting guides
7. ✅ Cleanup scripts

***

## **🎉 PROJECT COMPLETE! 🎉**

