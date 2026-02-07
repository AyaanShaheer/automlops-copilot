# AutoMLOps Copilot - TODO List

## 🎯 Next Session Priorities

### Phase 1: UI Enhancements (2-3 hours)
- [ ] Add "View Generated Code" modal
  - [ ] Show Dockerfile with syntax highlighting
  - [ ] Show training_wrapper.py
  - [ ] Show app.py (FastAPI)
  - [ ] Show analysis.json
- [ ] Add "Download Artifacts" button (ZIP download)
- [ ] Add job details page with tabs
- [ ] Add syntax highlighting (react-syntax-highlighter)
- [ ] Add copy button for each code block

### Phase 2: Docker Build Pipeline (3-4 hours)
- [ ] Create Kubernetes Job manifest for Docker build
- [ ] Add Kaniko or Docker-in-Docker support
- [ ] Push images to DigitalOcean Container Registry
- [ ] Update worker to trigger K8s job
- [ ] Add build logs streaming

### Phase 3: Training Pipeline (3-4 hours)
- [ ] Create Kubernetes Job for training
- [ ] Add Gradient GPU configuration
- [ ] Mount training scripts and data
- [ ] Upload trained models to DO Spaces
- [ ] Add training progress tracking

### Phase 4: Inference Deployment (2-3 hours)
- [ ] Create Kubernetes Deployment for inference
- [ ] Create LoadBalancer Service
- [ ] Health checks and readiness probes
- [ ] Auto-scaling (HPA)
- [ ] Update job with real API endpoint

### Phase 5: Production Deployment (4-5 hours)
- [ ] Create DOKS cluster on DigitalOcean
- [ ] Setup DO Container Registry
- [ ] Setup DO Spaces bucket
- [ ] Deploy PostgreSQL (managed)
- [ ] Deploy Redis (managed)
- [ ] Deploy all services to K8s
- [ ] Configure Gradient GPU integration
- [ ] Setup domain and SSL

### Phase 6: Monitoring (2-3 hours)
- [ ] Deploy Prometheus
- [ ] Deploy Grafana
- [ ] Create dashboards
- [ ] Add alerting
- [ ] Log aggregation

### Phase 7: Documentation & Demo (2-3 hours)
- [ ] Record demo video
- [ ] Create presentation
- [ ] Write blog post
- [ ] Prepare hackathon submission

## 📊 Current Stats
- Lines of Code: ~3000+
- Components: 6 (Frontend, Orchestrator, Agent, Worker, DB, Queue)
- API Endpoints: 5
- Time Invested: ~8 hours
- Time Remaining: 40+ days until deadline

## 🐛 Known Issues
- [ ] Python files count showing 0 for some repos (check analyzer)
- [ ] No error handling for invalid GitHub URLs
- [ ] No rate limiting on job creation
- [ ] No authentication/authorization
- [ ] Generated files only in /tmp (not persistent)

## 💡 Nice-to-Have Features
- [ ] Support for private GitHub repos
- [ ] Multiple LLM providers (Claude, GPT-4)
- [ ] Model performance benchmarking
- [ ] A/B testing for generated code
- [ ] Code quality scoring
- [ ] Estimated training time/cost
- [ ] Email notifications
- [ ] Slack integration
- [ ] GitHub webhook integration

## 📚 Research Needed
- [ ] Best practices for Kaniko on DOKS
- [ ] Gradient GPU API documentation
- [ ] DO Spaces pricing and limits
- [ ] K8s GPU scheduling
- [ ] Model serving best practices

## 🎓 Learning Resources
- DigitalOcean Kubernetes: https://docs.digitalocean.com/products/kubernetes/
- Gradient API: https://docs.paperspace.com/gradient/
- Kaniko: https://github.com/GoogleContainerTools/kaniko
- FastAPI: https://fastapi.tiangolo.com/
- Gin Framework: https://gin-gonic.com/

---
Last Updated: February 8, 2026
Next Session: TBD
