#!/bin/bash
set -e

source deployment/.env

echo "============================================"
echo "Building and Pushing Docker Images"
echo "============================================"
echo ""

# Login to DigitalOcean Container Registry
echo "🔐 Logging in to registry..."
doctl registry login

# Build Orchestrator
echo ""
echo "🔨 Building orchestrator..."
cd orchestrator
docker build -t $REGISTRY_URL/orchestrator:latest .
docker push $REGISTRY_URL/orchestrator:latest
cd ..

echo "✅ Orchestrator pushed!"

# Build Worker
echo ""
echo "🔨 Building worker..."

cat > workers/Dockerfile << DOCKERFILE
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
COPY ../agent/requirements.txt agent-requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r agent-requirements.txt

# Copy agent code
COPY ../agent /app/agent

# Copy worker code
COPY src /app/src

# Set Python path
ENV PYTHONPATH=/app:/app/agent

CMD ["python", "src/worker.py"]
DOCKERFILE

cd workers
docker build -t $REGISTRY_URL/worker:latest -f Dockerfile ..
docker push $REGISTRY_URL/worker:latest
cd ..

echo "✅ Worker pushed!"

# Build Frontend
echo ""
echo "🔨 Building frontend..."

cat > frontend/Dockerfile << DOCKERFILE
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
DOCKERFILE

# Update next.config.js for standalone build
cat > frontend/next.config.js << 'NEXTCONFIG'
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
}

module.exports = nextConfig
NEXTCONFIG

cd frontend
docker build -t $REGISTRY_URL/frontend:latest .
docker push $REGISTRY_URL/frontend:latest
cd ..

echo "✅ Frontend pushed!"

echo ""
echo "============================================"
echo "✅ All images built and pushed!"
echo "============================================"
