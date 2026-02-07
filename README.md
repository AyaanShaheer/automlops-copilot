# AutoMLOps Copilot 🚀

**DigitalOcean Gradient™ AI Hackathon Project**

Automatically convert any GitHub ML repository into a production-ready, deployed inference API using DigitalOcean's full AI and cloud ecosystem.

## 🎯 Project Vision

AutoMLOps Copilot allows users to paste a GitHub ML repository URL and automatically:
- Understand the repository structure using AI (Groq/Gemini)
- Generate Docker and API layers
- Train the model on Gradient™ GPU (TODO)
- Store model artifacts in DigitalOcean Spaces (TODO)
- Deploy a public inference API (TODO)
- Provide monitoring and logs (TODO)

## 🏗️ Architecture

```
User → Frontend (Next.js) → Orchestrator (Go) → Worker (Python) → AI Agent
                                ↓                    ↓
                          PostgreSQL              Redis Queue
                                                     ↓
                                              Generate Artifacts:
                                              - Dockerfile
                                              - Training Script
                                              - FastAPI Service
```

## 📦 Tech Stack

- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **API Orchestrator**: Go (Gin framework)
- **AI Agent**: Python + Groq LLM (llama-3.3-70b-versatile)
- **Async Workers**: Python + Redis
- **Database**: PostgreSQL
- **Queue**: Redis
- **Containerization**: Docker + Docker Compose
- **Deployment** (TODO): Kubernetes (DOKS), Gradient GPU, DO Spaces

## 🚀 Current Status

### ✅ Completed
- [✅] Next.js frontend with real-time job updates
- [✅] Go API orchestrator with job management
- [✅] Python AI agent that analyzes repos
- [✅] Groq LLM integration for code generation
- [✅] PostgreSQL database for job metadata
- [✅] Redis queue for async processing
- [✅] Worker that generates Dockerfile, training scripts, FastAPI services
- [✅] Docker Compose for local development

### 🚧 In Progress / TODO
- [ ] Add "View Generated Code" in UI
- [ ] Kubernetes manifests for build/training/deployment
- [ ] Docker image building pipeline
- [ ] Model training on Gradient GPU
- [ ] DigitalOcean Spaces integration
- [ ] Inference API deployment
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Production deployment to DOKS

## 📂 Project Structure

```
automlops-copilot/
├── frontend/              # Next.js UI
│   ├── app/              # Next.js 14 app directory
│   ├── lib/              # API client
│   └── package.json
│
├── orchestrator/          # Go API service
│   ├── cmd/server/       # Main entry point
│   ├── internal/         # Internal packages
│   │   ├── handlers/     # HTTP handlers
│   │   ├── models/       # Data models
│   │   ├── database/     # Database connection
│   │   ├── queue/        # Redis queue
│   │   └── config/       # Configuration
│   └── go.mod
│
├── agent/                 # Python AI repo parser
│   ├── src/
│   │   ├── analyzer/     # Repo analysis
│   │   ├── llm/          # LLM client (Groq/Gemini)
│   │   ├── generators/   # Code generators
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
│
├── workers/              # Async job processing
│   ├── src/worker.py
│   ├── requirements.txt
│   └── .env.example
│
├── k8s-manifests/        # Kubernetes YAML files (TODO)
│   ├── build/
│   ├── training/
│   └── inference/
│
├── docker-compose.yml    # Local development setup
└── README.md
```

## 🛠️ Setup Instructions

### Prerequisites
- Docker & Docker Compose
- Go 1.21+
- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 1. Clone Repository
```bash
git clone https://github.com/AyaanShaheer/automlops-copilot.git
cd automlops-copilot
```

### 2. Setup Agent (Python)
```bash
cd agent
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Add your GROQ_API_KEY and/or GEMINI_API_KEY
```

### 3. Setup Orchestrator (Go)
```bash
cd orchestrator
cp .env.example .env
go mod download
go build -o bin/orchestrator ./cmd/server
```

### 4. Setup Workers (Python)
```bash
cd workers
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy API keys from agent/.env
cp .env.example .env
# Add your API keys
```

### 5. Setup Frontend (Next.js)
```bash
cd frontend
npm install
cp .env.local.example .env.local
```

### 6. Start Services
```bash
# Terminal 1: Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Terminal 2: Start Orchestrator
cd orchestrator
./bin/orchestrator

# Terminal 3: Start Worker
cd workers
source .venv/bin/activate
python3 src/worker.py

# Terminal 4: Start Frontend
cd frontend
npm run dev
```

### 7. Access Application
- Frontend: http://localhost:3000
- API: http://localhost:8080
- Health Check: http://localhost:8080/health

## 🎮 Usage

1. Open http://localhost:3000
2. Paste any GitHub ML repository URL
3. Click "Create Job"
4. Watch as the AI agent:
   - Clones and analyzes the repo
   - Generates production-ready Dockerfile
   - Generates training wrapper script
   - Generates FastAPI inference service
5. View generated artifacts in `/tmp/automlops-output/{job_id}/`

## 📊 Example Repos to Test

- https://github.com/ageron/handson-ml2
- https://github.com/tensorflow/models
- https://github.com/keras-team/keras-examples
- Your own ML repositories!

## 🔑 Environment Variables

### Agent (.env)
```env
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
LLM_PROVIDER=groq
TEMP_REPO_DIR=/tmp/repos
```

### Orchestrator (.env)
```env
SERVER_PORT=8080
DB_HOST=localhost
DB_PORT=5432
DB_NAME=automlops
REDIS_HOST=localhost
REDIS_PORT=6379
```

## 🐛 Troubleshooting

### Worker not picking up jobs
```bash
# Check Redis connection
docker exec -it automlops-redis redis-cli ping

# Check queue
docker exec -it automlops-redis redis-cli LLEN automlops:jobs
```

### Database connection issues
```bash
# Check PostgreSQL
docker exec -it automlops-postgres psql -U postgres -d automlops -c "\dt"
```

### LLM API errors
- Verify API keys in `agent/.env` and `workers/.env`
- Check rate limits on Groq/Gemini dashboard

## 📝 Generated Artifacts

For each job, the system generates:
- `Dockerfile` - Production-ready containerization
- `training_wrapper.py` - Training orchestration script
- `app.py` - FastAPI inference service
- `requirements.txt` - Python dependencies
- `analysis.json` - Repository analysis metadata

## 🎯 Roadmap

### Phase 1: Core Foundation ✅
- [] Basic UI and API
- [] Job queue system
- [] AI code generation

### Phase 2: Execution Pipeline 🚧
- [ ] Docker image building
- [ ] Model training
- [ ] Inference deployment

### Phase 3: Production 🔜
- [ ] Kubernetes deployment
- [ ] GPU training on Gradient
- [ ] DigitalOcean integration
- [ ] Monitoring & logging

## 👥 Team & Responsibilities

- **Member 1**: Frontend UI and dashboard (Saif)
- **Member 2**: Go orchestrator and job system, Kubernetes, Docker, and deployment pipelines (Ayaan)
- **Member 3 & 4**: Python AI agent and repo understanding (Zain and Afzaal)

## 🏆 Why This Project Wins

1. Demonstrates full ML lifecycle automation
2. Uses complete DigitalOcean ecosystem
3. Production-ready system design
4. Real GPU usage (when implemented)
5. Impressive infrastructure and automation

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

This is a hackathon project. After the hackathon, we welcome contributions!

## 📧 Contact

For questions or issues, please open a GitHub issue.

---

