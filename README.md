# 🤖 AutoMLOps Copilot

**DigitalOcean AI Hackathon 2026 Project**

Transform any GitHub ML repository into production-ready containerized APIs automatically using AI-powered code generation.

---

## 🌟 Live Demo

**🌐 Production URL:** http://129.212.144.219

**Try it now:** Paste any ML GitHub repo and watch AI generate production artifacts in real-time!

---

## 🎯 Project Vision

AutoMLOps Copilot revolutionizes MLOps by automatically analyzing machine learning repositories and generating complete production infrastructure:

✨ **Paste GitHub URL** → **AI Analysis** → **Production-Ready API**

No manual configuration. No boilerplate. Just intelligent automation.

---

## 🏗️ System Architecture

<img width="2816" height="1536" alt="Gemini_Generated_Image_9wwzk69wwzk69wwz" src="https://github.com/user-attachments/assets/f44e24d3-3e2d-4546-800c-ff2dcc8c3f98" />

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                                │
│                    React + Vite (Port 80)                               │
│              http://129.212.144.219                                     │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      NGINX REVERSE PROXY                                │
│                      (LoadBalancer)                                     │
│    Routes:  /      → Frontend                                           │
│            /api/*  → Orchestrator                                       │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                ┌────────────┴───────────┐
                ▼                        ▼
    ┌───────────────────────┐   ┌──────────────────────┐
    │     ORCHESTRATOR      │   │      FRONTEND        │
    │    Go + Gin (x2)      │   │   React + Vite (x2)  │
    │    Port 8080          │   │                      │
    │  - Job Management     │   │  - Job Creation      │
    │  - Status Updates     │   │  - Real-time Updates │
    │  - API Endpoints      │   │  - Artifact Download │
    └──────┬───────┬────────┘   └──────────────────────┘
           │       │
           │       └──────────┐
           ▼                  ▼
    ┌─────────────┐    ┌──────────────┐
    │ PostgreSQL  │    │   Redis      │
    │  (Jobs DB)  │    │ (Job Queue)  │
    └─────────────┘    └──────┬───────┘
                              │
                              │ LPOP jobs
                              ▼
                    ┌────────────────────┐
                    │   WORKER (x2)      │
                    │   Python + AI      │
                    │                    │
                    │  1. Clone Repo     │
                    │  2. Analyze Code   │
                    │  3. AI Generation  │
                    │  4. Upload to S3   │
                    └─────────┬──────────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
                    ▼                    ▼
            ┌───────────────┐   ┌──────────────────┐
            │  Groq/Gemini  │   │  DO Spaces (S3)  │
            │   LLM APIs    │   │ automlops-models │
            │               │   │                  │
            │ - Code Gen    │   │ Generated Files: │
            │ - Analysis    │   │ - Dockerfile     │
            │               │   │ - app.py         │
            └───────────────┘   │ - training.py    │
                                │ - requirements   │
                                └──────────────────┘

                    All deployed on:
            DigitalOcean Kubernetes (DOKS)
                    nyc3 region
```

---

## 📦 Tech Stack

### **Frontend Layer**
- **Framework:** React 18 + Vite 5
- **Styling:** Tailwind CSS
- **State:** React Hooks
- **Deployment:** Nginx container (2 replicas)

### **Backend Layer**
- **API Orchestrator:** Go 1.21 + Gin Framework (2 replicas)
- **Worker Service:** Python 3.10 + Loguru (2 replicas)
- **Queue:** Redis 7.0
- **Database:** PostgreSQL 15 + GORM

### **AI/ML Layer**
- **LLM Provider:** Groq (llama-3.3-70b-versatile)
- **Fallback:** Google Gemini 1.5 Pro
- **Frameworks Detected:** TensorFlow, PyTorch, Scikit-learn, Keras, XGBoost

### **Infrastructure**
- **Container Registry:** DigitalOcean Container Registry
- **Orchestration:** Kubernetes (DOKS - 3 nodes)
- **Storage:** DigitalOcean Spaces (S3-compatible)
- **Load Balancer:** DigitalOcean LoadBalancer + Nginx
- **Region:** NYC3

### **DevOps**
- **Containerization:** Docker + Multi-stage builds
- **CI/CD:** GitHub Actions (TODO)
- **Monitoring:** Prometheus + Grafana (TODO)

---

## 🚀 Current Status

### ✅ **PRODUCTION READY - Phase 1 Complete**

| Component | Status | Details |
|-----------|--------|---------|
| 🎨 Frontend UI | ✅ **Live** | React SPA with real-time updates |
| 🔌 API Orchestrator | ✅ **Live** | 2 replicas, REST API |
| 🤖 AI Worker | ✅ **Live** | 2 replicas, LLM-powered |
| 📊 PostgreSQL | ✅ **Live** | Persistent job storage |
| 🔄 Redis Queue | ✅ **Live** | Async job processing |
| 🌐 LoadBalancer | ✅ **Live** | Public IP: 129.212.144.219 |
| 🪣 DO Spaces | ✅ **Live** | S3-compatible storage |
| 🐳 Container Registry | ✅ **Live** | 3 images published |
| ☸️ Kubernetes | ✅ **Live** | DOKS cluster (3 nodes) |
| 📥 Artifact Download | ✅ **Working** | Direct from Spaces |
| 🧠 Code Generation | ✅ **Working** | Dockerfile, FastAPI, Training |

### 🚧 **Phase 2 - Coming Soon**

| Feature | Status | Priority |
|---------|--------|----------|
| 🔄 CI/CD Pipelines | 📋 Planned | High |
| 🏋️ GPU Training | 📋 Planned | Medium |
| 🚀 Auto-Deploy APIs | 📋 Planned | High |
| 📈 Monitoring | 📋 Planned | Medium |
| 🧪 Testing Suite | 📋 Planned | Low |

---

## 📂 Project Structure

```
automlops-copilot/
├── frontend/                    # React + Vite UI
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── lib/                # API client
│   │   └── App.tsx             # Main app
│   ├── Dockerfile              # Production build
│   └── package.json
│
├── orchestrator/               # Go API Service
│   ├── cmd/server/            # Main entry point
│   ├── internal/
│   │   ├── handlers/          # HTTP handlers (Job CRUD)
│   │   ├── models/            # Data models (Job, Status)
│   │   ├── database/          # PostgreSQL + migrations
│   │   └── queue/             # Redis queue client
│   ├── Dockerfile             # Multi-stage build
│   └── go.mod
│
├── worker/                     # Python AI Agent
│   ├── agent/
│   │   └── src/
│   │       ├── analyzer/      # Repo analysis
│   │       │   └── repo_analyzer.py
│   │       ├── llm/           # LLM clients
│   │       │   ├── groq_client.py
│   │       │   └── gemini_client.py
│   │       └── generators/    # Code generators
│   │           ├── dockerfile_generator.py
│   │           ├── training_generator.py
│   │           └── fastapi_generator.py
│   ├── src/
│   │   ├── storage/           # S3/Spaces integration
│   │   └── worker.py          # Main worker loop
│   ├── Dockerfile
│   └── requirements.txt
│
├── k8s-manifests/             # Kubernetes Deployments
│   ├── namespace.yaml
│   ├── secrets.yaml
│   ├── postgres.yaml
│   ├── redis.yaml
│   ├── orchestrator.yaml
│   ├── worker.yaml
│   ├── frontend.yaml
│   └── nginx-proxy.yaml
│
└── README.md
```

---

## 🛠️ Local Development Setup

### **Prerequisites**
- Docker Desktop
- kubectl
- doctl (DigitalOcean CLI)
- Python 3.10+
- Go 1.21+
- Node.js 18+

### **1. Clone Repository**
```bash
git clone https://github.com/AyaanShaheer/automlops-copilot.git
cd automlops-copilot
```

### **2. Setup Environment Variables**

**Worker (.env):**
```bash
cd worker
cat > .env << EOF
GROQ_API_KEY=your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here
LLM_PROVIDER=groq
REDIS_HOST=localhost
REDIS_PORT=6379
ORCHESTRATOR_URL=http://localhost:8080
ENABLE_S3_UPLOAD=false
TEMP_REPO_DIR=/tmp/repos
EOF
```

**Orchestrator (.env):**
```bash
cd orchestrator
cat > .env << EOF
SERVER_PORT=8080
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=automlops
REDIS_HOST=localhost
REDIS_PORT=6379
EOF
```

### **3. Start Local Services**
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Start Orchestrator
cd orchestrator
go run cmd/server/main.go

# Start Worker (in new terminal)
cd worker
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Start Frontend (in new terminal)
cd frontend
npm install
npm run dev
```

### **4. Access Locally**
- Frontend: http://localhost:5173
- API: http://localhost:8080
- Health: http://localhost:8080/health

---

## ☸️ Production Deployment (DigitalOcean)

### **Prerequisites**
1. DigitalOcean account
2. DOKS cluster created
3. Container registry set up
4. Spaces bucket created

### **Step 1: Build and Push Images**
```bash
# Login to DO Registry
doctl registry login

# Build images
docker build -t registry.digitalocean.com/automlops/frontend:latest ./frontend
docker build -t registry.digitalocean.com/automlops/orchestrator:latest ./orchestrator
docker build -t registry.digitalocean.com/automlops/worker:latest ./worker

# Push to registry
docker push registry.digitalocean.com/automlops/frontend:latest
docker push registry.digitalocean.com/automlops/orchestrator:latest
docker push registry.digitalocean.com/automlops/worker:latest
```

### **Step 2: Configure Kubernetes**
```bash
# Get cluster credentials
doctl kubernetes cluster kubeconfig save your-cluster-name

# Create namespace
kubectl create namespace automlops

# Create secrets
kubectl create secret docker-registry do-registry-secret \
  --docker-server=registry.digitalocean.com \
  --docker-username=your-do-token \
  --docker-password=your-do-token \
  -n automlops

kubectl create secret generic llm-credentials \
  --from-literal=groq-api-key='your-groq-key' \
  --from-literal=gemini-api-key='your-gemini-key' \
  -n automlops

kubectl create secret generic spaces-credentials \
  --from-literal=access-key='your-spaces-key' \
  --from-literal=secret-key='your-spaces-secret' \
  -n automlops
```

### **Step 3: Deploy Services**
```bash
# Deploy all services
kubectl apply -f k8s-manifests/

# Check status
kubectl get pods -n automlops
kubectl get svc -n automlops

# Get LoadBalancer IP
kubectl get svc nginx-proxy -n automlops
```

---

## 🎮 Usage Guide

### **1. Create a Job**
1. Visit http://129.212.144.219
2. Paste GitHub ML repo URL (e.g., `https://github.com/username/ml-project`)
3. Click "Create Job"

### **2. Monitor Progress**
Watch real-time status updates:
- ⏳ **Queued** - Job in queue
- 🔍 **Analyzing** - Cloning and analyzing repo
- 🏗️ **Building** - Generating artifacts
- ☁️ **Uploading** - Uploading to Spaces
- ✅ **Completed** - Ready to download

### **3. Download Artifacts**
Click on the completed job to view and download:
- `Dockerfile` - Production-ready containerization
- `app.py` - FastAPI inference service
- `training_wrapper.py` - Model training script
- `requirements.txt` - Python dependencies
- `analysis.json` - Repository metadata

---

## 📊 Example Repositories to Test

| Repository | Framework | Description |
|------------|-----------|-------------|
| [Machine Downtime Predictor](https://github.com/AyaanShaheer/Machine_Downtime_Predictor_API) | Scikit-learn | Production example |
| [Personalized Wellness AI](https://github.com/AyaanShaheer/Personalized-Wellness-AI-) | Mixed | Complex notebook |
| Your own ML repos! | Any | Test your projects |

---

## 🔑 API Reference

### **Base URL**
```
Production: http://129.212.144.219/api
Local: http://localhost:8080/api
```

### **Endpoints**

**Create Job**
```bash
POST /api/jobs
Content-Type: application/json

{
  "repo_url": "https://github.com/username/ml-repo"
}

Response: 201 Created
{
  "job": {
    "id": "uuid",
    "repo_url": "...",
    "status": "queued",
    "created_at": "2026-02-11T..."
  }
}
```

**List Jobs**
```bash
GET /api/jobs

Response: 200 OK
[
  {
    "id": "uuid",
    "repo_url": "...",
    "status": "completed",
    "frameworks": "sklearn",
    "python_files": 1,
    "notebooks": 0
  }
]
```

**Get Job Details**
```bash
GET /api/jobs/:id

Response: 200 OK
{
  "id": "uuid",
  "status": "completed",
  "dockerfile_url": "https://...",
  "artifacts": [...]
}
```

**Health Check**
```bash
GET /health

Response: 200 OK
{
  "service": "automlops-orchestrator",
  "status": "healthy"
}
```

---

## 🐛 Troubleshooting

### **Jobs Stuck in Queue**
```bash
# Check worker pods
kubectl get pods -n automlops -l app=worker

# View worker logs
kubectl logs -n automlops -l app=worker --tail=100
```

### **Database Connection Issues**
```bash
# Check PostgreSQL
kubectl exec -n automlops deployment/orchestrator -- env | grep DB_

# Test connection
kubectl exec -it deployment/postgres-deployment -n automlops -- psql -U postgres
```

### **Artifact Download Fails**
```bash
# Verify Spaces bucket
aws s3 ls s3://automlops-models/jobs/ --endpoint-url=https://nyc3.digitaloceanspaces.com

# Check bucket permissions (should be public-read)
```

### **LLM API Errors**
```bash
# Check API keys
kubectl get secret llm-credentials -n automlops -o yaml

# View worker logs for API errors
kubectl logs -n automlops -l app=worker --tail=50
```

---

## 🎯 Roadmap

### **Phase 1: Core Platform** 
- [✅] Job creation and management
- [✅] Repository analysis using AI
- [✅] Artifact generation (Dockerfile, FastAPI, Training)
- [✅] S3/Spaces integration
- [✅] Kubernetes deployment
- [✅] Public LoadBalancer
- [✅] Real-time status updates

### **Phase 2: CI/CD & Automation** 🚧 IN PROGRESS
- [ ] Generate GitHub Actions workflows
- [ ] Generate GitLab CI configs
- [ ] Generate Jenkinsfiles
- [ ] Platform CI/CD pipeline
- [ ] Automated testing

### **Phase 3: Advanced Features** 📋 PLANNED
- [ ] Gradient GPU training integration
- [ ] Auto-deploy generated APIs to Kubernetes
- [ ] Model versioning and tracking
- [ ] A/B testing support
- [ ] Cost estimation

### **Phase 4: Production Hardening** 🔮 FUTURE
- [ ] Prometheus + Grafana monitoring
- [ ] Distributed tracing (Jaeger)
- [ ] Rate limiting and quotas
- [ ] Multi-tenancy support
- [ ] Custom LLM fine-tuning

---

## 👥 Team

| Name | Role | Responsibilities |
|------|------|------------------|
| **Ayaan Shaheer** | Lead DevOps & AI Systems Engineer | Kubernetes, Docker, Go orchestrator, infrastructure |
| **Saif** | Frontend Engineer | React UI, user experience, real-time updates |
| **Zain** | AI/ML Engineer | Python worker, LLM integration, code generation |
| **Afzaal** | Project Coordinator | Project Management, Documentation, Presentation |

---

## 🏆 Why This Project Stands Out
1. **🎯 Real Production Use Case** - Solves actual MLOps pain points
2. **🤖 AI-Powered** - Not just templates, intelligent code generation
3. **☁️ Full Cloud Stack** - DOKS, Spaces, Container Registry, LoadBalancer
4. **📈 Scalable Architecture** - Kubernetes with horizontal scaling
5. **🚀 Live Demo** - Fully functional public deployment
6. **💡 Innovation** - Unique approach to MLOps automation
7. **🏗️ Enterprise-Grade** - Production-ready infrastructure patterns

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

For major changes, please open an issue first to discuss.

---

## 📧 Contact & Support

- **Issues:** [GitHub Issues](https://github.com/AyaanShaheer/automlops-copilot/issues)
- **Email:** [EMAIL_ADDRESS](gfever252@gmail.com)
- **Demo:** [Live Demo](http://129.212.144.219)

---

## 🙏 Acknowledgments

- **DigitalOcean** - For the Gradient AI Hackathon and cloud infrastructure
- **Groq** - For lightning-fast LLM inference
- **Google** - For Gemini AI capabilities
- **Open Source Community** - For amazing tools and frameworks

---

**Built with ❤️ for the DigitalOcean AI Hackathon 2026**

**⭐ Star this repo if you find it useful!**



