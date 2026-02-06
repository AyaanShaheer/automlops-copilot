# Stage 1: Build
FROM python:3.10-slim as build

# Set working directory
WORKDIR /app

# Copy requirements files
COPY environment.yml requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install conda environment
RUN pip install -U conda
RUN conda env create -f environment.yml
RUN conda run --no-capture-output -n base pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy application code
COPY --from=build /app .

# Set entry point
CMD ["python", "train.py"]

# Expose port for potential web interface (e.g., TensorBoard)
EXPOSE 6006

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONPATH /app