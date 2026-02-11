FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy worker requirements
COPY workers/requirements.txt .

# Copy agent requirements
COPY agent/requirements.txt agent-requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r agent-requirements.txt

# Copy agent code
COPY agent /app/agent

# Copy worker code
COPY workers /app/workers

# Set working directory
WORKDIR /app/workers

# Set Python path
ENV PYTHONPATH=/app:/app/agent

CMD ["python", "src/worker.py"]
