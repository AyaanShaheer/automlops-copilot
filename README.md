# AutoMLOps Copilot

Automatically convert any GitHub ML repository into a production-ready, deployed inference API using DigitalOcean's full AI and cloud ecosystem.

## Architecture

- **Frontend**: Next.js
- **Orchestrator**: Go (Gin)
- **AI Agent**: Python + LLM
- **Training**: DigitalOcean Gradient GPU
- **Storage**: DO Spaces
- **Database**: DO Managed PostgreSQL
- **Infrastructure**: Kubernetes (DOKS)

## Project Structure

├── README.md
├── agent
│   ├── src
│   └── templates
├── docker-compose.yml
├── docker-templates
├── frontend
├── inference-template
├── k8s-manifests
│   ├── build
│   ├── inference
│   ├── monitoring
│   └── training
├── orchestrator
│   ├── cmd
│   ├── config
│   └── internal
└── workers



## Team Responsibilities

- **Member 1**: Frontend UI and logs dashboard
- **Member 2**: Go orchestrator and job system
- **Member 3**: Python AI agent and repo understanding
- **Member 4**: Kubernetes, Docker, and deployment pipelines

## Getting Started

See individual component READMEs for setup instructions.
